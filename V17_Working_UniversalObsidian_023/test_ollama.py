import time
import requests
import json

url = "http://localhost:11434/api/generate"
payload = {
    "model": "gemma4:e2b",
    "prompt": "안녕. 한 문장으로 답해줘.",
    "stream": False,
    "keep_alive": "10m",
    "options": {
        "num_predict": 64
    }
}

print("First Call...")
start = time.time()
try:
    resp = requests.post(url, json=payload, timeout=180)
    resp.raise_for_status()
    print("Response 1:", resp.json().get("response", "").strip())
except Exception as e:
    print("Error 1:", str(e))
print(f"First Call Time: {time.time() - start:.2f} seconds\n")

print("Second Call...")
start = time.time()
try:
    resp = requests.post(url, json=payload, timeout=180)
    resp.raise_for_status()
    print("Response 2:", resp.json().get("response", "").strip())
except Exception as e:
    print("Error 2:", str(e))
print(f"Second Call Time: {time.time() - start:.2f} seconds")
