
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def log(msg):
    print(f"[TEST] {msg}")

def check(resp, status_code=200):
    if resp.status_code != status_code:
        print(f"FAILED: Expected {status_code}, got {resp.status_code}")
        print(resp.text)
        return False
    return True

# 1. Register Users
session_alice = requests.Session()
session_bob = requests.Session()

log("Registering Alice...")
r = requests.post(f"{BASE_URL}/register", json={"username": "alice", "password": "password123"})
check(r, 200)

log("Registering Bob...")
r = requests.post(f"{BASE_URL}/register", json={"username": "bob", "password": "password123"})
check(r, 200)

# 2. Login
log("Logging in Alice...")
r = session_alice.post(f"{BASE_URL}/login", data={"username": "alice", "password": "password123"})
check(r, 200)

log("Logging in Bob...")
r = session_bob.post(f"{BASE_URL}/login", data={"username": "bob", "password": "password123"})
check(r, 200)

# 3. Send File Alice -> Bob
log("Alice sending file to Bob...")
files = {'file': ('test.txt', b'Hello World Content')}
data = {'recipient_username': 'bob', 'expiry_minutes': 1}
r = session_alice.post(f"{BASE_URL}/files/upload", files=files, data=data)
if check(r, 200):
    file_id = r.json()['file_id']
    log(f"File Sent, ID: {file_id}")
else:
    exit(1)

# 4. Bob Check Inbox
log("Bob checking inbox...")
r = session_bob.get(f"{BASE_URL}/files/inbox")
check(r, 200)
inbox = r.json()
if len(inbox) > 0 and inbox[0]['id'] == file_id:
    log("File found in inbox.")
else:
    log("File NOT found in inbox!")
    print(inbox)

# 5. Bob Download
log("Bob downloading file...")
r = session_bob.get(f"{BASE_URL}/files/{file_id}/download")
check(r, 200)
if r.content == b'Hello World Content':
    log("Download content verified.")
else:
    log("Download content mismatch!")

# 6. Messaging
log("Alice sending message to Bob...")
r = session_alice.post(f"{BASE_URL}/messages", json={"recipient_username": "bob", "content": "Hello Bob"})
check(r, 200)

log("Bob checking messages...")
r = session_bob.get(f"{BASE_URL}/messages")
check(r, 200)
msgs = r.json()
if any(m['content'] == "Hello Bob" for m in msgs):
    log("Message received.")
else:
    log("Message NOT received!")

log("Verification Complete.")
