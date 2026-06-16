import time
from playwright.sync_api import sync_playwright

def verify():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("[1] 앱 접속...")
        page.goto("http://localhost:8507")
        page.wait_for_selector('section[data-testid="stMain"]', timeout=30000)
        time.sleep(5)
        
        print("[2] 질문 입력...")
        # st.chat_input is actually an input inside a form, but here it might be a text area.
        textarea = page.locator('textarea[aria-label="메시지"]')
        textarea.fill("Obsidian 저장 검증 테스트입니다. Raw Wiki Schema Logs 저장 여부를 확인합니다.")
        
        print("[3] 전송 클릭...")
        send_btn = page.locator('button:has-text("전송")').first
        send_btn.click()
        
        print("[4] 대기 (Gemma 응답)...")
        time.sleep(25)
        
        print("[5] 기능 팝오버 열기...")
        plus_btn = page.locator('button:has-text("＋기능")').first
        if plus_btn.is_visible():
            plus_btn.click()
            time.sleep(2)
        else:
            plus_btn = page.locator('button:has-text("＋ 기능")').first
            if plus_btn.is_visible():
                plus_btn.click()
                time.sleep(2)
                
        print("[6] 옵시디언 저장 버튼 클릭...")
        save_btn = page.locator('button:has-text("옵시디언 저장")').first
        if save_btn.is_visible():
            save_btn.click()
            time.sleep(15)
        else:
            print("옵시디언 저장 버튼을 찾을 수 없음!")
        
        browser.close()
        print("[10] 검증 종료")

if __name__ == "__main__":
    verify()
