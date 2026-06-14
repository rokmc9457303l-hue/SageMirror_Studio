import requests
import json
import time
from pathlib import Path

report = []

def log(msg):
    print(msg)
    report.append(msg)

log("=== E4B 직접 호출 테스트 ===")
log(f"시작: {time.strftime('%H:%M:%S')}")

url = "http://localhost:11434/api/generate"
body = {
    "model": "gemma4:e4b",
    "prompt": "안녕. 지금 정상 작동 중인지 한 문장으로 대답해줘.",
    "stream": False,
    "keep_alive": "10m",
    "options": {
        "num_predict": 64
    }
}

log("\n--- 첫 번째 호출 시작 ---")
t0 = time.time()
try:
    resp = requests.post(url, json=body, timeout=(15, 360))
    elapsed1 = time.time() - t0
    resp.raise_for_status()
    data = resp.json()
    response_text = data.get("response", "(응답 없음)").strip()
    log(f"FIRST_RESPONSE: {response_text}")
    log(f"FIRST_SECONDS: {elapsed1:.1f}초")
    first_ok = True
except requests.exceptions.Timeout:
    elapsed1 = time.time() - t0
    log(f"FIRST_ERROR: Timeout ({elapsed1:.1f}초 후)")
    first_ok = False
except requests.exceptions.ConnectionError as e:
    elapsed1 = time.time() - t0
    log(f"FIRST_ERROR: ConnectionError — {e}")
    first_ok = False
except Exception as e:
    elapsed1 = time.time() - t0
    log(f"FIRST_ERROR: {type(e).__name__} — {e}")
    first_ok = False

if first_ok:
    log("\n--- 두 번째 호출 시작 ---")
    t1 = time.time()
    try:
        resp2 = requests.post(url, json=body, timeout=(5, 120))
        elapsed2 = time.time() - t1
        resp2.raise_for_status()
        data2 = resp2.json()
        response_text2 = data2.get("response", "(응답 없음)").strip()
        log(f"SECOND_RESPONSE: {response_text2}")
        log(f"SECOND_SECONDS: {elapsed2:.1f}초")
    except Exception as e:
        elapsed2 = time.time() - t1
        log(f"SECOND_ERROR: {type(e).__name__} — {e}")
else:
    log("첫 번째 실패로 두 번째 호출 생략")

log(f"\n완료: {time.strftime('%H:%M:%S')}")

# 결과 파일 저장
Path(r"C:\SageMirror_Production\e4b_direct_test_result.txt").write_text(
    "\n".join(report), encoding="utf-8"
)
print("결과 저장 완료.")
