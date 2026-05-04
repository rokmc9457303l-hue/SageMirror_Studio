# -*- coding: utf-8 -*-
import sys
import os
import json
import threading
from datetime import datetime

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
except ImportError:
    sys.exit(1)

try:
    import requests
except ImportError:
    requests = None

# --- [마스터 설정] ---
BASE_PATH = r"C:\SageMirror_Production"
VAULT_PATH = os.path.join(BASE_PATH, "00_Obsidian")
RULES_PATH = os.path.join(BASE_PATH, "Master_Rules.json")
OLLAMA_URL = "http://localhost:11434/v1"

C = {
    "bg": "#000000", "panel": "#0A0A0E", "card": "#151520",
    "gold": "#FFD700", "gold2": "#FFC107", "rose": "#E8445A", 
    "text": "#FFFFFF", "muted": "#444455", "teal": "#008080", "blue": "#1E90FF"
}

MASTER_KNOWLEDGE_PROMPT = """# [[Title of Concept/Entity]]

## 📌 Brief Summary
(A concise 1-2 sentence definition of this topic.)

## 📖 Core Content
(Detailed explanation synthesized from raw sources.)

## 🔗 Knowledge Connections
- **Related Topics:** [[Related-Concept-A]], [[Related-Concept-B]]
- **Projects/Contexts:** [[Project-Name]]
- **Contradictions/Notes:** (e.g., "Source X claims this, but Source Y disagrees.")

---
*Last updated: 오늘 날짜*"""

class OracleMasterSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("✦ Tubie Master · 현자의 거울 제작 엔진 v7.7.1")
        self.root.geometry("1450x950")
        self.root.configure(bg=C["bg"])
        self.ep_title = tk.StringVar(value="Ep_001_New_Project")
        self.active_model = "qwen3"
        self.api_url = OLLAMA_URL
        
        self.channels = [
            {"name": "김경일의 지혜", "url": "https://www.youtube.com/@wisdom_kj"},
            {"name": "놀심 (Nolsim)", "url": "https://www.youtube.com/@Nolsim"},
            {"name": "뇌부자들", "url": "https://www.youtube.com/@brainrich"},
            {"name": "Dr. Julie Smith", "url": "https://www.youtube.com/@drjuliesmith"},
            {"name": "HealthyGamerGG", "url": "https://www.youtube.com/@HealthyGamerGG"}
        ]
        
        self.main_container = tk.Frame(self.root, bg=C["bg"])
        self.main_container.pack(fill=tk.BOTH, expand=True)
        self._build_intro()
        threading.Thread(target=self._load_model, daemon=True).start()

    def _load_model(self):
        if requests:
            try:
                resp = requests.get(f"{OLLAMA_URL}/models", timeout=1)
                if resp.status_code == 200:
                    self.api_url = OLLAMA_URL
                    self.active_model = resp.json()["data"][0]["id"]
            except: pass

    def _save_to_obsidian(self, mod, title, content):
        try:
            ep_folder = self.ep_title.get()
            folder = os.path.join(VAULT_PATH, ep_folder)
            if not os.path.exists(folder): os.makedirs(folder, exist_ok=True)
            
            if "## 📌 Brief Summary" in content or "## 📖 Core Content" in content:
                formatted_content = f"{content}\n\n---\n*System Context:* [[{mod}]] / [[{ep_folder}]]\n*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
            else:
                formatted_content = f"""# [[{mod} - {title}]]\n\n## 📌 Brief Summary\n{ep_folder} 프로젝트의 {mod} 파트에서 생성된 핵심 산출물입니다.\n\n## 📖 Core Content\n{content}\n\n## 🔗 Knowledge Connections\n- **Related Topics:** [[{mod}]], [[SageMirror_Pipeline]]\n- **Projects/Contexts:** [[{ep_folder}]]\n- **Contradictions/Notes:** 현자의 거울 자동화 엔진에 의해 백업됨.\n\n---\n*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"""
            fname = f"{datetime.now().strftime('%Y%m%d')}_{mod}_{title.replace(' ', '_')}.md"
            with open(os.path.join(folder, fname), "w", encoding="utf-8") as f: f.write(formatted_content)
            return True
        except: return False

    def _build_intro(self):
        for w in self.main_container.winfo_children(): w.destroy()
        f = tk.Frame(self.main_container, bg=C["bg"])
        f.pack(expand=True)
        tk.Label(f, text="현자의 거울", font=("Malgun Gothic", 65, "bold"), bg=C["bg"], fg=C["gold"]).pack(pady=10)
        tk.Label(f, text="통합 마스터 제작 엔진 v7.7.1", font=("Malgun Gothic", 12), bg=C["bg"], fg=C["muted"]).pack(pady=(0, 40))
        tk.Label(f, text="제작 에피소드 제목 입력", font=("Malgun Gothic", 15), bg=C["bg"], fg=C["text"]).pack(pady=10)
        tk.Entry(f, textvariable=self.ep_title, font=("Malgun Gothic", 20), bg=C["card"], fg=C["text"], justify="center", width=35).pack(pady=20, ipady=12)
        tk.Button(f, text="오라클 관문 열기", font=("Malgun Gothic", 16, "bold"), bg=C["rose"], fg="white", padx=80, pady=22, relief=tk.FLAT, command=self._build_dashboard).pack(pady=30)

    def _build_dashboard(self):
        for w in self.main_container.winfo_children(): w.destroy()
        hdr = tk.Frame(self.main_container, bg=C["panel"], pady=25); hdr.pack(fill=tk.X)
        tk.Label(hdr, text="현자의 거울 제작 대시보드", font=("Malgun Gothic", 32, "bold"), bg=C["panel"], fg=C["gold"]).pack()
        tk.Button(self.main_container, text="⬅ HOME", bg=C["card"], fg="white", command=self._build_intro, relief=tk.FLAT).place(x=30, y=30)
        
        grid = tk.Frame(self.main_container, bg=C["bg"], padx=40, pady=40); grid.pack(fill=tk.BOTH, expand=True)
        mods = [
            ("01 벤치마킹", self.run_benchmarking), ("02 심층 자료조사", self.run_research), 
            ("03 썸네일 기획", self.run_thumbnail_master), ("04 제작기획", self.run_planning), 
            ("05 대본작성", self.run_scripting), ("06 구글플로우 이미지", self.run_generic),
            ("07 오팔 영상조각", self.run_generic), ("08 나레이션", self.run_generic), 
            ("09 음악창고", self.open_folder), ("10 캡컷조립", self.open_capcut_assembler)
        ]
        for i, (name, cmd) in enumerate(mods):
            r, c = divmod(i, 5)
            f = tk.Frame(grid, bg=C["bg"], padx=15, pady=20); f.grid(row=r, column=c, sticky="nsew")
            tk.Button(f, text=name, font=("Malgun Gothic", 11, "bold"), bg=C["card"], fg=C["text"], width=18, height=4, relief=tk.FLAT, command=lambda n=name, c=cmd: c(n)).pack()
        grid.grid_columnconfigure((0,1,2,3,4), weight=1)

    def open_folder(self, name): os.startfile(BASE_PATH)

    def open_capcut_assembler(self, name):
        import subprocess
        script_path = os.path.join(BASE_PATH, "02_CapCut_Automator", "CapCut_Auto_Assembler.py")
        if os.path.exists(script_path):
            try:
                # 콘솔창 없이 백그라운드에서 GUI만 띄우기 (CREATE_NO_WINDOW = 0x08000000)
                subprocess.Popen(["pythonw", script_path], creationflags=0x08000000, cwd=os.path.dirname(script_path))
            except Exception as e:
                messagebox.showerror("실행 에러", f"조립기 실행 실패:\n{e}")
        else:
            messagebox.showerror("에러", "캡컷 조립기 스크립트를 찾을 수 없습니다.")

    def _create_win(self, name, rule_text):
        win = tk.Toplevel(self.root); win.title(f"✦ {name}"); win.geometry("1450x950"); win.configure(bg=C["bg"])
        hdr = tk.Frame(win, bg=C["panel"], pady=15); hdr.pack(fill=tk.X)
        tk.Label(hdr, text=f"{name}", font=("Malgun Gothic", 22, "bold"), bg=C["panel"], fg=C["gold2"]).pack()
        tk.Button(hdr, text="⬅ BACK", bg=C["card"], fg="white", command=win.destroy, relief=tk.FLAT).place(x=20, y=15)
        rf = tk.Frame(win, bg=C["bg"], padx=20, pady=10); rf.pack(fill=tk.X)
        l_r = tk.LabelFrame(rf, text=" 📌 오디시언 지식 구조화 프롬프트 ", bg=C["bg"], fg=C["teal"], font=("Malgun Gothic", 10, "bold"), padx=15, pady=10)
        l_r.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        tk.Label(l_r, text=MASTER_KNOWLEDGE_PROMPT, font=("Consolas", 8), bg=C["bg"], fg="white", justify=tk.LEFT).pack(anchor="w")
        r_r = tk.LabelFrame(rf, text=f" 📡 {name} 수행 규칙서 ", bg=C["bg"], fg=C["rose"], font=("Malgun Gothic", 10, "bold"), padx=15, pady=10)
        r_r.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        rt_box = scrolledtext.ScrolledText(r_r, bg=C["bg"], fg="white", font=("Malgun Gothic", 10), height=10, wrap=tk.WORD, bd=0)
        rt_box.pack(fill=tk.BOTH, expand=True)
        rt_box.insert(tk.END, rule_text)
        rt_box.config(state=tk.DISABLED)
        return win, hdr

    def run_benchmarking(self, name):
        r = """1. 채널 모니터링: 지정된 5개 전문 채널 중 '조회수/시청률 1위' 영상 1개 채택
2. 키워드 분석: SEO 키워드 + 심리 트리거 키워드 추출
3. 기법 분석: 썸네일 카피 전략 및 도입부 5초 후킹 문구 공식화
4. 댓글 마이닝: 실제 경험담 위주의 댓글 100개 정밀 필터링 및 분석
5. 결과 도출: 분석된 화두를 페르소나에 맞춰 다음 연구 파트로 전달"""
        win, hdr = self._create_win("벤치마킹", r)
        # 헤더 라벨 수정 (이미 _create_win 내부에서 처리되지만, 명시적으로 '벤치마킹'으로 표시)
        mf = tk.Frame(win, bg=C["bg"], padx=15, pady=10); mf.pack(fill=tk.BOTH, expand=True)
        
        f1 = tk.LabelFrame(mf, text=" 🎬 5대 전문가 채널 관리 ", bg=C["bg"], fg=C["gold"], font=("Malgun Gothic", 10, "bold"), padx=10, pady=10)
        f1.grid(row=0, column=0, sticky="nsew", padx=5)
        lb = tk.Listbox(f1, bg=C["card"], fg="white", font=("Malgun Gothic", 10), width=35)
        lb.pack(fill=tk.BOTH, expand=True)
        for c in self.channels: 
            lb.insert(tk.END, f"[{c['name']}]")
            lb.insert(tk.END, f"URL: {c['url']}")
            lb.insert(tk.END, "--------------------------------")

        f2 = tk.LabelFrame(mf, text=" 💬 데이터 마이닝 (댓글 100개 이상) ", bg=C["bg"], fg=C["rose"], font=("Malgun Gothic", 10, "bold"), padx=10, pady=10)
        f2.grid(row=0, column=1, sticky="nsew", padx=5)
        t_in = scrolledtext.ScrolledText(f2, bg=C["card"], fg="white", font=("Malgun Gothic", 11), wrap=tk.WORD)
        t_in.pack(fill=tk.BOTH, expand=True)

        f3 = tk.LabelFrame(mf, text=" 🧠 Node 01 전략 분석 보고서 ", bg=C["bg"], fg=C["teal"], font=("Malgun Gothic", 10, "bold"), padx=10, pady=10)
        f3.grid(row=0, column=2, sticky="nsew", padx=5)
        t_out = scrolledtext.ScrolledText(f3, bg=C["card"], fg="white", font=("Malgun Gothic", 11), wrap=tk.WORD)
        t_out.pack(fill=tk.BOTH, expand=True)
        
        mf.grid_columnconfigure((1,2), weight=1); mf.grid_rowconfigure(0, weight=1)
        
        def run():
            data = t_in.get("1.0", tk.END).strip()
            if not data: return
            t_out.delete("1.0", tk.END); t_out.insert(tk.END, "⏳ Node 01 실전 명령서에 따라 정밀 분석 중...")
            if requests:
                sys_msg = f"당신은 유튜브 기획 전문가입니다. 반드시 아래 명령서에 따라 순차적으로 분석하고 구조화 양식을 준수하세요.\n\n{r}\n\n{MASTER_KNOWLEDGE_PROMPT}"
                try:
                    resp = requests.post(f"{self.api_url}/chat/completions", json={"model": self.active_model, "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": data}], "temperature": 0.7}, timeout=150)
                    ans = resp.json()['choices'][0]['message']['content']
                    t_out.delete("1.0", tk.END); t_out.insert(tk.END, ans)
                    self._save_to_obsidian(name, "Node01_Report", ans)
                except: t_out.insert(tk.END, "\n❌ AI 엔진 연결 오류")
        
        tk.Button(win, text="🚀 Node 01 실전 명령 수행 및 아카이빙", bg=C["rose"], fg="white", font=("Malgun Gothic", 13, "bold"), padx=50, pady=12, command=lambda: threading.Thread(target=run).start()).pack(pady=15)

    def run_research(self, name):
        r = """1. 데이터 위계: 옵시디언 DB 및 과거 조사 내용 우선 검색/참조 ➡️ 성경 말씀 조사 
   ➡️ 5대 사상 융합(쇼펜하우어, 빅터 프랭클, 칼 융, 몽테뉴, 다크심리학, 각종 에세이집)
2. 명칭 고정: 인물은 오직 '@주인공(Protagonist)'으로만 명기
3. 서사 구조화: 유튜브 채널 구조 분석 자료를 참조하여 
   ➡️ [기:폭로], [승:해부], [전:전환], [결:치유] 4단계로 구성하여 작성
4. 휴먼 터치: 4070 세대의 심금을 울리는 깊고 부드러운 현자의 어투로 가공
5. 결과물 통합: [주제-원문-통찰-상징물-교차참조] 포함 '지식 마스터 시트' 작성 후 제작기획 파트로 이관"""
        win, hdr = self._create_win("심층 자료조사", r)
        mf = tk.Frame(win, bg=C["bg"], padx=15, pady=10); mf.pack(fill=tk.BOTH, expand=True)
        
        f_top = tk.LabelFrame(mf, text=" [1] 📜 연구 대상 및 벤치마킹 화두 주입 ", bg=C["bg"], fg=C["gold"], font=("Malgun Gothic", 10, "bold"), padx=10, pady=10)
        f_top.pack(fill=tk.X, pady=5)
        t_in = scrolledtext.ScrolledText(f_top, bg=C["card"], fg="white", font=("Malgun Gothic", 11), height=8, wrap=tk.WORD)
        t_in.pack(fill=tk.X)

        f_bot = tk.LabelFrame(mf, text=" [2] 💎 4단계 서사 기반 '지식 마스터 시트' ", bg=C["bg"], fg=C["teal"], font=("Malgun Gothic", 10, "bold"), padx=10, pady=10)
        f_bot.pack(fill=tk.BOTH, expand=True, pady=5)
        t_out = scrolledtext.ScrolledText(f_bot, bg=C["card"], fg="white", font=("Malgun Gothic", 11), wrap=tk.WORD)
        t_out.pack(fill=tk.BOTH, expand=True)
        
        def run():
            data = t_in.get("1.0", tk.END).strip()
            if not data: return
            t_out.delete("1.0", tk.END); t_out.insert(tk.END, "⏳ 성경 위계 기반 4단계 서사 연구 중 (Node 02)...")
            if requests:
                sys_msg = f"당신은 심층 연구가입니다. 다음 실전 명령을 엄수하세요.\n\n{r}\n\n{MASTER_KNOWLEDGE_PROMPT}"
                try:
                    resp = requests.post(f"{self.api_url}/chat/completions", json={"model": self.active_model, "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": data}], "temperature": 0.6}, timeout=200)
                    ans = resp.json()['choices'][0]['message']['content']
                    t_out.delete("1.0", tk.END); t_out.insert(tk.END, ans)
                    self._save_to_obsidian(name, "Knowledge_Master_Sheet", ans)
                except: t_out.insert(tk.END, "\n❌ AI 엔진 연결 오류")
        
        btn = tk.Button(win, text="📥 옵시디언 영구 보존", font=("Malgun Gothic", 12, "bold"), bg=C["gold"], fg=C["bg"], pady=10, command=lambda: self._save_to_obsidian(name, "Knowledge_Master_Sheet", t_in.get("1.0", tk.END)))
        btn.pack(fill=tk.X, padx=15, pady=20)

    def run_thumbnail_master(self, name):
        r = """[현자의 거울 시스템 절대 규칙]
0. 절대 순번 (001~150) 지정 필수.

[Node 03] 썸네일 기획 파트 (최우선 전략)
- 전략 목표: 유튜브 떡상 알고리즘의 핵심인 '주제와 제목의 대칭성(Contrasting/Symmetrical)'을 극대화한다.
- 규칙 1 (대칭성): [주제]가 '우울증'이라면 [제목/썸네일 텍스트]는 '완벽한 평안을 얻는 법'처럼 반대되거나 해답을 제시하는 구조로 기획한다.
- 규칙 2 (시각적 후킹): 어그로가 아닌 철학적 울림이 있는 고품질 이미지 프롬프트를 작성한다.
- 규칙 3: 기획된 썸네일 컨셉을 [04 제작기획] 파트로 넘겨주어, 전체 서사가 썸네일의 약속을 지키도록 만든다.
"""
        win, hdr = self._create_win(name, r)
        mf = tk.Frame(win, bg=C["bg"], padx=15, pady=10); mf.pack(fill=tk.BOTH, expand=True)
        t_out = scrolledtext.ScrolledText(mf, bg=C["card"], fg="white", font=("Malgun Gothic", 11), wrap=tk.WORD)
        t_out.pack(fill=tk.BOTH, expand=True)
        btn = tk.Button(win, text="📥 옵시디언 영구 보존", font=("Malgun Gothic", 12, "bold"), bg=C["gold"], fg=C["bg"], pady=10, command=lambda: self._save_to_obsidian(name, "Thumbnail_Plan", t_out.get("1.0", tk.END)))
        btn.pack(fill=tk.X, padx=15, pady=20)

    def run_planning(self, name):
        r = """[현자의 거울 시스템 절대 규칙]마스터 가이드 v32.0 - 절대 명령서]
당신은 '현자의 거울' 스튜디오의 수석 연출가입니다. 아래의 세밀한 지침을 100% 준수하여 자동화 툴용 기획을 산출하십시오.

1. [대본 파트] 휴먼 터치 서사 기획
- 서사 구조: [기:폭로(결핍/공감)]-[승:해부(내면성찰)]-[전:전환(관점변화)]-[결:치유(절대적 평안)] 4단계.
- 분량 및 호흡: 영혼을 담아 15분 내외의 깊이 있는 대본 작성. 시청자가 생각할 수 있도록 문장 사이 '칸 띄워 쓰기'와 `[1초 쉼]`, `...` 기호를 강제 배치.
- 화법: "당신"이라는 단어를 사용해 4070 세대의 심금을 울리는 따뜻하고 단호한 현자의 어투 사용.

2. [이미지 파트] 구글 플로우(Fluore) 기법 (Nano Banana 7원칙)
- 원칙: 1.상세묘사 2.텍스트최적화 3.고전유화스타일 4.키아로스쿠로조명 5.세계지식 6.비율자연어(맨끝) 7.파라미터(--ar 등) 금지.
- @태그 필수: @주인공(60대 철학자), @거울, @배경(서재), @사물(@지구봉, @촛대, @옛날만년필, @모래시계 등).
- 아바타 묘사: 거울 속에 나타나는 희, 노, 애, 락 감정의 몽롱한(Hazy, Ethereal) 실루엣.

3. [영상 파트] 오팔(Veo 3.1) 기획 (유화풍 실사화)
- 거울 연출: 조각난 파편들이 스르륵 조립되며 완성되는 효과(Fragment assembly effect).
- 촬영 기법: Macro Cinematic Close-up, Floating dust motes(먼지 입자 산란), Slow-motion Dolly-in.
- 씬 조합 규격: 기획안 작성 시 무조건 `[순번] | [대본] | @[영상 JSON 프롬프트]` 형식으로 산출.

4. [배분 및 캡컷 연동]
- 병렬 배분: 주제 깊이에 따라 최대 10개 계정 동시 가동. 계정당 기본 12장면 내외(유동적 증감).
- 최종 산출 포맷 (JSON):
{
  "sequence": "001",
  "narration": "당신은 거울 앞에 서서... [1초 쉼] 진짜 자신을 마주해야 합니다.",
  "video_prompt": "Hyper-realistic oil painting of 60-year-old @Protagonist..., floating dust motes, cinematic lighting, 16:9 wide shot",
  "opal_motion": "Fragment assembly effect of @Mirror, slow-motion, 8 seconds duration"
}"""
        win, hdr = self._create_win("제작기획", r)
        mf = tk.Frame(win, bg=C["bg"], padx=15, pady=10); mf.pack(fill=tk.BOTH, expand=True)
        
        f_top = tk.LabelFrame(mf, text=" [1] 📥 Node 02 지식 마스터 시트 입력 ", bg=C["bg"], fg=C["gold"], font=("Malgun Gothic", 10, "bold"), padx=10, pady=10)
        f_top.pack(fill=tk.X, pady=5)
        t_in = scrolledtext.ScrolledText(f_top, bg=C["card"], fg="white", font=("Malgun Gothic", 11), height=8, wrap=tk.WORD)
        t_in.pack(fill=tk.X)

        f_bot = tk.LabelFrame(mf, text=" [2] 🎬 Node 03 최종 기획안 (캡컷 JSON 연동형) ", bg=C["bg"], fg=C["teal"], font=("Malgun Gothic", 10, "bold"), padx=10, pady=10)
        f_bot.pack(fill=tk.BOTH, expand=True, pady=5)
        t_out = scrolledtext.ScrolledText(f_bot, bg=C["card"], fg="white", font=("Malgun Gothic", 11), wrap=tk.WORD)
        t_out.pack(fill=tk.BOTH, expand=True)
        
        def run():
            data = t_in.get("1.0", tk.END).strip()
            if not data: return
            t_out.delete("1.0", tk.END); t_out.insert(tk.END, "⏳ 통합 기획 마스터 가이드 적용 중 (Node 03)...")
            if requests:
                sys_msg = f"당신은 스튜디오의 수석 연출가입니다. 다음의 '통합 기획 마스터 가이드'를 한 치의 오차 없이 엄수하여 15분 내외의 영상을 기획하세요.\n\n{r}\n\n{MASTER_KNOWLEDGE_PROMPT}"
                try:
                    resp = requests.post(f"{self.api_url}/chat/completions", json={"model": self.active_model, "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": data}], "temperature": 0.5}, timeout=200)
                    ans = resp.json()['choices'][0]['message']['content']
                    t_out.delete("1.0", tk.END); t_out.insert(tk.END, ans)
                    self._save_to_obsidian(name, "Production_Plan", ans)
                except: t_out.insert(tk.END, "\n❌ AI 엔진 연결 오류")
        
        tk.Button(hdr, text="⚙️ 마스터 기획 시작", bg=C["gold"], fg="black", font=("Malgun Gothic", 11, "bold"), padx=20, command=lambda: threading.Thread(target=run).start()).place(x=120, y=13)

    def run_scripting(self, name):
        r = """[현자의 거울 스튜디오 심장부: 통합 프롬프트 생성 명령서]
당신은 스튜디오의 수석 대본가이자 테크니컬 디렉터입니다. 

0. [전역 필수 규칙: 자율적 순번 배분 및 동기화]
- 영상의 길이는 약 15분 내외를 목표로 하되, 주제의 깊이와 감정선에 따라 **당신이 자율적으로 판단하여 씬(Scene)의 총 개수를 늘리거나 줄이십시오.** 영혼을 불어넣어 완벽한 작품을 만드는 것이 최우선입니다.
- 단, 모든 파트(나레이션, 이미지, 영상, 캡컷)의 결과물 앞에는 당신이 정한 `001`, `002` ... 형식의 **[세 자리 순번]**이 정확히 일치하게 매겨져야 캡컷 자동 조립이 가능합니다.

1. [데이터 소싱 및 리서치 의무]
- 기획안(Node 03)과 자료조사(Node 02) 데이터를 최우선 검토하십시오.
- 옵시디언 DB의 핵심 자료(성경구절, 쇼펜하우어, 빅터 프랭클, 칼 융, 몽테뉴, 다크심리학, 각종 에세이집)를 반드시 참조하여 초안을 작성하십시오.
- 작성 후 자체 리서치 기능을 가동하여 철학적/논리적 빈틈을 보완한 완성본을 만드십시오.

2. [출처 표기 강제 (거울 각인용)]
- 허위 사실 유포 방지를 위해, 대본에 사용된 철학적/종교적 인용문의 **[정확한 자료 출처(책 제목, 저자 등)]**를 반드시 명시하십시오. 이 출처는 영상 속 거울에 직접 새겨집니다.

3. [나레이션용 대본]: 4단계 서사 적용, [1초 쉼] 호흡 기호 필수, 4070을 향한 위로의 어투.
4. [이미지 프롬프트]: Nano Banana 7원칙 준수(비율은 맨 끝에), @주인공/@거울/@사물 태그 필수.
5. [영상 JSON 프롬프트]: Veo 3.1 규격. 유화풍 실사화, 조각이 맞춰지는 거울(Fragment assembly).
6. [캡컷 자동배치 JSON]: (출처 필드 포함)
{ "sequence": "001", "video_file": "scene_001.mp4", "audio_file": "voice_001.mp3", "subtitle": "거울을 보십시오.", "source": "쇼펜하우어, 『의지와 표상으로서의 세계』", "duration": "8.0s" }

*중요*: 결과물은 반드시 아래 4개의 정확한 구분자로 나누어 출력하세요.
[나레이션]
...내용...
[이미지]
...내용...
[영상]
...내용...
[캡컷]
...내용..."""
        win, hdr = self._create_win("대본작성", r)
        
        mf = tk.Frame(win, bg=C["bg"], padx=15, pady=10); mf.pack(fill=tk.BOTH, expand=True)
        
        f_top = tk.LabelFrame(mf, text=" 📥 기획안 및 참조 데이터 입력 ", bg=C["bg"], fg=C["gold"], font=("Malgun Gothic", 10, "bold"), padx=10, pady=5)
        f_top.pack(fill=tk.X, pady=5)
        t_in = scrolledtext.ScrolledText(f_top, bg=C["card"], fg="white", font=("Malgun Gothic", 11), height=5, wrap=tk.WORD)
        t_in.pack(fill=tk.X)

        f_bot = tk.Frame(mf, bg=C["bg"])
        f_bot.pack(fill=tk.BOTH, expand=True, pady=5)
        
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background=C["bg"], borderwidth=0)
        style.configure('TNotebook.Tab', background=C["card"], foreground="white", font=("Malgun Gothic", 11, "bold"), padding=[15, 8])
        style.map('TNotebook.Tab', background=[('selected', C["rose"])])

        nb = ttk.Notebook(f_bot)
        nb.pack(fill=tk.BOTH, expand=True)
        
        f1 = ttk.Frame(nb); f2 = ttk.Frame(nb); f3 = ttk.Frame(nb); f4 = ttk.Frame(nb)
        
        def create_tab(parent, title):
            def open_popup():
                pop = tk.Toplevel(win)
                pop.title(f"🔍 {title} 상세 팝업")
                pop.geometry("1100x850")
                pop.configure(bg=C["bg"])
                pop_txt = scrolledtext.ScrolledText(pop, bg=C["card"], fg="white", font=("Malgun Gothic", 13), wrap=tk.WORD)
                pop_txt.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
                pop_txt.insert(tk.END, t.get("1.0", tk.END))
                pop_txt.config(state=tk.DISABLED)

            btn_frame = tk.Frame(parent, bg=C["bg"])
            btn_frame.pack(fill=tk.X)
            tk.Button(btn_frame, text="🔍 팝업창으로 시원하게 크게 보기", bg=C["teal"], fg="white", font=("Malgun Gothic", 10, "bold"), command=open_popup).pack(side=tk.RIGHT, padx=5, pady=5)
            
            t = scrolledtext.ScrolledText(parent, bg=C["card"], fg="white", font=("Malgun Gothic", 11), wrap=tk.WORD)
            t.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            return t

        t_out1 = create_tab(f1, "1. 나레이션용 대본")
        t_out2 = create_tab(f2, "2. 구글 플로우 이미지 프롬프트")
        t_out3 = create_tab(f3, "3. 오팔 영상 프롬프트")
        t_out4 = create_tab(f4, "4. 캡컷 자동배치 JSON")

        nb.add(f1, text="  1. 나레이션용 대본  ")
        nb.add(f2, text="  2. 구글 플로우 이미지 프롬프트  ")
        nb.add(f3, text="  3. 오팔 영상 프롬프트  ")
        nb.add(f4, text="  4. 캡컷 자동배치 JSON  ")
        
        def run():
            data = t_in.get("1.0", tk.END).strip()
            if not data: return
            for t in [t_out1, t_out2, t_out3, t_out4]:
                t.delete("1.0", tk.END); t.insert(tk.END, "⏳ 생성 중...")
                
            if requests:
                sys_msg = f"당신은 스튜디오의 심장인 수석 대본가입니다. 다음 명령서에 따라 반드시 4가지 파트를 명확히 구분하여 답변하세요.\n\n{r}\n\n{MASTER_KNOWLEDGE_PROMPT}"
                try:
                    resp = requests.post(f"{self.api_url}/chat/completions", json={"model": self.active_model, "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": data}], "temperature": 0.6}, timeout=300)
                    ans = resp.json()['choices'][0]['message']['content']
                    
                    p1 = ans.split("[이미지]")
                    narration = p1[0].replace("[나레이션]", "").strip()
                    if len(p1) > 1:
                        p2 = p1[1].split("[영상]")
                        img = p2[0].strip()
                        if len(p2) > 1:
                            p3 = p2[1].split("[캡컷]")
                            vid = p3[0].strip()
                            cap = p3[1].strip() if len(p3) > 1 else ""
                        else: vid = ""; cap = ""
                    else: img = ""; vid = ""; cap = ""

                    t_out1.delete("1.0", tk.END); t_out1.insert(tk.END, narration)
                    t_out2.delete("1.0", tk.END); t_out2.insert(tk.END, img)
                    t_out3.delete("1.0", tk.END); t_out3.insert(tk.END, vid)
                    t_out4.delete("1.0", tk.END); t_out4.insert(tk.END, cap)
                    
                    self._save_to_obsidian(name, "Node04_Scripts", ans)
                except: t_out1.insert(tk.END, "\n❌ AI 엔진 연결 오류")
        
        tk.Button(hdr, text="🚀 스튜디오 심장 가동 (생성 시작)", bg=C["rose"], fg="white", font=("Malgun Gothic", 12, "bold"), padx=25, pady=5, command=lambda: threading.Thread(target=run).start()).place(x=120, y=10)

    def run_generic(self, name):
        win, hdr = self._create_win(name, "수행 규칙서 준비 중..."); mf = tk.Frame(win, bg=C["bg"], padx=20, pady=20); mf.pack(fill=tk.BOTH, expand=True)
        t = scrolledtext.ScrolledText(mf, bg=C["card"], fg="white", font=("Malgun Gothic", 12)); t.pack(fill=tk.BOTH, expand=True)
        tk.Button(win, text="💾 영구 보관 (Obsidian)", bg=C["teal"], fg="white", font=("Malgun Gothic", 12, "bold"), padx=40, pady=10, command=lambda: self._save_to_obsidian(name, "Result", t.get("1.0", tk.END))).pack(pady=15)

if __name__ == "__main__":
    root = tk.Tk(); app = OracleMasterSystem(root); root.mainloop()
