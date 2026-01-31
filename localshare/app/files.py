
import os
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Header
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .config import UPLOAD_DIRECTORY, MAX_UPLOAD_SIZE
from .database import get_db
from .models import User, File as FileModel, FileStatus
from .auth import get_current_user

router = APIRouter()

def validate_file_size(content_length: int = Header(None)):
    if content_length and content_length > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    return content_length

@router.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    recipient_username: str = Form(...),
    expiry_minutes: int = Form(...),
    content_length: int = Depends(validate_file_size),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate recipient
    recipient = db.query(User).filter(User.username == recipient_username).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    # Generate UUID and Path
    file_uuid = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIRECTORY, file_uuid)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not save file")
    
    # Calculate expiry
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)
    
    # Sanitize filename (basic)
    sanitized_filename = os.path.basename(file.filename)
    
    # Create DB record
    db_file = FileModel(
        uuid_filename=file_uuid,
        display_filename=sanitized_filename,
        sender_id=current_user.id,
        recipient_id=recipient.id,
        expires_at=expires_at,
        status=FileStatus.ACTIVE.value
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    return {"message": "File sent successfully", "file_id": db_file.id}

@router.get("/files/inbox")
async def get_inbox(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Get active files for recipient
    files = db.query(FileModel).filter(
        FileModel.recipient_id == current_user.id,
        FileModel.status == FileStatus.ACTIVE.value
    ).all()
    
    # Filter out expired ones just in case cleanup hasn't run, though we should show them as expired or not return them?
    # Logic: "Show expiry countdown". If expired, user can't download.
    # We return them, let frontend show status.
    # But wait, "Users can download UNTIL expiry". If expired, they shouldn't see it or it should be disabled.
    # Let's filter effectively valid files here for the "Inbox".
    
    valid_files = []
    now = datetime.now(timezone.utc)
    for f in files:
        # Ensure f.expires_at is timezone aware if naive.
        # SQLite stores naive, so we must attach UTC if missing.
        expires_at = f.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
            
        if expires_at > now:
            # We must assign the aware datetime back to the object or a dict for response
            f.expires_at = expires_at 
            valid_files.append(f)
    
    return valid_files

@router.get("/files/sent")
async def get_sent(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    files = db.query(FileModel).filter(
        FileModel.sender_id == current_user.id
    ).all()
    # Return all, assume logs style
    return files

@router.get("/files/{file_id}/download")
async def download_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
        
    # Ownership Check
    if file_record.recipient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this file")
    
    # Expiry Check
    if file_record.status != FileStatus.ACTIVE.value:
        raise HTTPException(status_code=410, detail="File is no longer active")
        
    expires_at = file_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        # Should have been cleaned up or status updated, but strictly enforcing here too
        raise HTTPException(status_code=410, detail="File has expired")

    # File Path
    file_path = os.path.join(UPLOAD_DIRECTORY, file_record.uuid_filename)
    if not os.path.exists(file_path):
        # Data inconsistency (DB says active, disk says gone)
        raise HTTPException(status_code=404, detail="File content missing")

    # Update downloaded_at
    file_record.downloaded_at = datetime.now(timezone.utc)
    db.commit()
    
    return FileResponse(
        path=file_path, 
        filename=file_record.display_filename,
        media_type='application/octet-stream'
    )
