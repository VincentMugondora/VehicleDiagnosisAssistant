import urllib.request
import json

req = urllib.request.Request(
    'http://localhost:8000/webhook/baileys',
    data=b'{"from":"test:+1234567890","text":"P0420","message_id":"test123"}',
    headers={'Content-Type': 'application/json'},
    method='POST'
)
try:
    with urllib.request.urlopen(req) as f:
        print("Status:", f.status)
        print(f.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print("HTTPError:", e.code)
    print(e.read().decode('utf-8'))
except Exception as e:
    print("Other error:", e)
