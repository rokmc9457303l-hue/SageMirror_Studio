import json
import time
from playwright.sync_api import sync_playwright

def run_diagnostics():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1540, "height": 788})
        
        print("1. Opening http://localhost:8521")
        page.goto("http://localhost:8521")
        
        # Wait for Streamlit to load
        page.wait_for_selector('div[data-testid="stColumn"]', timeout=30000)
        time.sleep(3) # Wait for initial render to settle
        
        print("2. Extracting initial DOM metrics")
        initial_metrics = page.evaluate("""() => {
            const cols = document.querySelectorAll('div[data-testid="stColumn"]');
            if (cols.length < 2) return { error: "Could not find right column" };
            
            const rightCol = cols[cols.length - 1]; // Assume last column is right
            const mainScrollContainer = document.querySelector('section[data-testid="stMain"]');
            const mainContainer = document.querySelector('div[data-testid="stMainBlockContainer"]');
            
            // Find chat container - it is inside rightCol, usually a stVerticalBlockBorderWrapper
            const chatWrapper = rightCol.querySelector('div[data-testid="stVerticalBlockBorderWrapper"]');
            
            // Find input area
            const inputs = rightCol.querySelectorAll('div[data-testid="stVerticalBlock"]');
            // the last one is usually the wrapper for the inputs
            const inputWrapper = inputs[inputs.length - 1];
            
            const rightColRect = rightCol.getBoundingClientRect();
            const rightColStyle = window.getComputedStyle(rightCol);
            
            const chatStyle = chatWrapper ? window.getComputedStyle(chatWrapper) : null;
            const chatRect = chatWrapper ? chatWrapper.getBoundingClientRect() : null;
            const chatInner = chatWrapper ? chatWrapper.querySelector('div[data-testid="stVerticalBlock"]') : null;
            const chatInnerRect = chatInner ? chatInner.getBoundingClientRect() : null;
            
            const inputStyle = inputWrapper ? window.getComputedStyle(inputWrapper) : null;
            const inputRect = inputWrapper ? inputWrapper.getBoundingClientRect() : null;
            
            let parent = rightCol.parentElement;
            let parents = [];
            while(parent && parent.tagName !== "BODY") {
                const s = window.getComputedStyle(parent);
                parents.push({
                    tagName: parent.tagName,
                    testId: parent.getAttribute("data-testid"),
                    overflow: s.overflow,
                    overflowY: s.overflowY,
                    height: s.height
                });
                parent = parent.parentElement;
            }
            
            return {
                rightCol: {
                    testId: "stColumn",
                    position: rightColStyle.position,
                    top: rightColStyle.top,
                    width: rightColStyle.width,
                    height: rightColStyle.height,
                    overflow: rightColStyle.overflow,
                    flex: rightColStyle.flex,
                    rect: { top: rightColRect.top, bottom: rightColRect.bottom, height: rightColRect.height }
                },
                chatArea: {
                    testId: "stVerticalBlockBorderWrapper",
                    height: chatStyle ? chatStyle.height : "null",
                    clientHeight: chatWrapper ? chatWrapper.clientHeight : null,
                    scrollHeight: chatWrapper ? chatWrapper.scrollHeight : null,
                    rect: chatRect ? { top: chatRect.top, bottom: chatRect.bottom, height: chatRect.height } : null,
                    innerRect: chatInnerRect ? { height: chatInnerRect.height } : null
                },
                inputArea: {
                    testId: "stVerticalBlock",
                    height: inputStyle ? inputStyle.height : "null",
                    rect: inputRect ? { top: inputRect.top, bottom: inputRect.bottom } : null
                },
                parents: parents,
                main: {
                    scrollHeight: mainScrollContainer ? mainScrollContainer.scrollHeight : null,
                    clientHeight: mainScrollContainer ? mainScrollContainer.clientHeight : null
                }
            };
        }""")
        
        print("=== Initial Metrics ===")
        print(json.dumps(initial_metrics, indent=2))
        
        print("3. Sending 15 messages...")
        # Actually typing and sending 15 messages might take too long for playwright test
        # Just send 5 messages to simulate height growth
        for i in range(1, 6):
            page.fill('textarea[aria-label="메시지"]', f"스크롤 테스트 {i}")
            # wait for value to update
            page.wait_for_timeout(200)
            # click send
            page.click('button:has-text("전송")')
            page.wait_for_timeout(1000)
            
            # Wait for assistant response to complete. 
            # In local test, it might be fast. Let's wait for the spinner to disappear.
            try:
                page.wait_for_selector('div[data-testid="stSpinner"]', state="detached", timeout=30000)
            except:
                pass
            
            page.screenshot(path=f"chat_{i}.png")
            print(f"Sent message {i}")
            
        print("4. Extracting DOM metrics after messages")
        final_metrics = page.evaluate("""() => {
            const cols = document.querySelectorAll('div[data-testid="stColumn"]');
            if (cols.length < 2) return { error: "Could not find right column" };
            
            const rightCol = cols[cols.length - 1]; // Assume last column is right
            const mainScrollContainer = document.querySelector('section[data-testid="stMain"]');
            const chatWrapper = rightCol.querySelector('div[data-testid="stVerticalBlockBorderWrapper"]');
            const inputs = rightCol.querySelectorAll('div[data-testid="stVerticalBlock"]');
            const inputWrapper = inputs[inputs.length - 1];
            
            const rightColRect = rightCol.getBoundingClientRect();
            const chatRect = chatWrapper ? chatWrapper.getBoundingClientRect() : null;
            const inputRect = inputWrapper ? inputWrapper.getBoundingClientRect() : null;
            const chatInner = chatWrapper ? chatWrapper.querySelector('div[data-testid="stVerticalBlock"]') : null;
            const chatInnerRect = chatInner ? chatInner.getBoundingClientRect() : null;
            
            return {
                rightCol: {
                    height: window.getComputedStyle(rightCol).height,
                    rect: { top: rightColRect.top, bottom: rightColRect.bottom, height: rightColRect.height }
                },
                chatArea: {
                    clientHeight: chatWrapper ? chatWrapper.clientHeight : null,
                    scrollHeight: chatWrapper ? chatWrapper.scrollHeight : null,
                    rect: chatRect ? { top: chatRect.top, bottom: chatRect.bottom, height: chatRect.height } : null,
                    innerRect: chatInnerRect ? { height: chatInnerRect.height } : null
                },
                inputArea: {
                    rect: inputRect ? { top: inputRect.top, bottom: inputRect.bottom } : null
                },
                main: {
                    scrollHeight: mainScrollContainer ? mainScrollContainer.scrollHeight : null
                }
            };
        }""")
        
        print("=== Final Metrics ===")
        print(json.dumps(final_metrics, indent=2))
        
        # Test scrolling down
        print("5. Scrolling main window down...")
        page.evaluate("""() => {
            const mainScrollContainer = document.querySelector('section[data-testid="stMain"]');
            if(mainScrollContainer) {
                mainScrollContainer.scrollTop = 1000;
            } else {
                window.scrollTo(0, 1000);
            }
        }""")
        page.wait_for_timeout(500)
        page.screenshot(path="chat_scrolled.png")
        
        scroll_metrics = page.evaluate("""() => {
            const cols = document.querySelectorAll('div[data-testid="stColumn"]');
            const rightCol = cols[cols.length - 1];
            const rightColRect = rightCol.getBoundingClientRect();
            return {
                rightCol: { rect: { top: rightColRect.top, bottom: rightColRect.bottom } }
            };
        }""")
        print("=== Scrolled Metrics ===")
        print(json.dumps(scroll_metrics, indent=2))
        
        browser.close()

if __name__ == "__main__":
    run_diagnostics()
