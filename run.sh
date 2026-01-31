#!/bin/bash
set -e

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found. Please run './setup.sh' first."
    exit 1
fi

# Activate Environment
source venv/bin/activate

# Ensure Environment Variables are loaded (if not automatically by python-dotenv or similar)
# We rely on Config loading .env or system envs. 
# Exporting them here just in case if needed, or we just trust the app.

echo "[+] Initializing Database..."
# Run migration/init script. 
# Assuming migrate_db.py or similar logic exists. 
# If it doesn't exist, we fallback to just running app which creates tables on startup.
if [ -f "migrate_db.py" ]; then
    python3 migrate_db.py || echo "Warning: Migration script returned error (might be benign if user exists)."
fi

# Get Local IP (Linux specific)
IP_ADDR=$(hostname -I | awk '{print $1}')

echo "==========================================================="
echo "   LOCALSHARE OPS :: SYSTEM ONLINE"
echo "==========================================================="
echo "ACCESS POINTS:"
echo "   > LOCALHOST:   http://localhost:8000"
echo "   > WI-FI / LAN: http://$IP_ADDR:8000"
echo "==========================================================="
echo "Press CTRL+C to stop the server."

# Start Server
# --host 0.0.0.0 allows access from other devices on the network
exec python3 -m uvicorn localshare.app.main:app --host 0.0.0.0 --port 8000 --reload
