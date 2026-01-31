
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database
DATABASE_URL = "sqlite:///./app.db"

# Storage
UPLOAD_DIRECTORY = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

# Security (Should be env var in prod, but local-only is okay-ish hardcoded if strictly strictly local)
# But for good practice, we'll try to get from env or default to a random string if not present?
# Since it's local-only and persistent, a fixed key is better for restarts if we don't want to invalidate sessions everywhere.
# Let's generate a strong key if not provided.
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME_IF_YOU_CARE_ABOUT_SECURITY_BUT_ITS_LOCAL")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 week sessions

# Constraints
MAX_UPLOAD_SIZE = 1024 * 1024 * 1024 # 1GB
APP_NAME = "LOCALSHARE OPS"
