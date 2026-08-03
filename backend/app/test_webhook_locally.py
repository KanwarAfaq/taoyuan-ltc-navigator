"""
test_webhook_locally.py — simulates a real LINE webhook call against your
locally running server, with a correctly computed X-Line-Signature.

Usage: make sure `python -m uvicorn main:app --reload --app-dir .` is
running in another terminal first, then:

    python test_webhook_locally.py
"""
import hmac
import hashlib
import base64
import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
if not CHANNEL_SECRET:
    print("LINE_CHANNEL_SECRET not found in .env -- set it first.")
    raise SystemExit(1)

LOCAL_URL = "http://127.0.0.1:8000/line/webhook"

# Simulates a user sending your bot a text message (any text triggers the
# wizard to start, per how process_follow_or_text() works)
body = json.dumps({
    "destination": "xxx",
    "events": [{
        "type": "message",
        "webhookEventId": "test-event-id",
        "deliveryContext": {"isRedelivery": False},
        "message": {"id": "test-msg-id", "type": "text", "text": "開始", "quoteToken": "fake-quote-token"},
        "replyToken": "00000000000000000000000000000000",  # dummy -- reply will fail, that's expected and handled
        "source": {"type": "user", "userId": "U_LOCAL_TEST_USER"},
        "timestamp": 1234567890,
        "mode": "active",
    }]
})

signature = base64.b64encode(
    hmac.new(CHANNEL_SECRET.encode(), body.encode(), hashlib.sha256).digest()
).decode()

resp = requests.post(
    LOCAL_URL,
    data=body,
    headers={"X-Line-Signature": signature, "Content-Type": "application/json"},
)

print(f"Status: {resp.status_code}")
print(f"Body: {resp.text}")
print()
if resp.status_code == 200:
    print("✅ Signature accepted and webhook processed successfully.")
    print("   (The reply itself will fail since the reply token is fake --")
    print("   check your server's terminal for a logged error about that,")
    print("   which is expected and handled gracefully.)")
else:
    print("❌ Something's wrong -- check the server terminal for a traceback.")
