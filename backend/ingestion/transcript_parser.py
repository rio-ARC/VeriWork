"""
Meeting Transcript Parser
Contribution Truth

Parses meeting transcripts with speaker attribution.
"""

import re
from datetime import datetime
from typing import Optional

from api.models import MeetingTranscript, TranscriptStatement


def parse_transcript(content: str, title: str = "Meeting") -> MeetingTranscript:
    """
    Parse a meeting transcript with speaker attribution.
    
    Supports multiple formats:
    1. "Speaker: message" format
    2. "[Speaker] message" format
    3. "Speaker - message" format
    4. Timestamped: "[HH:MM:SS] Speaker: message"
    """
    statements = []
    current_speaker = None
    current_content = []
    line_number = 0
    meeting_date = None
    
    lines = content.strip().split('\n')
    
    # Try to extract date from first few lines
    for line in lines[:5]:
        date = _extract_date(line)
        if date:
            meeting_date = date
            break
    
    # Patterns for speaker attribution
    patterns = [
        # "[HH:MM:SS] Speaker: message" or "[HH:MM] Speaker: message"
        re.compile(r'^\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*([^:\[\]]+?):\s*(.+)$'),
        # "Speaker: message"
        re.compile(r'^([^:\[\]]{2,30}):\s*(.+)$'),
        # "[Speaker] message"
        re.compile(r'^\[([^\]]+)\]\s*(.+)$'),
        # "Speaker - message"
        re.compile(r'^([^-]{2,30})\s*-\s*(.+)$'),
    ]
    
    for line in lines:
        line_number += 1
        line = line.strip()
        
        if not line:
            continue
        
        # Skip header-like lines
        if _is_header_line(line):
            continue
        
        # Try each pattern
        matched = False
        for pattern in patterns:
            match = pattern.match(line)
            if match:
                # Save previous speaker's content
                if current_speaker and current_content:
                    statements.append(TranscriptStatement(
                        speaker=_normalize_speaker(current_speaker),
                        content=' '.join(current_content),
                        line_number=line_number - len(current_content)
                    ))
                    current_content = []
                
                groups = match.groups()
                if len(groups) == 3:
                    # Timestamped format
                    timestamp, speaker, message = groups
                    statements.append(TranscriptStatement(
                        speaker=_normalize_speaker(speaker),
                        content=message.strip(),
                        timestamp=timestamp,
                        line_number=line_number
                    ))
                    current_speaker = None
                    current_content = []
                else:
                    # Non-timestamped format
                    speaker, message = groups
                    current_speaker = speaker
                    current_content = [message.strip()]
                
                matched = True
                break
        
        if not matched:
            # Continuation of previous speaker's message
            if current_speaker:
                current_content.append(line)
            else:
                # Standalone line, attribute to "Unknown" or skip
                pass
    
    # Don't forget the last statement
    if current_speaker and current_content:
        statements.append(TranscriptStatement(
            speaker=_normalize_speaker(current_speaker),
            content=' '.join(current_content),
            line_number=line_number - len(current_content) + 1
        ))
    
    return MeetingTranscript(
        title=title,
        date=meeting_date,
        statements=statements
    )


def _normalize_speaker(speaker: str) -> str:
    """Normalize speaker name"""
    speaker = speaker.strip()
    # Remove common prefixes
    prefixes = ['Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Prof.']
    for prefix in prefixes:
        if speaker.startswith(prefix):
            speaker = speaker[len(prefix):].strip()
    return speaker.title()


def _is_header_line(line: str) -> bool:
    """Check if a line is a header/metadata line"""
    header_indicators = [
        'meeting transcript',
        'meeting notes',
        'attendees:',
        'participants:',
        'date:',
        'time:',
        'location:',
        '---',
        '===',
        '***',
    ]
    line_lower = line.lower()
    return any(ind in line_lower for ind in header_indicators)


def _extract_date(line: str) -> Optional[datetime]:
    """Try to extract a date from a line"""
    # Common date patterns
    patterns = [
        r'(\d{4}-\d{2}-\d{2})',  # 2024-01-15
        r'(\d{2}/\d{2}/\d{4})',  # 01/15/2024
        r'(\d{2}-\d{2}-\d{4})',  # 01-15-2024
    ]
    
    for pattern in patterns:
        match = re.search(pattern, line)
        if match:
            date_str = match.group(1)
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
    
    return None


def extract_speaker_mentions(transcript: MeetingTranscript, name: str) -> list[TranscriptStatement]:
    """
    Extract all statements where a specific person is mentioned.
    
    Useful for finding evidence of someone's involvement.
    """
    name_lower = name.lower()
    mentions = []
    
    for statement in transcript.statements:
        if name_lower in statement.content.lower():
            mentions.append(statement)
    
    return mentions


def get_speaker_summary(transcript: MeetingTranscript) -> dict[str, dict]:
    """
    Get a summary of each speaker's participation.
    
    Returns dict with speaker names as keys and summary stats as values.
    """
    summary = {}
    
    for statement in transcript.statements:
        speaker = statement.speaker
        if speaker not in summary:
            summary[speaker] = {
                'statement_count': 0,
                'total_words': 0,
                'topics_discussed': []
            }
        
        summary[speaker]['statement_count'] += 1
        summary[speaker]['total_words'] += len(statement.content.split())
    
    return summary
