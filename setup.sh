#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

echo "=================================="
echo "   LOCALSHARE OPS SETUP SEQUENCE"
echo "=================================="

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 could not be found. Please install Python 3.9+."
    exit 1
fi

# Create Virtual Environment
if [ ! -d "venv" ]; then
    echo "[+] Creating virtual environment 'venv'..."
    python3 -m venv venv
else
    echo "[*] Virtual environment 'venv' already exists."
fi

# Activate Virtual Environment
source venv/bin/activate

# Install Dependencies
echo "[+] Installing requirements..."
pip install --upgrade pip
if [ -f "localshare/requirements.txt" ]; then
    pip install -r localshare/requirements.txt
else
    echo "ERROR: localshare/requirements.txt not found!"
    exit 1
fi

# Create .env if missing
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "[+] Creating .env from template..."
        cp .env.example .env
        echo "NOTE: Default .env created. Please edit it to change the SECRET_KEY."
    fi
fi

# Create uploads directory
mkdir -p uploads

echo "=================================="
echo "SETUP COMPLETED SUCCESSFULLY"
echo "Run './run.sh' to launch the server."
echo "=================================="
