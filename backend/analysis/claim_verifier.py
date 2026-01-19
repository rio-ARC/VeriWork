"""
Claim Verification Engine
Contribution Truth

THE CORE: This is the "wow factor" - disproval-based verification.

Key insight: We don't try to PROVE claims. We try to DISPROVE them.
If we fail to disprove, the claim is likely true.
"""

import json
import re
from typing import Optional

from api.models import (
    ContributionClaim,
    Evidence,
    EvidenceCollection,
    EvidenceStrength,
    EvidenceType,
    GitLog,
    MeetingTranscript,
    VerdictType,
    VerificationVerdict,
)
from analysis.gemini_client import GeminiClient, get_gemini_client, is_gemini_configured


class ClaimVerificationEngine:
    """
    The Evidence-Backed Claim Verification Engine.
    
    This system doesn't measure activity. It verifies truth.
    
    Given a claim like "I implemented the login system", Gemini autonomously
    tries to DISPROVE it using all available evidence:
    - Are there git commits from this student touching auth files?
    - Do meeting transcripts show them discussing login?
    - Did they create the task? Or just mark it complete?
    - Is there evidence someone ELSE actually built it?
    """
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """Initialize the verification engine."""
        self.gemini = gemini_client
        self._evidence: Optional[EvidenceCollection] = None
    
    def set_evidence(self, evidence: EvidenceCollection):
        """Set the evidence collection to analyze against."""
        self._evidence = evidence
    
    async def verify_claim(
        self,
        claimant: str,
        claim: str
    ) -> VerificationVerdict:
        """
        Verify a contribution claim using the disproval method.
        
        Args:
            claimant: Name of the person making the claim
            claim: The contribution claim to verify
        
        Returns:
            VerificationVerdict with verdict, confidence, and evidence
        """
        if not self._evidence:
            return self._create_unverifiable_verdict(
                claimant, claim, "No evidence has been uploaded for analysis."
            )
        
        # Prepare evidence context for Gemini
        evidence_context = self._prepare_evidence_context()
        
        # If Gemini is not configured, use heuristic analysis
        if not is_gemini_configured() or not self.gemini:
            return self._heuristic_verification(claimant, claim, evidence_context)
        
        # === THE DISPROVAL LOOP ===
        # Wrapped in try-catch to gracefully handle API errors (rate limits, etc.)
        try:
            # Step 1: Ask Gemini what evidence MUST exist if claim is true
            expected_evidence = await self._get_expected_evidence(claim, claimant)
            
            # If we got an empty response, Gemini might be failing - try heuristic
            if not expected_evidence:
                print("Gemini returned empty response, falling back to heuristic mode")
                return self._heuristic_verification(claimant, claim, evidence_context)
            
            # Step 2: Search for supporting evidence
            supporting = await self._find_supporting_evidence(
                claimant, claim, evidence_context, expected_evidence
            )
            
            # Step 3: Search for COUNTER-evidence (the key insight!)
            counter = await self._find_counter_evidence(
                claimant, claim, evidence_context
            )
            
            # Step 4: Identify missing expected evidence
            missing = await self._find_missing_evidence(
                claimant, claim, evidence_context, expected_evidence
            )
            
            # Step 5: Synthesize verdict
            verdict = await self._synthesize_verdict(
                claimant, claim, supporting, counter, missing, evidence_context
            )
            
            return verdict
            
        except Exception as e:
            error_msg = str(e)
            print(f"Gemini API error, falling back to heuristic: {error_msg}")
            
            # Check if it's a rate limit error
            if "429" in error_msg or "quota" in error_msg.lower() or "rate" in error_msg.lower():
                # Fall back to heuristic with a note about rate limiting
                result = self._heuristic_verification(claimant, claim, evidence_context)
                result.explanation = result.explanation.replace(
                    "(Heuristic mode",
                    "(Heuristic mode - Gemini API rate limited, please wait 30 seconds and retry for AI analysis"
                )
                return result
            else:
                # Other error - still use heuristic but note the error
                result = self._heuristic_verification(claimant, claim, evidence_context)
                return result
    
    def _prepare_evidence_context(self) -> str:
        """Prepare all evidence as context string for Gemini."""
        parts = []
        
        if self._evidence.git_log and self._evidence.git_log.commits:
            parts.append("=== GIT COMMIT LOG ===")
            for commit in self._evidence.git_log.commits:
                files_str = ", ".join(f.filename for f in commit.files_changed) if commit.files_changed else "N/A"
                parts.append(
                    f"[{commit.short_hash}] {commit.author_name} ({commit.timestamp.strftime('%Y-%m-%d')}): "
                    f"{commit.message}\n  Files: {files_str}"
                )
        
        if self._evidence.transcripts:
            for i, transcript in enumerate(self._evidence.transcripts):
                parts.append(f"\n=== MEETING TRANSCRIPT {i+1}: {transcript.title} ===")
                for stmt in transcript.statements:
                    parts.append(f"[L{stmt.line_number}] {stmt.speaker}: {stmt.content}")
        
        return "\n".join(parts)
    
    async def _get_expected_evidence(self, claim: str, claimant: str) -> str:
        """Ask Gemini what evidence should exist if the claim is true."""
        prompt = f"""A team member named "{claimant}" claims: "{claim}"

If this claim is TRUE, what specific evidence MUST we expect to find in:
1. Git commit logs (specific commits, file changes, patterns)
2. Meeting transcripts (discussions, presentations, questions they asked/answered)

List the expected evidence as bullet points. Be specific about what we'd look for."""

        try:
            return await self.gemini.analyze(prompt)
        except Exception as e:
            print(f"Error getting expected evidence: {e}")
            return ""
    
    async def _find_supporting_evidence(
        self,
        claimant: str,
        claim: str,
        evidence_context: str,
        expected_evidence: str
    ) -> list[Evidence]:
        """Find evidence that supports the claim."""
        prompt = f"""Analyze this evidence to find SUPPORT for the claim.

CLAIM: "{claimant}" says: "{claim}"

EXPECTED EVIDENCE (if claim is true):
{expected_evidence}

YOUR TASK: Search the evidence below and list ONLY items that SUPPORT the claim.
For each supporting item, specify:
1. Source type (git_commit or meeting_transcript)
2. Source ID (commit hash or line number)
3. What it shows
4. Strength (strong/moderate/weak)

EVIDENCE:
{evidence_context}

OUTPUT FORMAT (JSON array):
[
  {{"type": "git_commit", "source": "abc123", "summary": "what it shows", "strength": "strong"}},
  ...
]

Return ONLY the JSON array, no other text. If no supporting evidence found, return []."""

        try:
            response = await self.gemini.analyze(prompt)
            return self._parse_evidence_list(response, claim_type="supporting")
        except Exception as e:
            print(f"Error finding supporting evidence: {e}")
            return []
    
    async def _find_counter_evidence(
        self,
        claimant: str,
        claim: str,
        evidence_context: str
    ) -> list[Evidence]:
        """
        Find evidence that DISPROVES the claim.
        
        THIS IS THE KEY INSIGHT - we actively look for contradictions.
        """
        prompt = f"""Analyze this evidence to find anything that DISPROVES or CONTRADICTS the claim.

CLAIM: "{claimant}" says: "{claim}"

YOUR TASK: Search for COUNTER-EVIDENCE such as:
- Someone ELSE did the work (different author in git)
- Timeline mismatches (work done before/after claimant's involvement)
- Contradicting statements in transcripts
- Evidence showing minimal or no involvement by claimant

For each counter-evidence item, specify:
1. Source type (git_commit or meeting_transcript)
2. Source ID
3. What it shows
4. Strength (strong/moderate/weak)

EVIDENCE:
{evidence_context}

OUTPUT FORMAT (JSON array):
[
  {{"type": "git_commit", "source": "def456", "summary": "Shows Bob authored auth module, not Alice", "strength": "strong"}},
  ...
]

Return ONLY the JSON array. If no counter-evidence found, return []."""

        try:
            response = await self.gemini.analyze(prompt)
            return self._parse_evidence_list(response, claim_type="counter")
        except Exception as e:
            print(f"Error finding counter evidence: {e}")
            return []
    
    async def _find_missing_evidence(
        self,
        claimant: str,
        claim: str,
        evidence_context: str,
        expected_evidence: str
    ) -> list[str]:
        """Find expected evidence that is MISSING."""
        prompt = f"""Compare expected evidence against actual evidence for gaps.

CLAIM: "{claimant}" says: "{claim}"

EXPECTED EVIDENCE (if claim is true):
{expected_evidence}

ACTUAL EVIDENCE:
{evidence_context}

YOUR TASK: List any EXPECTED evidence that is MISSING from the actual evidence.
Only list significant gaps, not minor details.

OUTPUT FORMAT (JSON array of strings):
["No commits from claimant touching auth files", "No mention of claimant presenting this feature", ...]

Return ONLY the JSON array. If all expected evidence is present, return []."""

        try:
            response = await self.gemini.analyze(prompt)
            return self._parse_string_list(response)
        except Exception as e:
            print(f"Error finding missing evidence: {e}")
            return []
    
    async def _synthesize_verdict(
        self,
        claimant: str,
        claim: str,
        supporting: list[Evidence],
        counter: list[Evidence],
        missing: list[str],
        evidence_context: str
    ) -> VerificationVerdict:
        """Synthesize the final verdict from all evidence."""
        
        # Prepare summary for Gemini
        supporting_summary = "\n".join(
            f"- {e.summary} (source: {e.source}, strength: {e.strength.value})"
            for e in supporting
        ) or "None found"
        
        counter_summary = "\n".join(
            f"- {e.summary} (source: {e.source}, strength: {e.strength.value})"
            for e in counter
        ) or "None found"
        
        missing_summary = "\n".join(f"- {m}" for m in missing) or "None"
        
        prompt = f"""Synthesize a final verdict on this contribution claim.

CLAIM: "{claimant}" says: "{claim}"

SUPPORTING EVIDENCE:
{supporting_summary}

COUNTER-EVIDENCE:
{counter_summary}

MISSING EVIDENCE:
{missing_summary}

Based on the balance of evidence, provide:
1. VERDICT: One of "VERIFIED", "DISPUTED", or "UNVERIFIABLE"
   - VERIFIED: Strong supporting evidence, minimal counter-evidence
   - DISPUTED: Significant counter-evidence that contradicts the claim
   - UNVERIFIABLE: Not enough evidence to confirm or deny
2. CONFIDENCE: A decimal between 0.0 and 1.0
3. EXPLANATION: A 2-3 sentence explanation citing specific evidence

OUTPUT FORMAT (JSON):
{{"verdict": "VERIFIED", "confidence": 0.85, "explanation": "..."}}

Return ONLY the JSON object."""

        try:
            response = await self.gemini.analyze(prompt)
            result = self._parse_verdict_response(response)
            
            return VerificationVerdict(
                claim=claim,
                claimant=claimant,
                verdict=VerdictType(result.get("verdict", "unverifiable").lower()),
                confidence=float(result.get("confidence", 0.5)),
                explanation=result.get("explanation", "Unable to generate explanation."),
                supporting_evidence=supporting,
                counter_evidence=counter,
                missing_evidence=missing
            )
        except Exception as e:
            print(f"Error synthesizing verdict: {e}")
            return self._create_unverifiable_verdict(
                claimant, claim, f"Error during analysis: {str(e)}"
            )
    
    def _parse_evidence_list(self, response: str, claim_type: str) -> list[Evidence]:
        """Parse Gemini's response into Evidence objects."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\[[\s\S]*\]', response)
            if not json_match:
                return []
            
            data = json.loads(json_match.group())
            evidence_list = []
            
            for item in data:
                evidence_list.append(Evidence(
                    type=EvidenceType(item.get("type", "git_commit")),
                    source=str(item.get("source", "")),
                    summary=item.get("summary", ""),
                    strength=EvidenceStrength(item.get("strength", "moderate").lower())
                ))
            
            return evidence_list
        except Exception as e:
            print(f"Error parsing evidence list: {e}")
            return []
    
    def _parse_string_list(self, response: str) -> list[str]:
        """Parse Gemini's response into a list of strings."""
        try:
            json_match = re.search(r'\[[\s\S]*\]', response)
            if not json_match:
                return []
            
            data = json.loads(json_match.group())
            return [str(item) for item in data if item]
        except Exception as e:
            print(f"Error parsing string list: {e}")
            return []
    
    def _parse_verdict_response(self, response: str) -> dict:
        """Parse Gemini's verdict response."""
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                return {}
            
            return json.loads(json_match.group())
        except Exception as e:
            print(f"Error parsing verdict response: {e}")
            return {}
    
    def _create_unverifiable_verdict(
        self,
        claimant: str,
        claim: str,
        reason: str
    ) -> VerificationVerdict:
        """Create an unverifiable verdict with a reason."""
        return VerificationVerdict(
            claim=claim,
            claimant=claimant,
            verdict=VerdictType.UNVERIFIABLE,
            confidence=0.0,
            explanation=reason,
            supporting_evidence=[],
            counter_evidence=[],
            missing_evidence=["Insufficient evidence for analysis"]
        )
    
    def _heuristic_verification(
        self,
        claimant: str,
        claim: str,
        evidence_context: str
    ) -> VerificationVerdict:
        """
        Fallback heuristic verification when Gemini is not available.
        
        Uses simple pattern matching to find evidence.
        """
        evidence_lower = evidence_context.lower()
        claimant_lower = claimant.lower()
        
        # Count mentions of claimant in evidence
        claimant_mentions = evidence_lower.count(claimant_lower)
        
        # Check if claimant appears in git commits
        git_pattern = re.compile(rf'\[[\w]+\]\s*{re.escape(claimant_lower)}', re.IGNORECASE)
        git_matches = git_pattern.findall(evidence_context)
        
        # Check transcript for claimant speaking
        transcript_pattern = re.compile(rf'\[\w+\]\s*{re.escape(claimant_lower)}:', re.IGNORECASE)
        transcript_matches = transcript_pattern.findall(evidence_context)
        
        supporting = []
        counter = []
        missing = []
        
        if git_matches:
            supporting.append(Evidence(
                type=EvidenceType.GIT_COMMIT,
                source="heuristic",
                summary=f"Found {len(git_matches)} commits by {claimant}",
                strength=EvidenceStrength.MODERATE if len(git_matches) > 2 else EvidenceStrength.WEAK
            ))
        else:
            missing.append(f"No git commits found from {claimant}")
        
        if transcript_matches:
            supporting.append(Evidence(
                type=EvidenceType.MEETING_TRANSCRIPT,
                source="heuristic",
                summary=f"Found {len(transcript_matches)} statements by {claimant}",
                strength=EvidenceStrength.MODERATE
            ))
        
        # Determine verdict based on evidence balance
        if claimant_mentions > 5 and git_matches:
            verdict = VerdictType.VERIFIED
            confidence = min(0.7 + (claimant_mentions * 0.02), 0.95)
            explanation = f"Heuristic analysis found {claimant_mentions} mentions of {claimant} in the evidence, including {len(git_matches)} git commits. This suggests active involvement."
        elif claimant_mentions > 0:
            verdict = VerdictType.UNVERIFIABLE
            confidence = 0.4
            explanation = f"Limited evidence found for {claimant}'s claim. Found {claimant_mentions} mentions but insufficient to confirm specific contributions. Enable Gemini API for deeper analysis."
        else:
            verdict = VerdictType.DISPUTED
            confidence = 0.6
            explanation = f"No evidence found linking {claimant} to the claimed work. Zero mentions in git logs or meeting transcripts."
            counter.append(Evidence(
                type=EvidenceType.GIT_COMMIT,
                source="heuristic",
                summary=f"No activity found for {claimant}",
                strength=EvidenceStrength.STRONG
            ))
        
        return VerificationVerdict(
            claim=claim,
            claimant=claimant,
            verdict=verdict,
            confidence=confidence,
            explanation=explanation + " (Heuristic mode - configure GEMINI_API_KEY for AI-powered analysis)",
            supporting_evidence=supporting,
            counter_evidence=counter,
            missing_evidence=missing
        )


# Singleton instance
_engine: Optional[ClaimVerificationEngine] = None


def get_verification_engine() -> ClaimVerificationEngine:
    """Get or create the verification engine singleton."""
    global _engine
    if _engine is None:
        gemini = None
        if is_gemini_configured():
            from analysis.gemini_client import get_gemini_client
            gemini = get_gemini_client()
        _engine = ClaimVerificationEngine(gemini)
    return _engine
