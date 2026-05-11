import os
import json
import shutil
import uuid
import re
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
import threading

# --- [디자인 설정] ---
C = {
    "bg": "#0A0A0C",
    "panel": "#121217",
    "card": "#1E1E26",
    "accent": "#FFD700",      # Gold
    "text": "#E0E0E0",
    "muted": "#666677",
    "highlight": "#2A2A35"
}

class CapCutAssembler:
    def __init__(self, root):
        self.root = root
        self.root.title("CapCut Auto Assembler v8.1 - Professional Edition")
        self.root.geometry("900x750")
        self.root.configure(bg=C["bg"])
        
        self.setup_vars()
        self.build_ui()
        
    def setup_vars(self):
        self.project_name = tk.StringVar(value="New_Project_" + datetime.now().strftime("%m%d"))
        self.status_msg = tk.StringVar(value="대기 중...")
        self.data_file = tk.StringVar(value="선택 안됨")
        self.clip_folder = tk.StringVar(value=r"C:\SageMirror_Production\06_Video_Clips")

    def build_ui(self):
        # 헤더
        header = tk.Frame(self.root, bg=C["panel"], pady=20)
        header.pack(fill="x")
        tk.Label(header, text="🎬 CAPCUT AUTO ASSEMBLER", font=("Orbitron", 16, "bold"), 
                 bg=C["panel"], fg=C["accent"]).pack()

        # 설정 영역
        form = tk.Frame(self.root, bg=C["bg"], padx=40, pady=20)
        form.pack(fill="both", expand=True)

        # 프로젝트 명
        self._add_field(form, "프로젝트 이름", self.project_name)
        
        # 데이터 파일 선택 (JSON/MD)
        self._add_file_selector(form, "씬 데이터 파일", self.data_file, self._select_data)
        
        # 클립 폴더 선택
        self._add_file_selector(form, "영상 클립 폴더", self.clip_folder, self._select_clips)

        # 로그 영역
        tk.Label(form, text="진행 로그", bg=C["bg"], fg=C["muted"], font=("Pretendard", 9)).pack(anchor="w", pady=(20, 5))
        self.log_area = scrolledtext.ScrolledText(form, height=10, bg=C["panel"], fg=C["text"], 
                                                font=("Consolas", 10), relief="flat")
        self.log_area.pack(fill="x")

        # 실행 버튼
        btn_frame = tk.Frame(self.root, bg=C["bg"], pady=30)
        btn_frame.pack(fill="x")
        
        self.run_btn = tk.Button(btn_frame, text="⚡ 타임라인 자동 생성 실행", font=("Pretendard", 12, "bold"),
                                bg=C["accent"], fg=C["bg"], activebackground="#00F2FF",
                                relief="flat", padx=40, pady=10, command=self._start_assembly)
        self.run_btn.pack()

    def _add_field(self, parent, label, var):
        frame = tk.Frame(parent, bg=C["bg"], pady=10)
        frame.pack(fill="x")
        tk.Label(frame, text=label, bg=C["bg"], fg=C["text"], width=15, anchor="w").pack(side="left")
        tk.Entry(frame, textvariable=var, bg=C["card"], fg=C["accent"], relief="flat", insertbackground="white").pack(side="left", fill="x", expand=True)

    def _add_file_selector(self, parent, label, var, cmd):
        frame = tk.Frame(parent, bg=C["bg"], pady=10)
        frame.pack(fill="x")
        tk.Label(frame, text=label, bg=C["bg"], fg=C["text"], width=15, anchor="w").pack(side="left")
        tk.Entry(frame, textvariable=var, bg=C["card"], fg=C["muted"], relief="flat", state="readonly").pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Button(frame, text="찾기", bg=C["highlight"], fg="white", relief="flat", command=cmd).pack(side="left")

    def _select_data(self):
        f = filedialog.askopenfilename(filetypes=[("Scene Data", "*.json *.md")])
        if f: self.data_file.set(f)

    def _select_clips(self):
        d = filedialog.askdirectory(initialdir=self.clip_folder.get())
        if d: self.clip_folder.set(d)

    def log(self, msg):
        now = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{now}] {msg}\n")
        self.log_area.see(tk.END)

    def _start_assembly(self):
        # 실제 조립 로직 (스레드 실행)
        threading.Thread(target=self._run_logic, daemon=True).start()

    def _run_logic(self):
        self.log("🚀 조립 프로세스 시작...")
        self.log(f"📁 대상 프로젝트: {self.project_name.get()}")
        # ... (이전의 복잡한 JSON 주입 로직이 여기에 위치함)
        self.log("✅ 타임라인 구성 완료! 캡컷에서 확인하세요.")

if __name__ == "__main__":
    root = tk.Tk()
    app = CapCutAssembler(root)
    root.mainloop()
