import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
import shutil
import sys

print("[DEBUG] Importing modules successful.")

class CapCutAssembler:
    def __init__(self, root):
        print("[DEBUG] Initializing GUI...")
        self.root = root
        self.root.title("현자의 거울 - CapCut Auto Assembler v1.0")
        self.root.geometry("500x450")
        self.root.configure(bg="#0f172a")

        # 기본 경로 설정
        self.base_path = r"c:\Users\admin\Downloads\AI-Project\99_Output_Factory"
        
        # UI 구성
        self.create_widgets()
        print("[DEBUG] UI Creation successful.")

    def create_widgets(self):
        title_label = tk.Label(self.root, text="💎 CapCut Factory Assembler", font=("Arial", 16, "bold"), bg="#0f172a", fg="#fbbf24")
        title_label.pack(pady=20)

        self.status_text = tk.Text(self.root, height=10, width=55, bg="#1e293b", fg="#cbd5e1", font=("Consolas", 9))
        self.status_text.pack(pady=10)
        self.log("시스템 준비 완료. 재료 폴더를 확인하세요.")

        btn_check = tk.Button(self.root, text="📁 재료 폴더 스캔", command=self.scan_factory, width=30, bg="#334155", fg="white")
        btn_check.pack(pady=5)

        btn_assemble = tk.Button(self.root, text="🚀 캡컷 프로젝트 조립 시작", command=self.assemble, width=30, bg="#6366f1", fg="white")
        btn_assemble.pack(pady=15)

    def log(self, message):
        self.status_text.insert(tk.END, f"> {message}\n")
        self.status_text.see(tk.END)

    def scan_factory(self):
        self.log("--- 폴더 스캔 시작 ---")
        try:
            for folder in ["1_Narration", "2_Images", "3_Data"]:
                path = os.path.join(self.base_path, folder)
                if not os.path.exists(path):
                    os.makedirs(path)
                files = os.listdir(path)
                self.log(f"{folder}: {len(files)}개의 파일 발견")
        except Exception as e:
            self.log(f"스캔 오류: {str(e)}")

    def assemble(self):
        try:
            data_path = os.path.join(self.base_path, "3_Data", "draft_content.json")
            if not os.path.exists(data_path):
                messagebox.showerror("오류", "3_Data 폴더에 draft_content.json 파일이 없습니다!")
                return

            with open(data_path, 'r', encoding='utf-8') as f:
                draft_data = json.load(f)

            output_project_path = os.path.join(self.base_path, "COMPLETED_PROJECT")
            if not os.path.exists(output_project_path):
                os.makedirs(output_project_path)
            
            with open(os.path.join(output_project_path, "draft_content.json"), 'w', encoding='utf-8') as f:
                json.dump(draft_data, f, indent=4, ensure_ascii=False)

            self.log("캡컷 프로젝트 파일 주입 완료!")
            messagebox.showinfo("성공", "조립 완료!")
        except Exception as e:
            messagebox.showerror("오류", str(e))

if __name__ == "__main__":
    try:
        print("[DEBUG] Main block starting...")
        root = tk.Tk()
        app = CapCutAssembler(root)
        print("[DEBUG] Mainloop starting. Window should appear now.")
        root.mainloop()
    except Exception as e:
        print(f"[CRITICAL ERROR] {str(e)}")
        input("Press Enter to exit...")
