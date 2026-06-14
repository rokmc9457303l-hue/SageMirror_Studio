"""
DOM 진단 스크립트 - 우측 패널 스크롤 문제 원인 파악
실제 computed style, 부모 hierarchy, 높이 변화를 측정한다.
"""
import json
import time
from playwright.sync_api import sync_playwright

OUTPUT = {}

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1540, "height": 788})

        print("[STEP 1] http://localhost:8521 로드 중...")
        page.goto("http://localhost:8521", wait_until="domcontentloaded")
        # Streamlit이 실제로 렌더링되길 기다림
        page.wait_for_selector('div[data-testid="stHorizontalBlock"]', timeout=30000)
        time.sleep(3)

        page.screenshot(path="diag_01_initial.png")
        print("[STEP 1] 초기 스크린샷 저장 완료")

        # ──────────────────────────────────────────
        # STEP 2: 초기 DOM 구조 측정
        # ──────────────────────────────────────────
        initial = page.evaluate("""() => {
            function getStyle(el) {
                if (!el) return null;
                const s = window.getComputedStyle(el);
                const r = el.getBoundingClientRect();
                return {
                    testId: el.getAttribute('data-testid'),
                    tag: el.tagName,
                    position: s.position,
                    top: s.top,
                    height: s.height,
                    minHeight: s.minHeight,
                    maxHeight: s.maxHeight,
                    overflow: s.overflow,
                    overflowY: s.overflowY,
                    display: s.display,
                    flexGrow: s.flexGrow,
                    flexShrink: s.flexShrink,
                    flexBasis: s.flexBasis,
                    rect_top: r.top,
                    rect_bottom: r.bottom,
                    rect_height: r.height,
                    scrollHeight: el.scrollHeight,
                    clientHeight: el.clientHeight
                };
            }

            // 우측 Column 찾기 - stHorizontalBlock 안의 두 번째 stColumn
            const hBlock = document.querySelector('div[data-testid="stHorizontalBlock"]');
            const cols = hBlock ? hBlock.querySelectorAll(':scope > div[data-testid="stColumn"]') : [];
            const rightCol = cols.length >= 2 ? cols[cols.length - 1] : null;

            // 우측 Column 내의 stVerticalBlock (최상위)
            const rightColInner = rightCol ? rightCol.querySelector(':scope > div[data-testid="stVerticalBlock"]') : null;

            // border=True 컨테이너 (stVerticalBlockBorderWrapper)
            const borderWrapper = rightCol ? rightCol.querySelector('div[data-testid="stVerticalBlockBorderWrapper"]') : null;
            const borderInner = borderWrapper ? borderWrapper.querySelector(':scope > div[data-testid="stVerticalBlock"]') : null;

            // 텍스트 입력 영역 찾기
            const textarea = rightCol ? rightCol.querySelector('textarea') : null;
            const textareaWrapper = textarea ? textarea.closest('div[data-testid="stVerticalBlock"]') : null;

            // 전송 버튼 찾기
            const sendBtn = document.querySelector('button[data-testid="baseButton-primary"]');
            const sendBtnWrapper = sendBtn ? sendBtn.closest('div[data-testid="stHorizontalBlock"]') : null;

            // stMain 스크롤 컨테이너
            const stMain = document.querySelector('section[data-testid="stMain"]');

            // 부모 체인 분석
            let parents = [];
            if (rightCol) {
                let p = rightCol.parentElement;
                while (p && p.tagName !== "BODY") {
                    const s = window.getComputedStyle(p);
                    parents.push({
                        tag: p.tagName,
                        testId: p.getAttribute('data-testid'),
                        overflow: s.overflow,
                        overflowY: s.overflowY,
                        height: s.height,
                        display: s.display
                    });
                    p = p.parentElement;
                }
            }

            return {
                hBlock: getStyle(hBlock),
                rightCol: getStyle(rightCol),
                rightColInner: getStyle(rightColInner),
                borderWrapper: getStyle(borderWrapper),
                borderInner: getStyle(borderInner),
                textareaWrapper: getStyle(textareaWrapper),
                sendBtnWrapper: getStyle(sendBtnWrapper),
                stMain: getStyle(stMain),
                parentChain: parents
            };
        }""")

        print("\n=== [초기 DOM 측정] ===")
        print(json.dumps(initial, indent=2, ensure_ascii=False))
        OUTPUT["initial"] = initial

        # ──────────────────────────────────────────
        # STEP 3: 메시지 3회 전송
        # ──────────────────────────────────────────
        print("\n[STEP 3] 메시지 3회 전송 시도...")
        for i in range(1, 4):
            try:
                ta = page.locator('textarea').last
                ta.fill(f"스크롤 테스트 {i}")
                time.sleep(0.5)
                btn = page.locator('button:has-text("전송")').last
                btn.click()
                print(f"  → 메시지 {i} 전송 완료")
                # 스피너가 사라질 때까지 대기
                try:
                    page.wait_for_selector('div[data-testid="stSpinner"]', state="attached", timeout=5000)
                    page.wait_for_selector('div[data-testid="stSpinner"]', state="detached", timeout=60000)
                except:
                    pass
                time.sleep(1)
            except Exception as e:
                print(f"  → 메시지 {i} 전송 실패: {e}")

        page.screenshot(path="diag_02_after3msgs.png")
        print("[STEP 3] 3회 전송 후 스크린샷 저장")

        # ──────────────────────────────────────────
        # STEP 4: 3회 전송 후 높이 재측정
        # ──────────────────────────────────────────
        after3 = page.evaluate("""() => {
            function getHeights(el) {
                if (!el) return null;
                const r = el.getBoundingClientRect();
                return {
                    testId: el.getAttribute('data-testid'),
                    rect_top: r.top,
                    rect_bottom: r.bottom,
                    rect_height: r.height,
                    scrollHeight: el.scrollHeight,
                    clientHeight: el.clientHeight
                };
            }
            const hBlock = document.querySelector('div[data-testid="stHorizontalBlock"]');
            const cols = hBlock ? hBlock.querySelectorAll(':scope > div[data-testid="stColumn"]') : [];
            const rightCol = cols.length >= 2 ? cols[cols.length - 1] : null;
            const borderWrapper = rightCol ? rightCol.querySelector('div[data-testid="stVerticalBlockBorderWrapper"]') : null;
            const textarea = rightCol ? rightCol.querySelector('textarea') : null;
            const sendBtn = document.querySelector('button[data-testid="baseButton-primary"]');
            const stMain = document.querySelector('section[data-testid="stMain"]');
            return {
                rightCol: getHeights(rightCol),
                borderWrapper: getHeights(borderWrapper),
                textarea_rect: textarea ? (() => { const r = textarea.getBoundingClientRect(); return {top: r.top, bottom: r.bottom}; })() : null,
                sendBtn_rect: sendBtn ? (() => { const r = sendBtn.getBoundingClientRect(); return {top: r.top, bottom: r.bottom}; })() : null,
                stMain: { scrollHeight: stMain ? stMain.scrollHeight : null, clientHeight: stMain ? stMain.clientHeight : null }
            };
        }""")

        print("\n=== [3회 전송 후 높이 측정] ===")
        print(json.dumps(after3, indent=2, ensure_ascii=False))
        OUTPUT["after3"] = after3

        # ──────────────────────────────────────────
        # STEP 5: 중앙 화면 스크롤 후 우측 위치 확인
        # ──────────────────────────────────────────
        print("\n[STEP 5] 중앙 화면 스크롤 테스트...")
        page.evaluate("""() => {
            const stMain = document.querySelector('section[data-testid="stMain"]');
            if (stMain) stMain.scrollTop = 800;
        }""")
        time.sleep(0.8)
        page.screenshot(path="diag_03_scrolled.png")

        scrolled = page.evaluate("""() => {
            const hBlock = document.querySelector('div[data-testid="stHorizontalBlock"]');
            const cols = hBlock ? hBlock.querySelectorAll(':scope > div[data-testid="stColumn"]') : [];
            const rightCol = cols.length >= 2 ? cols[cols.length - 1] : null;
            const textarea = rightCol ? rightCol.querySelector('textarea') : null;
            const sendBtn = document.querySelector('button[data-testid="baseButton-primary"]');
            const stMain = document.querySelector('section[data-testid="stMain"]');
            const rect = rightCol ? rightCol.getBoundingClientRect() : null;
            return {
                rightCol_rect: rect ? {top: rect.top, bottom: rect.bottom, height: rect.height} : null,
                textarea_rect: textarea ? (() => { const r = textarea.getBoundingClientRect(); return {top: r.top, bottom: r.bottom, visible: r.top >= 0 && r.bottom <= 788}; })() : null,
                sendBtn_rect: sendBtn ? (() => { const r = sendBtn.getBoundingClientRect(); return {top: r.top, bottom: r.bottom, visible: r.top >= 0 && r.bottom <= 788}; })() : null,
                stMain_scrollTop: stMain ? stMain.scrollTop : null
            };
        }""")

        print("\n=== [스크롤 후 우측 위치] ===")
        print(json.dumps(scrolled, indent=2, ensure_ascii=False))
        OUTPUT["scrolled"] = scrolled

        browser.close()
        print("\n[완료] 브라우저 종료")

    with open("dom_diagnosis.json", "w", encoding="utf-8") as f:
        json.dump(OUTPUT, f, indent=2, ensure_ascii=False)
    print("dom_diagnosis.json 저장 완료")

if __name__ == "__main__":
    run()
