from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from datetime import datetime
import json
import urllib.request

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=CURRENT_DIR, static_url_path='')
CORS(app)

# [v19 마스터 저장소]
VAULT_ROOT = r"C:\SageMirror_Vault"
os.makedirs(VAULT_ROOT, exist_ok=True)

print(f"--- SAGE MIRROR MASTER ENGINE v19.0 (RESTORED) ---")
print(f"--- VAULT: {VAULT_ROOT} ---")

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/stats', methods=['GET'])
def get_stats():
    cpu, ram = 0, 0
    try:
        import psutil
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
    except: pass
    return jsonify({"cpu": cpu, "ram": ram})

@app.route('/api/save', methods=['POST'])
def save_to_vault():
    data = request.json
    content = data.get('content', '')
    filename = data.get('filename', 'MASTER')
    topic = data.get('topic', 'General').upper()
    
    topic_path = os.path.join(VAULT_ROOT, topic)
    os.makedirs(topic_path, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{filename}_{timestamp}"
    
    report_filename = f"{base_name}_REPORT.md"
    memo_filename = f"{base_name}_MEMO.md"
    
    report_path = os.path.join(topic_path, report_filename)
    memo_path = os.path.join(topic_path, memo_filename)
    
    # 상호 연결 링크 생성
    report_content = f"> [!TIP] 관련 메모: [[{memo_filename}|상세 메모 보기]]\n\n" + content
    memo_content = f"""# 📝 작업 메모: {filename}
> [!NOTE] 관련 리포트: [[{report_filename}|메인 리포트 보기]]
> 생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 💡 아이디어 스케치
(여기에 자유롭게 아이디어를 기록하세요.)

## 🧠 젬마의 추가 통찰
(분석 과정에서 나온 젬마의 키워드와 피드백을 여기에 보강하세요.)

---
#MEMO #{topic}
"""
    try:
        with open(report_path, 'w', encoding='utf-8') as f: f.write(report_content)
        with open(memo_path, 'w', encoding='utf-8') as f: f.write(memo_content)
        return jsonify({"status": "success", "report": report_filename, "path": topic})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate_ai():
    data = request.json
    prompt = data.get('prompt')
    model = data.get('model', 'gemma4:e4b')
    try:
        req = urllib.request.Request("http://localhost:11434/api/generate")
        req.add_header('Content-Type', 'application/json')
        jsondata = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode('utf-8')
        with urllib.request.urlopen(req, jsondata, timeout=120) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return jsonify({"status": "success", "response": res_data.get('response')})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=False)
