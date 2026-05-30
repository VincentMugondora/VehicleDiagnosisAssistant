import threading
import time
import httpx
import uvicorn
from app.main import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8003, log_level="debug")

if __name__ == "__main__":
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    time.sleep(2)  # Wait for server to start
    
    body = {"from":"test:+1234567890","text":"P0420","message_id":"test123"}
    try:
        response = httpx.post("http://127.0.0.1:8003/webhook/baileys", json=body)
        print("Status Code:", response.status_code)
        print("Response Body:", response.text)
    except Exception as e:
        print("Client Error:", e)
    
    time.sleep(1)
