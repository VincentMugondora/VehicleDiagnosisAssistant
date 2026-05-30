import subprocess
import time
import requests

def main():
    # Start the server
    process = subprocess.Popen(["uvicorn", "app.main:app", "--port", "8005", "--log-level", "debug"], 
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    time.sleep(3) # Wait for startup
    
    # Send request
    try:
        response = requests.post(
            "http://127.0.0.1:8005/webhook/baileys",
            json={"from":"test:+1234567890","text":"P0420","message_id":"test12345"}
        )
        print("Status:", response.status_code)
        print("Response:", response.text)
    except Exception as e:
        print("Error:", e)
        
    process.terminate()
    try:
        outs, errs = process.communicate(timeout=5)
        print("--- SERVER LOGS ---")
        print(outs)
    except:
        process.kill()

if __name__ == "__main__":
    main()
