"""
Git Log Parser
Contribution Truth

Parses git log output in various formats and normalizes to internal model.
"""

import json
import re
from datetime import datetime
from typing import Optional

from api.models import GitCommit, GitFileChange, GitLog


def parse_git_log_json(content: str) -> GitLog:
    """
    Parse git log output in JSON format.
    
    Expected format from: git log --pretty=format:'{"hash":"%H","author":"%an","email":"%ae","date":"%aI","message":"%s"},'
    
    Or a JSON array of commit objects.
    """
    commits = []
    
    # Try parsing as JSON array first
    try:
        # Clean up common issues with git log JSON output
        content = content.strip()
        if content.endswith(','):
            content = content[:-1]
        if not content.startswith('['):
            content = '[' + content + ']'
        
        data = json.loads(content)
        
        for item in data:
            commit = _parse_commit_object(item)
            if commit:
                commits.append(commit)
                
    except json.JSONDecodeError:
        # Fall back to line-by-line JSON parsing
        for line in content.strip().split('\n'):
            line = line.strip().rstrip(',')
            if not line:
                continue
            try:
                item = json.loads(line)
                commit = _parse_commit_object(item)
                if commit:
                    commits.append(commit)
            except json.JSONDecodeError:
                continue
    
    return GitLog(commits=commits)


def _parse_commit_object(item: dict) -> Optional[GitCommit]:
    """Parse a single commit object from JSON"""
    try:
        # Handle various key names
        hash_val = item.get('hash') or item.get('commit') or item.get('sha') or ''
        author = item.get('author') or item.get('author_name') or 'Unknown'
        email = item.get('email') or item.get('author_email') or ''
        message = item.get('message') or item.get('subject') or item.get('title') or ''
        
        # Parse date
        date_str = item.get('date') or item.get('timestamp') or item.get('authored_date')
        if isinstance(date_str, str):
            timestamp = _parse_date(date_str)
        elif isinstance(date_str, (int, float)):
            timestamp = datetime.fromtimestamp(date_str)
        else:
            timestamp = datetime.now()
        
        # Parse file changes if present
        files = []
        if 'files' in item:
            for f in item['files']:
                if isinstance(f, str):
                    files.append(GitFileChange(filename=f))
                elif isinstance(f, dict):
                    files.append(GitFileChange(
                        filename=f.get('filename') or f.get('name') or f.get('path', ''),
                        additions=f.get('additions', 0),
                        deletions=f.get('deletions', 0),
                        status=f.get('status', 'modified')
                    ))
        
        return GitCommit(
            hash=hash_val,
            author_name=author,
            author_email=email,
            timestamp=timestamp,
            message=message,
            files_changed=files
        )
    except Exception as e:
        print(f"Error parsing commit: {e}")
        return None


def parse_git_log_text(content: str) -> GitLog:
    """
    Parse git log output in standard text format.
    
    Expected format from: git log --oneline or git log
    """
    commits = []
    current_commit = {}
    
    lines = content.strip().split('\n')
    
    # Try oneline format first: "abc1234 Author Name - Commit message"
    oneline_pattern = re.compile(r'^([a-f0-9]{7,40})\s+(.+?)\s*-\s*(.+)$', re.IGNORECASE)
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for oneline format
        match = oneline_pattern.match(line)
        if match:
            commits.append(GitCommit(
                hash=match.group(1),
                author_name=match.group(2).strip(),
                timestamp=datetime.now(),  # Not available in oneline
                message=match.group(3).strip()
            ))
            continue
        
        # Try standard format
        if line.startswith('commit '):
            if current_commit.get('hash'):
                commits.append(_create_commit_from_dict(current_commit))
            current_commit = {'hash': line[7:].strip()}
        elif line.startswith('Author:'):
            author_match = re.match(r'Author:\s*(.+?)\s*<(.+?)>', line)
            if author_match:
                current_commit['author'] = author_match.group(1).strip()
                current_commit['email'] = author_match.group(2).strip()
            else:
                current_commit['author'] = line[7:].strip()
        elif line.startswith('Date:'):
            current_commit['date'] = line[5:].strip()
        elif line and not line.startswith('Merge:'):
            # This is likely the commit message
            if 'message' in current_commit:
                current_commit['message'] += ' ' + line
            else:
                current_commit['message'] = line
    
    # Don't forget the last commit
    if current_commit.get('hash'):
        commits.append(_create_commit_from_dict(current_commit))
    
    return GitLog(commits=commits)


def _create_commit_from_dict(data: dict) -> GitCommit:
    """Create a GitCommit from a dict of parsed values"""
    timestamp = datetime.now()
    if 'date' in data:
        timestamp = _parse_date(data['date'])
    
    return GitCommit(
        hash=data.get('hash', ''),
        author_name=data.get('author', 'Unknown'),
        author_email=data.get('email', ''),
        timestamp=timestamp,
        message=data.get('message', '').strip()
    )


def _parse_date(date_str: str) -> datetime:
    """Try to parse a date string in various formats"""
    formats = [
        '%Y-%m-%dT%H:%M:%S%z',  # ISO format with timezone
        '%Y-%m-%dT%H:%M:%S',    # ISO format without timezone
        '%a %b %d %H:%M:%S %Y %z',  # Git default format
        '%a %b %d %H:%M:%S %Y',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    return datetime.now()


def parse_git_log(content: str) -> GitLog:
    """
    Auto-detect format and parse git log.
    
    Tries JSON first, then falls back to text format.
    """
    content = content.strip()
    
    # Check if it looks like JSON
    if content.startswith('{') or content.startswith('['):
        return parse_git_log_json(content)
    
    # Otherwise parse as text
    return parse_git_log_text(content)
