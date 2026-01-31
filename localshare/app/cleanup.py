
import os
import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import File as FileModel, FileStatus
from .config import UPLOAD_DIRECTORY

def cleanup_expired_files():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        # SQLite storage might be naive, so we might need to handle this.
        # However, SQLAlchemy filtering usually handles it if we pass aware datetime?
        # If not, let's use naive for query if stored naive.
        # But we saved as UTC.
        # Let's try removing tzinfo from 'now' for the query if it fails, but let's assume it works or fix it if it errors.
        # Actually safer to let it be, but if it fails, we'll know.
        # The previous error was in Python code comparison, not SQL query.
        expired_files = db.query(FileModel).filter(
            FileModel.status == FileStatus.ACTIVE.value,
            FileModel.expires_at < now
        ).all()
        
        count = 0
        for file_record in expired_files:
            file_path = os.path.join(UPLOAD_DIRECTORY, file_record.uuid_filename)
            
            # Delete from disk
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as e:
                    print(f"Error deleting file {file_path}: {e}")
            
            # Update DB
            file_record.status = FileStatus.EXPIRED.value
            file_record.deleted_at = now
            count += 1
            
        if count > 0:
            db.commit()
            print(f"Cleanup: Removed {count} expired files.")
            
    except Exception as e:
        print(f"Cleanup Error: {e}")
    finally:
        db.close()

# For a simple background task, we can just run this loop in a thread or use fastapi-utils or just a loop in main's startup
# We'll expose the function here, and call it from main.
