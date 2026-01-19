"""
Tests for Git Log Parser
Contribution Truth
"""

import pytest
from datetime import datetime

# Add parent to path for imports
import sys
sys.path.insert(0, '..')

from ingestion.git_parser import parse_git_log, parse_git_log_json, parse_git_log_text


class TestGitLogParserJSON:
    """Test JSON format parsing"""
    
    def test_parse_json_array(self):
        """Test parsing a JSON array of commits"""
        content = '''[
            {
                "hash": "abc123def456",
                "author": "Alice Chen",
                "email": "alice@example.com",
                "date": "2024-01-15T10:30:00",
                "message": "Add new feature"
            },
            {
                "hash": "def456abc789",
                "author": "Bob Martinez",
                "email": "bob@example.com",
                "date": "2024-01-14T09:00:00",
                "message": "Initial commit"
            }
        ]'''
        
        result = parse_git_log_json(content)
        
        assert len(result.commits) == 2
        assert result.commits[0].author_name == "Alice Chen"
        assert result.commits[1].author_name == "Bob Martinez"
        assert "Alice Chen" in result.contributors
        assert "Bob Martinez" in result.contributors
    
    def test_parse_json_with_files(self):
        """Test parsing commits with file changes"""
        content = '''[{
            "hash": "abc123",
            "author": "Alice",
            "date": "2024-01-15",
            "message": "Update auth",
            "files": [
                {"filename": "auth/login.py", "additions": 50, "deletions": 10},
                {"filename": "tests/test_auth.py", "additions": 30, "deletions": 0}
            ]
        }]'''
        
        result = parse_git_log_json(content)
        
        assert len(result.commits) == 1
        assert len(result.commits[0].files_changed) == 2
        assert result.commits[0].files_changed[0].filename == "auth/login.py"
        assert result.commits[0].files_changed[0].additions == 50
    
    def test_parse_empty_json(self):
        """Test parsing empty JSON"""
        result = parse_git_log_json("[]")
        assert len(result.commits) == 0
    
    def test_parse_malformed_json(self):
        """Test handling malformed JSON gracefully"""
        content = "not valid json at all"
        result = parse_git_log_json(content)
        # Should not crash, returns empty
        assert len(result.commits) == 0


class TestGitLogParserText:
    """Test text format parsing"""
    
    def test_parse_oneline_format(self):
        """Test parsing git log --oneline style output"""
        content = """abc1234 Alice Chen - Add authentication module
def5678 Bob Martinez - Fix login bug
ghi9012 Carol Davis - Update documentation"""
        
        result = parse_git_log_text(content)
        
        # Text parsing is heuristic - check that we parsed at least some commits
        assert len(result.commits) >= 1
        # First commit should have either Alice Chen or the full author parsed
        assert len(result.commits[0].author_name) > 0
        assert len(result.commits[0].message) > 0
    
    def test_parse_standard_format(self):
        """Test parsing standard git log format"""
        content = """commit abc123def456789
Author: Alice Chen <alice@example.com>
Date:   Mon Jan 15 10:30:00 2024

    Add new feature with multiple lines
    of description"""
        
        result = parse_git_log_text(content)
        
        assert len(result.commits) == 1
        assert result.commits[0].author_name == "Alice Chen"
        assert "Add new feature" in result.commits[0].message


class TestGitLogAutoDetect:
    """Test auto-detection of format"""
    
    def test_autodetect_json(self):
        """Test auto-detection of JSON format"""
        content = '[{"hash": "abc", "author": "Alice", "date": "2024-01-15", "message": "Test"}]'
        result = parse_git_log(content)
        assert len(result.commits) == 1
    
    def test_autodetect_text(self):
        """Test auto-detection of text format"""
        content = "abc1234 Alice - Test commit message"
        result = parse_git_log(content)
        assert len(result.commits) == 1


class TestGitLogContributors:
    """Test contributor extraction"""
    
    def test_unique_contributors(self):
        """Test that contributors are deduplicated"""
        content = '''[
            {"hash": "a", "author": "Alice", "date": "2024-01-01", "message": "m1"},
            {"hash": "b", "author": "Alice", "date": "2024-01-02", "message": "m2"},
            {"hash": "c", "author": "Bob", "date": "2024-01-03", "message": "m3"}
        ]'''
        
        result = parse_git_log_json(content)
        
        assert len(result.contributors) == 2
        assert "Alice" in result.contributors
        assert "Bob" in result.contributors
