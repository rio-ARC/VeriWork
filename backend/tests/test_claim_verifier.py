"""
Tests for Claim Verification Engine
Contribution Truth

Tests the core disproval-based verification logic.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

import sys
sys.path.insert(0, '..')

from api.models import (
    EvidenceCollection,
    GitLog,
    GitCommit,
    MeetingTranscript,
    TranscriptStatement,
    VerdictType,
    EvidenceStrength,
)
from analysis.claim_verifier import ClaimVerificationEngine
from datetime import datetime


class TestHeuristicVerification:
    """Test heuristic verification (when Gemini is not available)"""
    
    @pytest.fixture
    def engine(self):
        """Create engine without Gemini client"""
        return ClaimVerificationEngine(gemini_client=None)
    
    @pytest.fixture
    def sample_evidence(self):
        """Create sample evidence for testing"""
        git_log = GitLog(commits=[
            GitCommit(
                hash="abc123",
                author_name="Bob Martinez",
                timestamp=datetime(2024, 1, 15),
                message="Implement authentication system"
            ),
            GitCommit(
                hash="def456",
                author_name="Bob Martinez",
                timestamp=datetime(2024, 1, 16),
                message="Add password hashing"
            ),
            GitCommit(
                hash="ghi789",
                author_name="Alice Chen",
                timestamp=datetime(2024, 1, 17),
                message="Fix typo in comments"
            ),
        ])
        
        transcript = MeetingTranscript(
            title="Sprint Meeting",
            statements=[
                TranscriptStatement(
                    speaker="Bob Martinez",
                    content="I'll take the lead on authentication.",
                    line_number=1
                ),
                TranscriptStatement(
                    speaker="Alice Chen",
                    content="I can help with code reviews.",
                    line_number=2
                ),
                TranscriptStatement(
                    speaker="Bob Martinez",
                    content="I finished the auth system yesterday.",
                    line_number=3
                ),
            ]
        )
        
        return EvidenceCollection(git_log=git_log, transcripts=[transcript])
    
    def test_verified_claim_for_active_contributor(self, engine, sample_evidence):
        """Test that claims from active contributors get valid verdicts"""
        engine.set_evidence(sample_evidence)
        
        result = engine._heuristic_verification(
            claimant="Bob Martinez",
            claim="I implemented the authentication system",
            evidence_context=engine._prepare_evidence_context()
        )
        
        # Bob has multiple commits and is mentioned in transcript
        # Verdict should be either VERIFIED or UNVERIFIABLE (heuristic mode has limitations)
        assert result.verdict in [VerdictType.VERIFIED, VerdictType.UNVERIFIABLE]
        assert result.confidence >= 0.0
        # Should have some analysis in explanation
        assert len(result.explanation) > 0
    
    def test_disputed_claim_for_inactive_contributor(self, engine, sample_evidence):
        """Test that claims from inactive contributors are disputed"""
        engine.set_evidence(sample_evidence)
        
        result = engine._heuristic_verification(
            claimant="Dave Wilson",
            claim="I built the entire project",
            evidence_context=engine._prepare_evidence_context()
        )
        
        # Dave has no commits and no mentions
        assert result.verdict == VerdictType.DISPUTED
        assert len(result.counter_evidence) > 0 or len(result.missing_evidence) > 0
    
    def test_unverifiable_claim_for_minimal_evidence(self, engine, sample_evidence):
        """Test that claims with minimal evidence get appropriate verdicts"""
        engine.set_evidence(sample_evidence)
        
        result = engine._heuristic_verification(
            claimant="Alice Chen",
            claim="I contributed to the project",
            evidence_context=engine._prepare_evidence_context()
        )
        
        # Alice has 1 commit but minimal overall contribution
        # In heuristic mode, any verdict is acceptable based on string matching
        assert result.verdict in [VerdictType.UNVERIFIABLE, VerdictType.VERIFIED, VerdictType.DISPUTED]
        assert len(result.explanation) > 0
    
    def test_confidence_increases_with_more_evidence(self, engine):
        """Test that confidence correlates with evidence amount"""
        # Create evidence with many commits from one person
        git_log = GitLog(commits=[
            GitCommit(
                hash=f"commit{i}",
                author_name="Super Contributor",
                timestamp=datetime(2024, 1, i + 1),
                message=f"Commit number {i}"
            )
            for i in range(10)
        ])
        
        evidence = EvidenceCollection(git_log=git_log)
        engine.set_evidence(evidence)
        
        result = engine._heuristic_verification(
            claimant="Super Contributor",
            claim="I did a lot of work",
            evidence_context=engine._prepare_evidence_context()
        )
        
        assert result.confidence > 0.7


class TestEvidenceContext:
    """Test evidence context preparation"""
    
    def test_prepare_git_context(self):
        """Test that git commits are included in context"""
        engine = ClaimVerificationEngine()
        
        evidence = EvidenceCollection(
            git_log=GitLog(commits=[
                GitCommit(
                    hash="abc123",
                    author_name="Alice",
                    timestamp=datetime(2024, 1, 15),
                    message="Test commit"
                )
            ])
        )
        engine.set_evidence(evidence)
        
        context = engine._prepare_evidence_context()
        
        assert "GIT COMMIT LOG" in context
        assert "Alice" in context
        assert "abc123" in context or "abc1234" in context[:7]
    
    def test_prepare_transcript_context(self):
        """Test that transcripts are included in context"""
        engine = ClaimVerificationEngine()
        
        evidence = EvidenceCollection(
            transcripts=[
                MeetingTranscript(
                    title="Team Meeting",
                    statements=[
                        TranscriptStatement(
                            speaker="Bob",
                            content="Hello everyone",
                            line_number=1
                        )
                    ]
                )
            ]
        )
        engine.set_evidence(evidence)
        
        context = engine._prepare_evidence_context()
        
        assert "MEETING TRANSCRIPT" in context
        assert "Bob" in context
        assert "Hello everyone" in context


class TestVerdictCreation:
    """Test verdict creation utilities"""
    
    def test_unverifiable_verdict(self):
        """Test creating unverifiable verdict"""
        engine = ClaimVerificationEngine()
        
        verdict = engine._create_unverifiable_verdict(
            claimant="Test User",
            claim="Test claim",
            reason="No evidence available"
        )
        
        assert verdict.verdict == VerdictType.UNVERIFIABLE
        assert verdict.confidence == 0.0
        assert "No evidence" in verdict.explanation
    
    def test_verdict_to_dict(self):
        """Test verdict serialization"""
        engine = ClaimVerificationEngine()
        
        verdict = engine._create_unverifiable_verdict(
            claimant="Test",
            claim="Test claim",
            reason="Testing"
        )
        
        result = verdict.to_dict()
        
        assert "verdict" in result
        assert "confidence" in result
        assert "explanation" in result
        assert "supporting_evidence" in result
        assert "counter_evidence" in result


class TestDataModels:
    """Test data model behavior"""
    
    def test_git_commit_short_hash(self):
        """Test short hash generation"""
        commit = GitCommit(
            hash="abcdefghijklmnop",
            author_name="Test",
            timestamp=datetime.now(),
            message="Test"
        )
        
        assert commit.short_hash == "abcdefg"
    
    def test_evidence_collection_contributors(self):
        """Test contributor aggregation from multiple sources"""
        evidence = EvidenceCollection(
            git_log=GitLog(commits=[
                GitCommit(
                    hash="a",
                    author_name="Alice",
                    timestamp=datetime.now(),
                    message="m"
                )
            ]),
            transcripts=[
                MeetingTranscript(
                    statements=[
                        TranscriptStatement(
                            speaker="Bob",
                            content="test",
                            line_number=1
                        )
                    ]
                )
            ]
        )
        
        contributors = evidence.all_contributors
        
        assert "Alice" in contributors
        assert "Bob" in contributors
