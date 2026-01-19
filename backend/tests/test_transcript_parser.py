"""
Tests for Meeting Transcript Parser
Contribution Truth
"""

import pytest

import sys
sys.path.insert(0, '..')

from ingestion.transcript_parser import (
    parse_transcript,
    extract_speaker_mentions,
    get_speaker_summary
)


class TestTranscriptParser:
    """Test transcript parsing in various formats"""
    
    def test_parse_colon_format(self):
        """Test parsing 'Speaker: message' format"""
        content = """Alice: I'll work on the frontend.
Bob: I can handle the backend API.
Alice: Great, let's sync tomorrow."""
        
        result = parse_transcript(content)
        
        assert len(result.statements) == 3
        assert result.statements[0].speaker == "Alice"
        assert result.statements[1].speaker == "Bob"
        assert "frontend" in result.statements[0].content
    
    def test_parse_timestamped_format(self):
        """Test parsing '[HH:MM] Speaker: message' format"""
        content = """[10:00] Alice: Let's start the meeting.
[10:02] Bob: I have an update on the auth system.
[10:05] Carol: The tests are passing now."""
        
        result = parse_transcript(content)
        
        assert len(result.statements) == 3
        assert result.statements[0].speaker == "Alice"
        assert result.statements[0].timestamp == "10:00"
        assert result.statements[1].speaker == "Bob"
    
    def test_parse_bracket_format(self):
        """Test parsing '[Speaker] message' format"""
        content = """[Alice] I finished the login component.
[Bob] Nice work! I'll review it today."""
        
        result = parse_transcript(content)
        
        assert len(result.statements) == 2
        assert result.statements[0].speaker == "Alice"
    
    def test_participants_extraction(self):
        """Test that participants are correctly extracted"""
        content = """Alice: First point.
Bob: Second point.
Alice: Third point.
Carol: Fourth point."""
        
        result = parse_transcript(content)
        
        assert len(result.participants) == 3
        assert "Alice" in result.participants
        assert "Bob" in result.participants
        assert "Carol" in result.participants
    
    def test_multiline_statement(self):
        """Test handling multi-line statements"""
        content = """Alice: This is a long statement
that continues on multiple lines
and should be captured together.
Bob: Next speaker here."""
        
        result = parse_transcript(content)
        
        assert len(result.statements) == 2
        assert "multiple lines" in result.statements[0].content
    
    def test_skip_headers(self):
        """Test that header lines are skipped"""
        content = """Meeting Transcript
Date: 2024-01-15
Participants: Alice, Bob
---
Alice: Let's begin.
Bob: Agreed."""
        
        result = parse_transcript(content)
        
        # Should only have the actual statements
        assert len(result.statements) == 2
    
    def test_empty_transcript(self):
        """Test handling empty transcript"""
        result = parse_transcript("")
        assert len(result.statements) == 0
        assert len(result.participants) == 0


class TestSpeakerMentions:
    """Test speaker mention extraction"""
    
    def test_find_mentions(self):
        """Test finding mentions of a person"""
        content = """Alice: I discussed with Bob about the API.
Bob: Thanks Alice for the clarification.
Carol: Bob's implementation looks good."""
        
        transcript = parse_transcript(content)
        mentions = extract_speaker_mentions(transcript, "Bob")
        
        # Bob is mentioned in Alice's and Carol's statements
        assert len(mentions) >= 2
    
    def test_case_insensitive_mentions(self):
        """Test case-insensitive mention search"""
        content = """Alice: BOB did a great job.
Carol: Yes, bob's code is clean."""
        
        transcript = parse_transcript(content)
        mentions = extract_speaker_mentions(transcript, "Bob")
        
        assert len(mentions) == 2


class TestSpeakerSummary:
    """Test speaker summary statistics"""
    
    def test_statement_count(self):
        """Test counting statements per speaker"""
        content = """Alice: First statement.
Bob: Second statement.
Alice: Third statement.
Alice: Fourth statement."""
        
        transcript = parse_transcript(content)
        summary = get_speaker_summary(transcript)
        
        assert summary["Alice"]["statement_count"] == 3
        assert summary["Bob"]["statement_count"] == 1
    
    def test_word_count(self):
        """Test word counting per speaker"""
        content = """Alice: One two three.
Bob: One two three four five."""
        
        transcript = parse_transcript(content)
        summary = get_speaker_summary(transcript)
        
        assert summary["Alice"]["total_words"] == 3
        assert summary["Bob"]["total_words"] == 5
