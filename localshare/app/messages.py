
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from pydantic import BaseModel

from .database import get_db
from .models import User, Message
from .auth import get_current_user

router = APIRouter()

class MessageCreate(BaseModel):
    recipient_username: str
    content: str

class MessageResponse(BaseModel):
    id: int
    sender_username: str
    recipient_username: str
    content: str
    timestamp: datetime
    
    class Config:
        from_attributes = True

@router.post("/messages", response_model=MessageResponse)
async def send_message(
    msg: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recipient = db.query(User).filter(User.username == msg.recipient_username).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    new_message = Message(
        sender_id=current_user.id,
        recipient_id=recipient.id,
        content=msg.content
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    return MessageResponse(
        id=new_message.id,
        sender_username=current_user.username,
        recipient_username=recipient.username,
        content=new_message.content,
        timestamp=new_message.timestamp
    )

@router.get("/messages/{other_user_id}", response_model=List[MessageResponse])
async def get_conversation(
    other_user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify other user exists
    other_user = db.query(User).filter(User.id == other_user_id).first()
    if not other_user:
        raise HTTPException(status_code=404, detail="User not found")

    messages = db.query(Message).filter(
        ((Message.sender_id == current_user.id) & (Message.recipient_id == other_user_id)) |
        ((Message.sender_id == other_user_id) & (Message.recipient_id == current_user.id))
    ).order_by(Message.timestamp).all()
    
    return [
        MessageResponse(
            id=m.id,
            sender_username=m.sender.username if m.sender else "Unknown",
            recipient_username=m.recipient.username if m.recipient else "Unknown",
            content=m.content,
            timestamp=m.timestamp
        ) for m in messages
    ]

# Also valid to get all recent messages?
# The spec says "Users can send text messages to other users" and "Messages are stored persistently".
# UI says "Message streams" and "Message received" activity.
# A global endpoint for all my messages might be useful for the "inbox" view.

@router.get("/messages", response_model=List[MessageResponse])
async def get_all_my_messages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get all messages sent or received by me, ordered by time desc
    messages = db.query(Message).filter(
        (Message.sender_id == current_user.id) | (Message.recipient_id == current_user.id)
    ).order_by(Message.timestamp.desc()).limit(100).all()
    
    return [
        MessageResponse(
            id=m.id,
            sender_username=m.sender.username if m.sender else "Unknown",
            recipient_username=m.recipient.username if m.recipient else "Unknown",
            content=m.content,
            timestamp=m.timestamp
        ) for m in messages
    ]
