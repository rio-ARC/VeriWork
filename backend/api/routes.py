"""
API Routes - REST Endpoints
Contribution Truth
"""

import os
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.models import (
    EvidenceCollection,
    UploadResponse,
    VerifyClaimRequest,
)
from ingestion.git_parser import parse_git_log
from ingestion.transcript_parser import parse_transcript
from analysis.claim_verifier import get_verification_engine
from analysis.gemini_client import is_gemini_configured


router = APIRouter(prefix="/api", tags=["Contribution Truth"])

# In-memory evidence storage (for prototype)
_current_evidence: Optional[EvidenceCollection] = None


@router.post("/evidence/upload", response_model=UploadResponse)
async def upload_evidence(
    git_log: Optional[UploadFile] = File(None),
    transcript: Optional[UploadFile] = File(None)
):
    """
    Upload evidence files for analysis.
    
    Accepts:
    - git_log: JSON or text output from git log
    - transcript: Meeting transcript with speaker attribution
    """
    global _current_evidence
    
    if not git_log and not transcript:
        raise HTTPException(status_code=400, detail="At least one file must be uploaded")
    
    evidence = EvidenceCollection()
    git_commits_parsed = 0
    transcript_statements_parsed = 0
    
    # Parse git log
    if git_log:
        try:
            content = await git_log.read()
            content_str = content.decode('utf-8')
            evidence.git_log = parse_git_log(content_str)
            git_commits_parsed = len(evidence.git_log.commits)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse git log: {str(e)}")
    
    # Parse transcript
    if transcript:
        try:
            content = await transcript.read()
            content_str = content.decode('utf-8')
            parsed = parse_transcript(content_str, title=transcript.filename or "Meeting")
            evidence.transcripts.append(parsed)
            transcript_statements_parsed = len(parsed.statements)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse transcript: {str(e)}")
    
    # Store evidence and set on verification engine
    _current_evidence = evidence
    engine = get_verification_engine()
    engine.set_evidence(evidence)
    
    return UploadResponse(
        success=True,
        message="Evidence uploaded and parsed successfully",
        git_commits_parsed=git_commits_parsed,
        transcript_statements_parsed=transcript_statements_parsed,
        contributors_found=evidence.all_contributors
    )


@router.post("/verify")
async def verify_claim(request: VerifyClaimRequest):
    """
    Verify a contribution claim against uploaded evidence.
    
    This is THE CORE feature - disproval-based verification.
    
    The engine tries to DISPROVE the claim. If it fails to disprove,
    the claim is likely true.
    """
    global _current_evidence
    
    if not _current_evidence:
        raise HTTPException(
            status_code=400,
            detail="No evidence uploaded. Please upload git logs and/or transcripts first."
        )
    
    if not request.claimant or not request.claim:
        raise HTTPException(
            status_code=400,
            detail="Both claimant name and claim text are required."
        )
    
    engine = get_verification_engine()
    
    try:
        verdict = await engine.verify_claim(
            claimant=request.claimant,
            claim=request.claim
        )
        return verdict.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Verification failed: {str(e)}"
        )


@router.get("/evidence/status")
async def evidence_status():
    """Get the current status of uploaded evidence."""
    global _current_evidence
    
    if not _current_evidence:
        return {
            "has_evidence": False,
            "git_commits": 0,
            "transcript_statements": 0,
            "contributors": []
        }
    
    transcript_statements = sum(
        len(t.statements) for t in _current_evidence.transcripts
    )
    
    return {
        "has_evidence": True,
        "git_commits": len(_current_evidence.git_log.commits) if _current_evidence.git_log else 0,
        "transcript_statements": transcript_statements,
        "contributors": _current_evidence.all_contributors,
        "gemini_enabled": is_gemini_configured()
    }


@router.delete("/evidence/clear")
async def clear_evidence():
    """Clear all uploaded evidence."""
    global _current_evidence
    _current_evidence = None
    
    return {"success": True, "message": "Evidence cleared"}
