from playwright.sync_api import sync_playwright
import time
import json

def diagnose_dom():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8520")
        
        # Wait for the right panel to load
        page.wait_for_selector("#right-gemma-fixed-marker", state="attached", timeout=15000)
        time.sleep(2) # ensure layout settles
        
        # Inject script to extract DOM info
        result = page.evaluate("""() => {
            const marker = document.getElementById("right-gemma-fixed-marker");
            if (!marker) return "Marker not found";
            
            let parent = marker.parentElement;
            let output = [];
            let level = 0;
            
            while (parent && parent.tagName !== "BODY") {
                const style = window.getComputedStyle(parent);
                const testId = parent.getAttribute("data-testid") || "none";
                const classNames = parent.className || "none";
                
                output.push({
                    level: level,
                    tagName: parent.tagName,
                    testId: testId,
                    className: classNames,
                    position: style.position,
                    top: style.top,
                    height: style.height,
                    maxHeight: style.maxHeight,
                    overflow: style.overflow,
                    overflowY: style.overflowY,
                    display: style.display,
                    flex: style.flex,
                    flexDirection: style.flexDirection,
                    transform: style.transform,
                    contain: style.contain
                });
                
                parent = parent.parentElement;
                level++;
            }
            
            // Also find the chat container
            const chatContainer = document.querySelector('div[data-testid="stVerticalBlockBorderWrapper"]');
            let chatStyle = null;
            if(chatContainer) {
                const s = window.getComputedStyle(chatContainer);
                chatStyle = {
                    testId: "stVerticalBlockBorderWrapper",
                    height: s.height,
                    overflow: s.overflow,
                    overflowY: s.overflowY,
                    display: s.display,
                    flex: s.flex,
                    minHeight: s.minHeight
                };
            }
            
            return { hierarchy: output, chatContainer: chatStyle };
        }""")
        
        print(json.dumps(result, indent=2))
        browser.close()

if __name__ == "__main__":
    diagnose_dom()
