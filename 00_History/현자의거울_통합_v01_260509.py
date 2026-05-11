# -*- coding: utf-8 -*-
"""
현자의 거울 v1.6 (v35.0 Master Manual Applied)
Sage Mirror Studio - Deluxe UI Edition
(AI Integration & Knowledge Structuring Applied)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
from datetime import datetime
import urllib.request
import urllib.parse
import threading

# --- [디자인 설정] ---
C = {
    "bg": "#0A0A0C",
    "panel": "#121217",
    "card": "#1E1E26",
    "accent": "#FFD700",
    "sub_accent": "#00F2FF",
    "text": "#E0E0E0",
    "muted": "#666677",
    "highlight": "#2A2A35"
}

BASE_PATH = r"C:\SageMirror_Production"
VAULT_PATH = os.path.join(BASE_PATH, "00_Obsidian")
CONFIG_FILE = os.path.join(BASE_PATH, "studio_config.json")

class SageMirrorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("현자의 거울 스튜디오 - 총괄 지휘소 (v01)")
        
        try: self.root.state('zoomed')
        except: pass
            
        self.root.configure(bg=C["bg"])
        self.config = self._load_config()
        self._build_main_ui()
        
    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f: return json.load(f)
            except: pass
        return {"channels": ["", "", "", "", ""], "last_ep": "Ep_001"}

    def _save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    def _add_context_menu(self, widget):
        menu = tk.Menu(widget, tearoff=0, bg=C["panel"], fg=C["text"], activebackground=C["accent"], activeforeground=C["bg"])
        menu.add_command(label="복사 (Copy)", command=lambda: widget.event_generate("<<Copy>>"))
        menu.add_command(label="붙여넣기 (Paste)", command=lambda: widget.event_generate("<<Paste>>"))
        menu.add_command(label="잘라내기 (Cut)", command=lambda: widget.event_generate("<<Cut>>"))
        menu.add_separator()
        menu.add_command(label="모두 선택 (Select All)", command=lambda: self._select_all(widget))
        
        widget.bind("<Button-3>", lambda e: menu.post(e.x_root, e.y_root))
        widget.bind("<Double-Button-1>", lambda e: self._open_zoom_window(widget))

    def _select_all(self, widget):
        if isinstance(widget, tk.Text):
            widget.tag_add("sel", "1.0", "end")
        elif isinstance(widget, tk.Entry):
            widget.selection_range(0, tk.END)
        return "break"

    def _open_zoom_window(self, widget):
        zoom_win = tk.Toplevel(self.root)
        zoom_win.title("내용 상세보기 및 편집")
        zoom_win.geometry("900x700")
        zoom_win.configure(bg=C["bg"])
        
        orig_content = widget.get("1.0", tk.END) if isinstance(widget, tk.Text) else widget.get()
        
        header = tk.Frame(zoom_win, bg=C["panel"], pady=10)
        header.pack(fill=tk.X)
        tk.Label(header, text="상세 편집 모드", font=("Malgun Gothic", 12, "bold"), bg=C["panel"], fg=C["accent"]).pack()

        txt_frame = tk.Frame(zoom_win, bg=C["bg"], padx=20, pady=20)
        txt_frame.pack(fill=tk.BOTH, expand=True)
        
        v_scroll = tk.Scrollbar(txt_frame)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        big_txt = tk.Text(txt_frame, bg=C["card"], fg=C["text"], font=("Malgun Gothic", 11), 
                         relief="flat", undo=True, yscrollcommand=v_scroll.set)
        big_txt.pack(fill=tk.BOTH, expand=True)
        v_scroll.config(command=big_txt.yview)
        
        big_txt.insert("1.0", orig_content.strip())
        self._add_context_menu(big_txt)

        def _apply_and_close():
            new_val = big_txt.get("1.0", tk.END).strip()
            if isinstance(widget, tk.Text):
                widget.delete("1.0", tk.END)
                widget.insert("1.0", new_val)
            else:
                widget.delete(0, tk.END)
                widget.insert(0, new_val)
            zoom_win.destroy()

        btn_frame = tk.Frame(zoom_win, bg=C["bg"], pady=15)
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="적용하고 닫기", font=("Malgun Gothic", 10, "bold"), 
                  bg=C["accent"], fg=C["bg"], padx=30, command=_apply_and_close).pack()

    def _build_main_ui(self):
        self.main_container = tk.Frame(self.root, bg=C["bg"])
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        header = tk.Frame(self.main_container, bg=C["bg"], pady=20)
        header.pack(fill=tk.X)
        tk.Label(header, text="현 자 의  거 울", font=("Malgun Gothic", 50, "bold"), bg=C["bg"], fg=C["accent"]).pack()
        
        grid_container = tk.Frame(self.main_container, bg=C["bg"])
        grid_container.pack(expand=True, pady=(0, 40)) 
        
        self.parts = [
            ("총괄기획파트", "📊", "콘텐츠 시나리오 마스터 기획"), ("섬네일파트", "🎨", "시선을 사로잡는 비주얼 기획"),
            ("대본파트", "✍️", "깊이 있는 서사의 완성"), ("이미지파트", "🖼️", "마스터 에셋 기반 번호순 생성"),
            ("영상파트", "🎞️", "오팔 전용 마스터 프롬프트"), ("나레이션파트", "🎙️", "영혼을 담은 TTS 렌더링"),
            ("BGM파트", "🎵", "청각적 분위기와 감성"), ("캡컷파트", "✂️", "완성본 툴 자동 배치")
        ]
        
        for i, (name, icon, desc) in enumerate(self.parts):
            row, col = divmod(i, 4)
            self._create_card(grid_container, name, icon, desc, row, col)

    def _create_card(self, parent, name, icon, desc, row, col):
        card = tk.Frame(parent, bg=C["card"], padx=2, pady=2, cursor="hand2")
        card.grid(row=row, column=col, padx=25, pady=20)
        inner = tk.Frame(card, bg=C["card"], width=280, height=220, padx=20, pady=30)
        inner.pack_propagate(False)
        inner.pack()
        
        lbl_icon = tk.Label(inner, text=icon, font=("Segoe UI Emoji", 38), bg=C["card"], fg=C["sub_accent"])
        lbl_icon.pack(pady=(0, 10))
        lbl_name = tk.Label(inner, text=name, font=("Malgun Gothic", 17, "bold"), bg=C["card"], fg=C["accent"])
        lbl_name.pack()
        lbl_desc = tk.Label(inner, text=desc, font=("Malgun Gothic", 9), bg=C["card"], fg=C["muted"], pady=15)
        lbl_desc.pack()

        for widget in [card, inner, lbl_icon, lbl_name, lbl_desc]:
            widget.bind("<Button-1>", lambda e, n=name: self._open_part_window(n))

    def _open_part_window(self, name):
        new_win = tk.Toplevel(self.root)
        new_win.title(f"현자의 거울 - {name}")
        new_win.geometry("1400x900")
        new_win.configure(bg=C["bg"])
        
        win_header = tk.Frame(new_win, bg=C["panel"], height=60)
        win_header.pack(fill=tk.X)
        tk.Label(win_header, text=f"◀ {name}", font=("Malgun Gothic", 18, "bold"), bg=C["panel"], fg=C["accent"]).pack(side=tk.LEFT, padx=20)
        
        canvas = tk.Canvas(new_win, bg=C["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(new_win, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=C["bg"])

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=1380)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        if name == "총괄기획파트":
            self._build_research_module(scrollable_frame)
        else:
            tk.Label(scrollable_frame, text=f"[{name}] 모듈 준비 중...", font=("Malgun Gothic", 14), bg=C["bg"], fg=C["muted"]).pack(pady=100)

    def _build_research_module(self, parent):
        top_frame = tk.Frame(parent, bg=C["bg"], padx=30, pady=20)
        top_frame.pack(fill=tk.X)
        
        f1 = tk.LabelFrame(top_frame, text="[좌] 옵시디언 헌법 (절대 준수)", bg=C["bg"], fg=C["accent"], font=("Malgun Gothic", 10, "bold"), padx=10, pady=10)
        f1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        t1 = tk.Text(f1, bg=C["card"], fg=C["text"], height=10, relief="flat", font=("Consolas", 10))
        t1.pack(fill=tk.BOTH)
        obsidian_rule = """[System Rule: 지식 구조화 헌법]
