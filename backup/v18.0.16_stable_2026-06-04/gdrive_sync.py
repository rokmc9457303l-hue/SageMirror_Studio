# -*- coding: utf-8 -*-
"""
core/gdrive_sync.py — Google Drive + Docs 자동 동기화

기능:
- OAuth 인증 (최초 1회)
- 지정 폴더 5분 주기 polling
- 새 파일 자동 다운로드
- 형식별 텍스트 추출 (gdoc/pdf/docx/txt/md)
- 옵시디언 규칙서 자동 변환 + 듀얼 저장
"""

import os
import json
import time
import threading
from pathlib import Path
from datetime import datetime

# Google API
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

from core.config import OBSIDIAN_SYSTEM
from core.unified_save import save_anything


# ── 설정 경로 ──────────────────────────────────
DATA_DIR = Path(r"C:\SageMirror_Studio_v18\data")
CREDENTIALS_FILE = DATA_DIR / "google_credentials.json"
TOKEN_FILE = DATA_DIR / "google_token.json"
SYNC_STATE_FILE = DATA_DIR / "gdrive_sync_state.json"

# Drive 스코프
SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/documents.readonly",
]


# ── 인증 ────────────────────────────────────
def get_credentials():
    """OAuth 인증 (최초 1회 + 자동 갱신)"""
    
    if not GOOGLE_API_AVAILABLE:
        raise ImportError("google-api-python-client 미설치")
    
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"OAuth 인증 파일 없음: {CREDENTIALS_FILE}"
        )
    
    creds = None
    
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(
            str(TOKEN_FILE), SCOPES
        )
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    
    return creds


# ── 폴더 ID 가져오기 ────────────────────────
def get_folder_id(service, folder_name: str):
    """이름으로 Drive 폴더 ID 찾기"""
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(
        q=query,
        fields="files(id, name)",
    ).execute()
    items = results.get("files", [])
    return items[0]["id"] if items else None


# ── 파일 목록 조회 ──────────────────────────
def list_files_in_folder(service, folder_id: str, modified_after: str = None):
    """폴더 내 파일 목록"""
    query = f"'{folder_id}' in parents and trashed = false"
    if modified_after:
        query += f" and modifiedTime > '{modified_after}'"
    
    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType, modifiedTime, size)",
        orderBy="modifiedTime desc",
    ).execute()
    
    return results.get("files", [])


# ── 파일 내용 추출 ──────────────────────────
def extract_file_content(service, docs_service, file_info: dict) -> str:
    """파일 형식별 텍스트 추출"""
    
    file_id = file_info["id"]
    mime_type = file_info["mimeType"]
    name = file_info["name"]
    
    try:
        # Google Docs
        if mime_type == "application/vnd.google-apps.document":
            doc = docs_service.documents().get(documentId=file_id).execute()
            content = []
            for elem in doc.get("body", {}).get("content", []):
                if "paragraph" in elem:
                    for r in elem["paragraph"].get("elements", []):
                        if "textRun" in r:
                            content.append(r["textRun"].get("content", ""))
            return "".join(content)
        
        # 일반 텍스트
        elif mime_type in ["text/plain", "text/markdown"]:
            request = service.files().get_media(fileId=file_id)
            from googleapiclient.http import MediaIoBaseDownload
            import io
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            return fh.getvalue().decode("utf-8", errors="ignore")
        
        # PDF (메타데이터만, 실제 추출은 다운로드 후 별도 처리)
        elif mime_type == "application/pdf":
            return f"[PDF 파일: {name}]\n다운로드 후 별도 텍스트 추출 필요"
        
        else:
            return f"[지원하지 않는 형식: {mime_type}]\n파일명: {name}"
    
    except Exception as e:
        return f"[추출 실패: {e}]"


# ── 동기화 상태 관리 ────────────────────────
def load_sync_state() -> dict:
    if SYNC_STATE_FILE.exists():
        return json.loads(SYNC_STATE_FILE.read_text(encoding="utf-8"))
    return {"last_sync": None, "processed_ids": []}


def save_sync_state(state: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SYNC_STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ── 메인 동기화 함수 ─────────────────────────
def sync_drive_folder(folder_name: str = "현자의거울_자료") -> dict:
    """지정 Drive 폴더 자료 자동 수집"""
    
    if not GOOGLE_API_AVAILABLE:
        return {"success": False, "error": "google-api-python-client 미설치"}
    
    try:
        creds = get_credentials()
        drive_service = build("drive", "v3", credentials=creds)
        docs_service = build("docs", "v1", credentials=creds)
        
        # 폴더 ID
        folder_id = get_folder_id(drive_service, folder_name)
        if not folder_id:
            return {
                "success": False,
                "error": f"폴더 '{folder_name}' 찾을 수 없음",
                "hint": "Google Drive에 해당 이름의 폴더를 만들어주세요",
            }
        
        # 상태 로드
        state = load_sync_state()
        last_sync = state.get("last_sync")
        
        # 파일 목록
        files = list_files_in_folder(drive_service, folder_id, last_sync)
        
        new_files = [f for f in files if f["id"] not in state.get("processed_ids", [])]
        
        if not new_files:
            return {
                "success": True,
                "new_files": 0,
                "message": "새 파일 없음",
            }
        
        # 처리
        processed = []
        for f in new_files:
            content = extract_file_content(drive_service, docs_service, f)
            
            if content and not content.startswith("[추출 실패"):
                # 통합 저장 엔진 호출
                save_anything(
                    content=content,
                    title=f["name"].replace(".gdoc", "").replace(".pdf", ""),
                    content_type="google_drive",
                    extra_meta={
                        "drive_file_id": f["id"],
                        "mime_type": f["mimeType"],
                        "modified": f.get("modifiedTime"),
                        "source": "Google Drive",
                    },
                )
                processed.append({
                    "name": f["name"],
                    "id": f["id"],
                    "size": len(content),
                })
        
        # 상태 업데이트
        state["last_sync"] = datetime.now().isoformat()
        state["processed_ids"] = list(set(
            state.get("processed_ids", []) + [f["id"] for f in new_files]
        ))[-200:]  # 최근 200개만 유지
        save_sync_state(state)
        
        return {
            "success": True,
            "new_files": len(processed),
            "processed": processed,
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


# ── 백그라운드 동기화 (5분 주기) ─────────────
_sync_thread = None
_sync_active = False


def start_auto_sync(folder_name: str = "현자의거울_자료", interval: int = 300):
    """백그라운드 자동 동기화 시작"""
    global _sync_thread, _sync_active
    
    if _sync_active:
        return False
    
    _sync_active = True
    
    def worker():
        while _sync_active:
            try:
                result = sync_drive_folder(folder_name)
                if result.get("new_files", 0) > 0:
                    print(f"[GDrive 동기화] 새 파일 {result['new_files']}건 수집")
            except Exception as e:
                print(f"[GDrive 동기화 오류] {e}")
            
            time.sleep(interval)
    
    _sync_thread = threading.Thread(target=worker, daemon=True)
    _sync_thread.start()
    return True


def stop_auto_sync():
    global _sync_active
    _sync_active = False


def get_sync_status() -> dict:
    state = load_sync_state()
    return {
        "active": _sync_active,
        "last_sync": state.get("last_sync"),
        "total_processed": len(state.get("processed_ids", [])),
    }
