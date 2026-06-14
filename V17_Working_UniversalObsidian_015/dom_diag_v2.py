"""
DOM 진단 v2 - stMain 내부의 실제 우측 패널만 정확히 선택
"""
import json
import time
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1540, "height": 788})

        print("[STEP 1] http://localhost:8521 로드 중...")
        page.goto("http://localhost:8521", wait_until="domcontentloaded")
        page.wait_for_selector('section[data-testid="stMain"]', timeout=30000)
        time.sleep(4)
        page.screenshot(path="diag_v2_01_initial.png")

        # ─────────────────────────────────────────────────────────
        # STEP 2: stMain 내부의 실제 우측 패널 찾기
        # ─────────────────────────────────────────────────────────
        result = page.evaluate("""() => {
            function getStyle(el, label) {
                if (!el) return { label, error: 'null element' };
                const s = window.getComputedStyle(el);
                const r = el.getBoundingClientRect();
                return {
                    label,
                    testId: el.getAttribute('data-testid'),
                    tag: el.tagName,
                    position: s.position,
                    top_css: s.top,
                    height_css: s.height,
                    minHeight: s.minHeight,
                    maxHeight: s.maxHeight,
                    overflow: s.overflow,
                    overflowY: s.overflowY,
                    display: s.display,
                    flexGrow: s.flexGrow,
                    flexShrink: s.flexShrink,
                    flexBasis: s.flexBasis,
                    rect_top: Math.round(r.top * 10) / 10,
                    rect_bottom: Math.round(r.bottom * 10) / 10,
                    rect_height: Math.round(r.height * 10) / 10,
                    scrollHeight: el.scrollHeight,
                    clientHeight: el.clientHeight,
                    childCount: el.children.length
                };
            }

            // stMain 찾기
            const stMain = document.querySelector('section[data-testid="stMain"]');

            // stMain 내부의 stHorizontalBlock 중에서 stColumn을 2개 이상 가진 것 찾기
            const allHBlocks = stMain ? stMain.querySelectorAll('div[data-testid="stHorizontalBlock"]') : [];
            let targetHBlock = null;
            let leftCol = null;
            let rightCol = null;

            for (const hb of allHBlocks) {
                const cols = hb.querySelectorAll(':scope > div[data-testid="stColumn"]');
                if (cols.length >= 2) {
                    targetHBlock = hb;
                    leftCol = cols[0];
                    rightCol = cols[cols.length - 1];
                    break;
                }
            }

            // 우측 컬럼 내부 구조 탐색
            let borderWrapper = rightCol ? rightCol.querySelector('div[data-testid="stVerticalBlockBorderWrapper"]') : null;
            let borderWrapperInner = borderWrapper ? borderWrapper.querySelector(':scope > div[data-testid="stVerticalBlock"]') : null;
            let rightColInner = rightCol ? rightCol.querySelector(':scope > div[data-testid="stVerticalBlock"]') : null;
            let textarea = rightCol ? rightCol.querySelector('textarea') : null;
            let sendBtn = rightCol ? rightCol.querySelector('button[data-testid="baseButton-primary"]') : null;

            // 우측 컬럼 자식 구조 전체 나열
            let rightColChildren = [];
            if (rightColInner) {
                for (const child of rightColInner.children) {
                    const s = window.getComputedStyle(child);
                    const r = child.getBoundingClientRect();
                    rightColChildren.push({
                        testId: child.getAttribute('data-testid'),
                        tag: child.tagName,
                        height: s.height,
                        rect_h: Math.round(r.height * 10) / 10,
                        overflow: s.overflow,
                        overflowY: s.overflowY,
                        display: s.display,
                        flexGrow: s.flexGrow,
                        scrollH: child.scrollHeight,
                        clientH: child.clientHeight
                    });
                }
            }

            // 기존 CSS marker 찾기
            const marker = document.getElementById("right-gemma-fixed-marker");
            let markerParent = marker ? marker.parentElement : null;
            let markerAncestors = [];
            if (markerParent) {
                let el = markerParent;
                while (el && el.tagName !== "BODY") {
                    const s = window.getComputedStyle(el);
                    markerAncestors.push({
                        testId: el.getAttribute('data-testid'),
                        tag: el.tagName,
                        position: s.position,
                        height: s.height,
                        overflow: s.overflow,
                        overflowY: s.overflowY
                    });
                    el = el.parentElement;
                }
            }

            // CSS 셀렉터 검증
            const wrongSelector = document.querySelectorAll('div[data-testid="column"]');
            const rightSelector = document.querySelectorAll('div[data-testid="stColumn"]');

            return {
                stMain: getStyle(stMain, "stMain"),
                targetHBlock: getStyle(targetHBlock, "targetHBlock"),
                rightCol: getStyle(rightCol, "rightCol"),
                rightColInner: getStyle(rightColInner, "rightColInner"),
                borderWrapper: getStyle(borderWrapper, "borderWrapper"),
                borderWrapperInner: getStyle(borderWrapperInner, "borderWrapperInner"),
                textarea: textarea ? (() => {
                    const r = textarea.getBoundingClientRect();
                    return { rect_top: r.top, rect_bottom: r.bottom, rect_height: r.height };
                })() : null,
                sendBtn: sendBtn ? (() => {
                    const r = sendBtn.getBoundingClientRect();
                    return { rect_top: r.top, rect_bottom: r.bottom };
                })() : null,
                rightColChildren: rightColChildren,
                markerFound: !!marker,
                markerAncestors: markerAncestors,
                cssCheck: {
                    wrongSelectorMatches: wrongSelector.length,  // data-testid="column" 개수
                    rightSelectorMatches: rightSelector.length   // data-testid="stColumn" 개수
                }
            };
        }""")

        print("\n=== [DOM 진단 v2] ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # 스크린샷 - 각 요소 하이라이트
        page.evaluate("""() => {
            // 우측 패널 하이라이트 (빨간 테두리)
            const stMain = document.querySelector('section[data-testid="stMain"]');
            const allHBlocks = stMain ? stMain.querySelectorAll('div[data-testid="stHorizontalBlock"]') : [];
            for (const hb of allHBlocks) {
                const cols = hb.querySelectorAll(':scope > div[data-testid="stColumn"]');
                if (cols.length >= 2) {
                    cols[cols.length-1].style.outline = '3px solid red';
                    // border wrapper
                    const bw = cols[cols.length-1].querySelector('div[data-testid="stVerticalBlockBorderWrapper"]');
                    if (bw) bw.style.outline = '3px solid blue';
                    break;
                }
            }
        }""")
        page.screenshot(path="diag_v2_02_highlight.png")

        browser.close()

if __name__ == "__main__":
    run()