모든 데이터는 아래 형식을 준수하여 출력하라.
# [[001_Title]]
## 📌 Brief Summary: [핵심 요약]
## 📖 Core Content: [상세 내용]
## 🔗 Knowledge Connections: #현자의거울"""
        t1.insert("1.0", obsidian_rule)
        self._add_context_menu(t1)

        f2 = tk.LabelFrame(top_frame, text="[우] 지식 전략 및 페르소나 제어", bg=C["bg"], fg=C["accent"], font=("Malgun Gothic", 10, "bold"), padx=10, pady=10)
        f2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        t2 = tk.Text(f2, bg=C["card"], fg=C["text"], height=10, relief="flat", font=("Consolas", 10))
        t2.pack(fill=tk.BOTH)
        persona_rule = """[System Rule: 서사 융합 및 페르소나]
1. 성경을 절대적 기둥으로 세우고 거장들의 사상을 융합할 것.
2. 모든 인칭은 '@주인공' 또는 '현자'로 통일 (Ethan 등 금지).
3. 5060 세대를 위한 깊은 '휴먼 터치' 문체 강제."""
        t2.insert("1.0", persona_rule)
        self._add_context_menu(t2)

        mid_frame = tk.LabelFrame(parent, text="[타겟 조준] 유튜브 벤치마킹 채널 URL", bg=C["bg"], fg=C["sub_accent"], font=("Malgun Gothic", 10, "bold"), padx=40, pady=15)
        mid_frame.pack(fill=tk.X, padx=30)
        self.channel_entries = []
        for i in range(5):
            f = tk.Frame(mid_frame, bg=C["bg"])
            f.pack(fill=tk.X, pady=2)
            tk.Label(f, text=f"{i+1}.", bg=C["bg"], fg=C["text"]).pack(side=tk.LEFT)
            ent = tk.Entry(f, bg=C["card"], fg=C["accent"], relief="flat", insertbackground="white", font=("Arial", 10))
            ent.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            ent.insert(0, self.config["channels"][i])
            ent.bind("<KeyRelease>", lambda e: self._update_channels())
            self._add_context_menu(ent)
            self.channel_entries.append(ent)

        bot_frame = tk.Frame(parent, bg=C["bg"], padx=30, pady=20)
        bot_frame.pack(fill=tk.BOTH, expand=True)
        
        self.outputs = {}
        defaults = {
            "1. 유튜브 분석 (아이템 발굴)": "[Mission: 시장 조사]\n타겟 영상 URL 및 댓글 분석 결과 보고.",
            "2. 심층 자료조사 (지식 융합)": "[Mission: 지식 부여]\n성경 말씀을 뼈대로 사상 융합 초안 작성.",
            "3. 영상 총괄 기획 (시나리오)": "[Mission: 절대 기준 작성]\n전 부서 참고용 총괄 시나리오 작성."
        }

        for col, default_text in defaults.items():
            f = tk.LabelFrame(bot_frame, text=col, bg=C["bg"], fg=C["accent"], font=("Malgun Gothic", 10, "bold"), padx=10, pady=10)
            f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            t = tk.Text(f, bg=C["card"], fg=C["text"], relief="flat", font=("Malgun Gothic", 10), height=25)
            t.pack(fill=tk.BOTH, expand=True)
            t.insert("1.0", default_text) 
            self.outputs[col] = t
            self._add_context_menu(t)
            
            btn_frame = tk.Frame(f, bg=C["bg"])
            btn_frame.pack(fill=tk.X, pady=(10, 0))

            ai_btn = tk.Button(btn_frame, text="✨ AI 초안 생성", bg=C["sub_accent"], fg=C["bg"], 
                               font=("Malgun Gothic", 9, "bold"), relief="flat", pady=8,
                               command=lambda c=col: self._run_ai_generation(c))
            ai_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

            btn_text = "💾 시나리오 확정" if "3." in col else "💾 결과 저장"
            save_btn = tk.Button(btn_frame, text=btn_text, bg=C["highlight"], fg=C["accent"], 
                                 relief="flat", pady=8,
                                 command=lambda c=col: self._execute_and_save(c))
            save_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _update_channels(self):
        self.config["channels"] = [e.get() for e in self.channel_entries]
        self._save_config()

    def _run_ai_generation(self, mode):
        raw_prompt = self.outputs[mode].get("1.0", tk.END).strip()
        if not raw_prompt:
            messagebox.showwarning("경고", "프롬프트를 입력해주세요.")
            return

        prompt = f"""[System: 지식 구조화 규정 준수]
반드시 다음 구조로만 출력하라:
# [[주제]]
## 📌 Brief Summary
(요약)
## 📖 Core Content
(상세)
## 🔗 Knowledge Connections
- 관련 지식 연결...
--------------------------------------------------
사용자 지령: {raw_prompt}"""

        self.outputs[mode].delete("1.0", tk.END)
        self.outputs[mode].insert("1.0", "⏳ 현자가 생각에 잠겼습니다... 잠시만 기다려주세요...\n")
        
        def _thread_target():
            try:
                url = "http://localhost:5000/api/generate"
                data = json.dumps({"prompt": prompt}).encode('utf-8')
                req = urllib.request.Request(url, data=data, method='POST')
                req.add_header('Content-Type', 'application/json')
                
                with urllib.request.urlopen(req, timeout=120) as response:
                    res = json.loads(response.read().decode('utf-8'))
                    if res.get("status") == "success":
                        result = res.get("response")
                        self.root.after(0, lambda: self._update_ui_with_ai(mode, result))
                    else:
                        error_msg = res.get("message", "알 수 없는 오류")
                        self.root.after(0, lambda: messagebox.showerror("AI 연결 실패", f"오류: {error_msg}"))
                        self.root.after(0, lambda: self._update_ui_with_ai(mode, raw_prompt))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("연결 오류", f"브리지 서버가 실행 중인지 확인하세요.\n{str(e)}"))
                self.root.after(0, lambda: self._update_ui_with_ai(mode, raw_prompt))

        threading.Thread(target=_thread_target, daemon=True).start()

    def _update_ui_with_ai(self, mode, content):
        self.outputs[mode].delete("1.0", tk.END)
        self.outputs[mode].insert("1.0", content)

    def _execute_and_save(self, mode):
        content = self.outputs[mode].get("1.0", tk.END).strip()
        if not content: return
        today = datetime.now().strftime("%Y-%m-%d")
        title = f"{self.config['last_ep']}_{mode.split(' ')[1]}"
        
        # [서버 API를 통한 지식 구조화 저장 권장]
        try:
            url = "http://localhost:5000/api/save"
            data = json.dumps({"filename": title, "content": content, "topic": self.config['last_ep']}).encode('utf-8')
            req = urllib.request.Request(url, data=data, method='POST')
            req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req, timeout=10) as res:
                messagebox.showinfo("저장 완료", "브리지 서버를 통해 지식 구조화 템플릿으로 저장되었습니다.")
        except:
            # 로컬 직접 저장 (폴백)
            folder = os.path.join(VAULT_PATH, self.config["last_ep"])
            if not os.path.exists(folder): os.makedirs(folder, exist_ok=True)
            filename = f"{mode.split(' ')[0]}_{datetime.now().strftime('%H%M%S')}.md"
            with open(os.path.join(folder, filename), "w", encoding="utf-8") as f: f.write(content)
            messagebox.showinfo("저장 완료", "로컬 폴더에 일반 마크다운으로 저장되었습니다.")

if __name__ == "__main__":
    for p in [BASE_PATH, VAULT_PATH]:
        if not os.path.exists(p): os.makedirs(p, exist_ok=True)
    root = tk.Tk()
    app = SageMirrorApp(root)
    root.mainloop()
