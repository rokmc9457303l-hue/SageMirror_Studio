"""
수정 후 검증 - stColumn sticky 및 chat_container 높이 고정 확인
"""
import json
import time
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1540, "height": 788})

        print("[STEP 1] http://localhost:8521 로드...")
        page.goto("http://localhost:8521", wait_until="domcontentloaded")
        page.wait_for_selector('section[data-testid="stMain"]', timeout=30000)
        time.sleep(5)  # Streamlit 완전 렌더링 대기

        page.screenshot(path="verify_01_initial.png")

        # 수정 후 DOM 확인
        result = page.evaluate("""() => {
            function getStyle(el, label) {
                if (!el) return { label, error: 'null' };
                const s = window.getComputedStyle(el);
                const r = el.getBoundingClientRect();
                return {
                    label,
                    testId: el.getAttribute('data-testid'),
                    position: s.position,
                    top_css: s.top,
                    height_css: s.height,
                    maxHeight: s.maxHeight,
                    overflow: s.overflow,
                    rect_top: Math.round(r.top),
                    rect_height: Math.round(r.height),
                    scrollHeight: el.scrollHeight,
                    clientHeight: el.clientHeight
                };
            }

            const stMain = document.querySelector('section[data-testid="stMain"]');
            const marker = document.getElementById("right-research-marker");

            // stMain 내의 stHorizontalBlock > 두 번째 stColumn
            const allHBlocks = stMain ? stMain.querySelectorAll('div[data-testid="stHorizontalBlock"]') : [];
            let rightCol = null;
            for (const hb of allHBlocks) {
                const cols = hb.querySelectorAll(':scope > div[data-testid="stColumn"]');
                if (cols.length >= 2) {
                    rightCol = cols[cols.length - 1];
                    break;
                }
            }

            // 채팅 컨테이너 (stLayoutWrapper height=500)
            const chatWrapper = rightCol ? (() => {
                for (const el of rightCol.querySelectorAll('div[data-testid="stLayoutWrapper"]')) {
                    if (el.clientHeight >= 490) return el;
                }
                return null;
            })() : null;

            // textarea
            const textarea = rightCol ? rightCol.querySelector('textarea') : null;

            return {
                markerFound: !!marker,
                rightCol: getStyle(rightCol, "rightCol"),
                chatWrapper: getStyle(chatWrapper, "chatWrapper"),
                textarea: textarea ? (() => { const r = textarea.getBoundingClientRect(); return {rect_top: Math.round(r.top), rect_bottom: Math.round(r.bottom), visible: r.top >= 0 && r.bottom <= 788}; })() : null,
                stMain: { scrollHeight: stMain ? stMain.scrollHeight : null }
            };
        }""")

        print("=== [수정 후 DOM 확인] ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # stMain 스크롤 후 우측 패널 위치 확인
        page.evaluate("() => { const m = document.querySelector('section[data-testid=\"stMain\"]'); if(m) m.scrollTop = 600; }")
        time.sleep(0.5)
        page.screenshot(path="verify_02_scrolled.png")

        scrolled = page.evaluate("""() => {
            const stMain = document.querySelector('section[data-testid="stMain"]');
            const allHBlocks = stMain ? stMain.querySelectorAll('div[data-testid="stHorizontalBlock"]') : [];
            let rightCol = null;
            for (const hb of allHBlocks) {
                const cols = hb.querySelectorAll(':scope > div[data-testid="stColumn"]');
                if (cols.length >= 2) { rightCol = cols[cols.length - 1]; break; }
            }
            const rect = rightCol ? rightCol.getBoundingClientRect() : null;
            const textarea = rightCol ? rightCol.querySelector('textarea') : null;
            return {
                rightCol_top_after_scroll: rect ? Math.round(rect.top) : null,
                textarea_visible: textarea ? (() => { const r = textarea.getBoundingClientRect(); return r.top >= 0 && r.bottom <= 788; })() : null,
                stMain_scrollTop: stMain ? stMain.scrollTop : null
            };
        }""")

        print("=== [스크롤 후 위치] ===")
        print(json.dumps(scrolled, indent=2, ensure_ascii=False))

        browser.close()

if __name__ == "__main__":
    run()
