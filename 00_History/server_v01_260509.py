# [Backup] server.py v01 260509
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
import subprocess

app = Flask(__name__)
CORS(app)

BASE_PATH = r"C:\SageMirror_Production"
OBSIDIAN_PATH = os.path.join(BASE_PATH, "00_Obsidian")
os.makedirs(OBSIDIAN_PATH, exist_ok=True)

@app.route('/api/save', methods=['POST'])
def save_to_obsidian():
    data = request.json
    content = data.get('content', '')
    original_filename = data.get('filename', '현자의거울_기록')
    topic = data.get('topic', '미분류_프로젝트')
    today = datetime.now().strftime("%Y-%m-%d")
    structured_content = f"""# [[{original_filename}]]

## 📌 Brief Summary
(AI가 요약한 핵심 정의)

## 📖 Core Content
{content}

## 🔗 Knowledge Connections
- **Related Topics:** [[에피소드_분석]], [[현자의_통찰]]
- **Projects/Contexts:** [[{topic}]]
- **Contradictions/Notes:** (특이사항 및 보완점 기록)

---
*Last updated: {today}*
"""
    filename = f"{original_filename}_{datetime.now().strftime('%H%M%S')}.md"
    full_path = os.path.join(OBSIDIAN_PATH, filename)
    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(structured_content)
        return jsonify({"status": "success", "path": full_path})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/run', methods=['POST'])
def run_module():
    module = request.json.get('module')
    if module == "capcut":
        path = os.path.join(BASE_PATH, "02_CapCut_Automator", "CapCut_Auto_Assembler.py")
    elif module == "oracle":
        path = os.path.join(BASE_PATH, "01_Oracle_Center", "Oracle_Main_System.py")
    elif module == "ping":
        return jsonify({"status": "success", "message": "pong"})
    else:
        return jsonify({"status": "error", "message": "Unknown module"}), 400
    try:
        subprocess.Popen(["pythonw", path])
        return jsonify({"status": "success", "message": f"{module} run"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate_ai():
    import json
    import urllib.request
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
    app.run(port=5000)
