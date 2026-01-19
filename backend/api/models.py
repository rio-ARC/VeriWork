"""
Data Models - Unified Internal Representations
Contribution Truth
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    """Types of evidence sources"""
    GIT_COMMIT = "git_commit"
    MEETING_TRANSCRIPT = "meeting_transcript"
    DOCUMENT_EDIT = "document_edit"
    TASK_BOARD = "task_board"


class EvidenceStrength(str, Enum):
    """Strength levels for evidence"""
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"


class VerdictType(str, Enum):
    """Possible verdict outcomes"""
    VERIFIED = "verified"
    DISPUTED = "disputed"
    UNVERIFIABLE = "unverifiable"


# =============================================================================
# Git Data Models
# =============================================================================

class GitFileChange(BaseModel):
    """A single file change in a commit"""
    filename: str
    additions: int = 0
    deletions: int = 0
    status: str = "modified"  # added, modified, deleted, renamed


class GitCommit(BaseModel):
    """A single git commit"""
    hash: str
    short_hash: str = ""
    author_name: str
    author_email: str = ""
    timestamp: datetime
    message: str
    files_changed: list[GitFileChange] = []
    
    def model_post_init(self, __context):
        if not self.short_hash:
            self.short_hash = self.hash[:7]


class GitLog(BaseModel):
    """Parsed git log containing all commits"""
    commits: list[GitCommit] = []
    contributors: list[str] = []
    
    def model_post_init(self, __context):
        if not self.contributors and self.commits:
            self.contributors = list(set(c.author_name for c in self.commits))


# =============================================================================
# Meeting Transcript Models
# =============================================================================

class TranscriptStatement(BaseModel):
    """A single statement in a meeting transcript"""
    speaker: str
    content: str
    timestamp: Optional[str] = None
    line_number: int = 0


class MeetingTranscript(BaseModel):
    """Parsed meeting transcript"""
    title: str = "Meeting"
    date: Optional[datetime] = None
    statements: list[TranscriptStatement] = []
    participants: list[str] = []
    
    def model_post_init(self, __context):
        if not self.participants and self.statements:
            self.participants = list(set(s.speaker for s in self.statements))


# =============================================================================
# Evidence Models
# =============================================================================

class Evidence(BaseModel):
    """A piece of evidence from any source"""
    type: EvidenceType
    source: str  # e.g., commit hash, transcript line
    summary: str
    strength: EvidenceStrength = EvidenceStrength.MODERATE
    raw_data: Optional[dict] = None


class EvidenceCollection(BaseModel):
    """All evidence for a verification session"""
    git_log: Optional[GitLog] = None
    transcripts: list[MeetingTranscript] = []
    
    @property
    def all_contributors(self) -> list[str]:
        """Get all unique contributors across sources"""
        contributors = set()
        if self.git_log:
            contributors.update(self.git_log.contributors)
        for t in self.transcripts:
            contributors.update(t.participants)
        return sorted(list(contributors))


# =============================================================================
# Claim & Verdict Models
# =============================================================================

class ContributionClaim(BaseModel):
    """A claim made by a contributor"""
    claimant: str
    claim: str
    timestamp: datetime = Field(default_factory=datetime.now)


class VerificationVerdict(BaseModel):
    """The verdict for a claim verification"""
    claim: str
    claimant: str
    verdict: VerdictType
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str
    supporting_evidence: list[Evidence] = []
    counter_evidence: list[Evidence] = []
    missing_evidence: list[str] = []
    
    def to_dict(self) -> dict:
        """Convert to dict for JSON response"""
        return {
            "claim": self.claim,
            "claimant": self.claimant,
            "verdict": self.verdict.value.upper(),
            "confidence": self.confidence,
            "explanation": self.explanation,
            "supporting_evidence": [
                {
                    "type": e.type.value,
                    "source": e.source,
                    "summary": e.summary,
                    "strength": e.strength.value
                }
                for e in self.supporting_evidence
            ],
            "counter_evidence": [
                {
                    "type": e.type.value,
                    "source": e.source,
                    "summary": e.summary,
                    "strength": e.strength.value
                }
                for e in self.counter_evidence
            ],
            "missing_evidence": self.missing_evidence
        }


# =============================================================================
# API Request/Response Models
# =============================================================================

class VerifyClaimRequest(BaseModel):
    """Request to verify a claim"""
    claimant: str
    claim: str


class UploadResponse(BaseModel):
    """Response after uploading evidence"""
    success: bool
    message: str
    git_commits_parsed: int = 0
    transcript_statements_parsed: int = 0
    contributors_found: list[str] = []
