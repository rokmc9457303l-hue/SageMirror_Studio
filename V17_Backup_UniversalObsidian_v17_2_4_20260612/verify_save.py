import time
import os
from playwright.sync_api import sync_playwright

def verify():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("[1] 앱 접속...")
        page.goto("http://localhost:8524")
        page.wait_for_selector('section[data-testid="stMain"]', timeout=30000)
        time.sleep(5)
        
        print("[2] 질문 입력...")
        textarea = page.locator('textarea[aria-label="메시지"]')
        textarea.fill("기술 발전이 인간의 집중력에 미치는 영향을 범용 지식 자료로 정리해줘.")
        
        print("[3] 전송 클릭...")
        send_btn = page.locator('button:has-text("전송")')
        send_btn.click()
        
        print("[4] 응답 대기 (최대 180초)...")
        # assistant 메시지가 나타날 때까지 대기
        page.wait_for_selector('div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"])', timeout=180000)
        time.sleep(20) # 답변이 충분히 생성될 때까지 대기
        
        print("[5] 기능 팝오버 열기...")
        plus_btn = page.locator('button:has-text("＋ 기능")')
        plus_btn.click()
        time.sleep(2)
        
        print("[6] 옵시디언 저장 버튼 클릭...")
        save_btn = page.locator('button:has-text("옵시디언 저장")')
        save_btn.click()
        time.sleep(25) # 팝오버가 닫히고 저장이 완료될 때까지 대기 (내부 Gemma 호출 때문)
        
        print("[7] 첫 번째 저장 완료 스크린샷...")
        page.screenshot(path="verify_save_1.png")
        
        print("[8] 중복 저장 테스트...")
        plus_btn.click()
        time.sleep(2)
        save_btn.click()
        time.sleep(15)
        
        print("[9] 두 번째 저장 완료 스크린샷...")
        page.screenshot(path="verify_save_2.png")
        
        browser.close()

if __name__ == "__main__":
    verify()
