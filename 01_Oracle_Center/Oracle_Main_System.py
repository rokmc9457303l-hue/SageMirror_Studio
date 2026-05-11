# -*- coding: utf-8 -*-
"""
=======================================================
  현자의 거울 (Sage Mirror Studio) - Oracle Main System
  Version: 10.6.0 Stable (Restored)
  Description: 8대 생산 모듈 통합 관리 및 지식 자산화 엔진
=======================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import json
import threading
import subprocess
from datetime import datetime

# --- [환경 설정] ---
BASE_PATH = r"C:\SageMirror_Production"
VAULT_PATH = os.path.join(BASE_PATH, "00_Obsidian")
CONFIG_FILE = os.path.join(BASE_PATH, "studio_config.json")

# 디자인 테마 (Obsidian Black & Gold)
C = {
    "bg": "#0A0A0C",
    "panel": "#121217",
    "card": "#1E1E26",
    "accent": "#FFD700",      # Gold
    "sub_accent": "#00F2FF",  # Cyan
    "text": "#E0E0E0",
    "muted": "#666677",
    "highlight": "#2A2A35",
    "success": "#4CAF50",
    "error": "#F44336"
}

class OracleMainSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("현자의 거울 - Oracle Main System v10.6.0")
        
        # 화면 최적화
        try: self.root.state('zoomed')
        except: self.root.geometry("1400x900")
            
        self.root.configure(bg=C["bg"])
        self.config = self._load_config()
        self._setup_styles()
        self._build_ui()
        
    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return {"last_episode": "Ep_001", "author": "Master"}

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Oracle.TFrame", background=C["bg"])
        style.configure("Panel.TFrame", background=C["panel"])
        style.configure("Card.TFrame", background=C["card"], relief="flat")
        
        # 버튼 스타일
        style.configure("Gold.TButton", foreground=C["bg"], background=C["accent"], font=("Pretendard", 10, "bold"))
        style.map("Gold.TButton", background=[('active', C["sub_accent"])])

    def _build_ui(self):
        # [상단 헤더]
        header = tk.Frame(self.root, bg=C["panel"], height=60)
        header.pack(fill="x", side="top")
        
        tk.Label(header, text="SAGE MIRROR STUDIO", font=("Orbitron", 18, "bold"), 
                 bg=C["panel"], fg=C["accent"]).pack(side="left", padx=30, pady=15)
        
        status_frame = tk.Frame(header, bg=C["panel"])
        status_frame.pack(side="right", padx=30)
        
        self.status_label = tk.Label(status_frame, text="● SYSTEM ONLINE", font=("Pretendard", 9, "bold"),
                                    bg=C["panel"], fg=C["success"])
        self.status_label.pack()

        # [메인 본체 - 8대 모듈 그리드]
        self.main_container = tk.Frame(self.root, bg=C["bg"])
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        modules = [
            ("01_자료조사", "Research & Wisdom", self._open_research),
            ("02_총괄기획", "Production Plan", self._open_planning),
            ("03_대본집필", "Script Writing", self._open_scripting),
            ("04_이미지생성", "Visual Engine", self._open_visuals),
            ("05_영상클립", "Video Clips", self._open_video),
            ("06_나레이션", "Narration AI", self._open_narration),
            ("07_배경음악", "BGM & Sound", self._open_bgm),
            ("08_캡컷조립", "Final Assembly", self._open_capcut)
        ]
        
        for i, (name, subtitle, cmd) in enumerate(modules):
            row, col = divmod(i, 4)
            self._create_module_card(self.main_container, name, subtitle, cmd, row, col)

    def _create_module_card(self, parent, title, sub, cmd, row, col):
        card = tk.Frame(parent, bg=C["card"], highlightthickness=1, highlightbackground=C["highlight"])
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        parent.grid_columnconfigure(col, weight=1)
        parent.grid_rowconfigure(row, weight=1)
        
        # 카드 호버 효과
        card.bind("<Enter>", lambda e: card.config(highlightbackground=C["accent"]))
        card.bind("<Leave>", lambda e: card.config(highlightbackground=C["highlight"]))
        
        tk.Label(card, text=title, font=("Pretendard", 14, "bold"), bg=C["card"], fg=C["accent"]).pack(pady=(20, 5))
        tk.Label(card, text=sub, font=("Pretendard", 9), bg=C["card"], fg=C["muted"]).pack(pady=(0, 20))
        
        btn = tk.Button(card, text="실행하기", font=("Pretendard", 10, "bold"),
                        bg=C["accent"], fg=C["bg"], activebackground=C["sub_accent"],
                        relief="flat", cursor="hand2", command=cmd)
        btn.pack(pady=(0, 20), padx=30, fill="x")

    # --- [모듈별 실행 함수] ---
    def _open_research(self): self._popup_module("자료조사 파트", "AI Research Agent가 작동 중입니다...")
    def _open_planning(self): self._popup_module("총괄기획 파트", "에피소드 기획 및 프롬프트 최적화 중...")
    def _open_scripting(self): self._popup_module("대본집필 파트", "Qwen-3 엔진이 대본을 작성합니다.")
    def _open_visuals(self): self._popup_module("이미지 파트", "Stable Diffusion / Midjourney 연동 중...")
    def _open_video(self): self._popup_module("영상클립 파트", "AI Video Generation 도구 실행 중...")
    def _open_narration(self): self._popup_module("나레이션 파트", "CosyVoice Colab 서버 연동 중...")
    def _open_bgm(self): self._popup_module("배경음악 파트", "ACE-Step 배경음악 생성 엔진 연동...")
    def _open_capcut(self): self._popup_module("캡컷조립 파트", "CapCut Auto Assembler v8.1 실행 중...")

    def _popup_module(self, title, content):
        pop = tk.Toplevel(self.root)
        pop.title(title)
        pop.geometry("800x600")
        pop.configure(bg=C["bg"])
        
        tk.Label(pop, text=title, font=("Pretendard", 16, "bold"), bg=C["bg"], fg=C["accent"]).pack(pady=20)
        
        txt = scrolledtext.ScrolledText(pop, bg=C["panel"], fg=C["text"], insertbackground=C["text"], 
                                      font=("Consolas", 11), relief="flat")
        txt.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        txt.insert("1.0", f"--- {title} 시스템 로그 ---\n\n{content}\n\n[알림] 실제 자동화 로직은 각 모듈별 독립 스크립트와 연동됩니다.")
        
        # 우클릭 메뉴 추가
        self._add_context_menu(txt)

    def _add_context_menu(self, widget):
        menu = tk.Menu(widget, tearoff=0, bg=C["panel"], fg=C["text"])
        menu.add_command(label="복사", command=lambda: widget.event_generate("<<Copy>>"))
        menu.add_command(label="붙여넣기", command=lambda: widget.event_generate("<<Paste>>"))
        widget.bind("<Button-3>", lambda e: menu.post(e.x_root, e.y_root))

if __name__ == "__main__":
    root = tk.Tk()
    app = OracleMainSystem(root)
    root.mainloop()
