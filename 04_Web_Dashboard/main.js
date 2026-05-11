const SERVER_URL = "http://127.0.0.1:5050"; 

const MODULE_DATA = {
    research: { title: "RESEARCH MASTER WORKSPACE", engines: ["1. 벤치마킹 분석", "2. 주제 선정 (20선)", "3. 통합 제작 기획서"], filename: "01_RESEARCH_PLAN" },
    thumbnail: { title: "VISUAL CONCEPT WORKSPACE", engines: ["1. 썸네일 컨셉 도출", "2. 레이아웃 설계", "3. 시각적 후킹 분석"], filename: "02_VISUAL_PLAN" },
    script: { title: "SCRIPT WRITING WORKSPACE", engines: ["1. 대본 초안 구성", "2. 인트로 후킹 강화", "3. 최종 대본 다듬기"], filename: "03_SCRIPT_FINAL" },
    image: { title: "IMAGE GENERATION WORKSPACE", engines: ["1. 이미지 프롬프트 설계", "2. AI 이미지 생성 요청", "3. 에셋 최종 선정"], filename: "04_IMAGE_ASSETS" },
    video: { title: "VIDEO EDITING WORKSPACE", engines: ["1. 컷 편집 가이드", "2. 특수효과(FX) 배치", "3. 최종 영상 검수"], filename: "05_VIDEO_PRODUCTION" },
    narration: { title: "VOICE NARRATION WORKSPACE", engines: ["1. 나레이션 톤 설정", "2. AI 음성 합성 요청", "3. 싱크 및 호흡 조절"], filename: "06_VOICE_DATA" },
    bgm: { title: "SOUND & MUSIC WORKSPACE", engines: ["1. BGM 큐레이션", "2. 효과음(SFX) 배치", "3. 사운드 믹싱 지시"], filename: "07_SOUND_PLAN" },
    capcut: { title: "MASTER ASSEMBLY WORKSPACE", engines: ["1. 전체 프로젝트 조립", "2. 메타데이터 최종화", "3. 렌더링 및 배포 준비"], filename: "08_MASTER_EXPORT" }
};

const RULES = {
    obsidian: `# [[Title of Concept/Entity]]\n\n## 📌 Brief Summary\n(A concise 1-2 sentence definition of this topic.)\n\n## 📖 Core Content\n(Detailed explanation synthesized from raw sources.)\n\n## 🔗 Knowledge Connections\n- **Related Topics:** [[Related-Concept-A]], [[Related-Concept-B]]\n- **Projects/Contexts:** [[Project-Name]]\n- **Contradictions/Notes:** (특이사항 및 보완점 기록)\n\n---\n*Last updated: ${new Date().toLocaleDateString()}*`,
    prompt: `### 🏛️ [절대 규정] 젬마: 키워드 분석가 활용 지침\n\n1. **키워드 분석 지령**\n   - 대화 시 가장 중요한 키워드 5개를 추출하십시오.\n   - 형식: [[키워드]] (대괄호 필수)\n   - 분류 예시:\n     * 분류 [철학]: [[쇼펜하우어]], [[의지]]\n     * 분류 [심리]: [[그림자]], [[고립]]\n     * 분류 [성경]: [[광야]]\n\n2. **지식 관리 전략**\n   - 방법 A (노트 생성): 키워드별 새 노트를 만들고 관련 문장을 기록하라.\n   - 방법 B (태그 시스템): #철학, #심리 등 '이름표'를 붙여 관리하라.\n\n3. **마스터 키워드 전략**\n   - 하위 개념에 매몰되지 말고 [[인생론]], [[염세주의]] 같은 상위 개념(마스터 키워드)을 함께 제시하여 지식의 지도를 그려라.`,
    gemma_locked: `[🏛️ 젬마야, 이것은 너의 절대 지령이다!]\n\n1. 자료를 받으면 반드시 핵심 키워드 5개를 [[키워드]] 형식으로 뽑아줘.\n2. 이 키워드가 [철학], [심리], [성경] 중 어디에 속하는지 명확히 분류해줘.\n3. 지식의 지도를 그릴 수 있게 [[상위 개념]]도 꼭 함께 알려줘야 해.\n4. 나중에 옵시디언에서 찾기 쉽게 #태그(이름표)도 잊지 마!\n--------------------------------------------------\n[현자의 가르침 아래 작업이 시작됩니다...]\n`
};

let CURRENT_MODULE = 'research';

// 안전하게 텍스트를 넣는 헬퍼 함수
function setVal(id, val) {
    const el = document.getElementById(id);
    if (el) el.value = val;
}

function openModule(name) {
    try {
        if (!MODULE_DATA[name]) return;
        CURRENT_MODULE = name;
        const config = MODULE_DATA[name];
        const overlay = document.getElementById('workspaceOverlay');
        if (!overlay) return;

        // UI 업데이트
        const titleEl = document.getElementById('workspace-title');
        if (titleEl) titleEl.innerText = config.title;
        
        // 엔진 라벨 업데이트
        const engineLabels = document.querySelectorAll('.engine-row .ws-label');
        engineLabels.forEach((label, idx) => {
            if (config.engines[idx]) label.innerText = config.engines[idx];
        });

        // 규칙 주입
        setVal('rule-obsidian', RULES.obsidian);
        setVal('rule-prompt', RULES.prompt);
        setVal('protocol-gemma', RULES.gemma_locked);
        setVal('protocol-gemini', "[GEMINI: 마스터 전략 엔진]\n분야별 알고리즘 및 구조화 분석 수행.");

        overlay.classList.add('active');
        addLog(`✨ ${config.title} 활성화.`);
    } catch (e) {
        console.error(e);
        addLog(`❌ 모달 오픈 에러: ${e.message}`);
    }
}

function closeWorkspace() {
    const overlay = document.getElementById('workspaceOverlay');
    if (overlay) overlay.classList.remove('active');
}

async function saveAllWorkspace() {
    try {
        const config = MODULE_DATA[CURRENT_MODULE];
        addLog(`💾 [${CURRENT_MODULE}] 데이터 옵시디언 전송 시작...`);
        
        const combinedContent = `
# 🔬 ${config.title} REPORT (${new Date().toLocaleString()})

## 📜 RULES & PROTOCOLS
${document.getElementById('rule-obsidian')?.value || ""}

---

## 📊 PRODUCTION OUTPUTS
### ${config.engines[0]}
${document.getElementById('out-benchmarking')?.innerText || ""}

### ${config.engines[1]}
${document.getElementById('out-topics')?.innerText || ""}

### ${config.engines[2]}
${document.getElementById('out-final')?.innerText || ""}
`;

        const res = await fetch(`${SERVER_URL}/api/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: combinedContent, filename: config.filename, topic: CURRENT_MODULE })
        });
        const result = await res.json();
        if (result.status === "success") {
            addLog(`✅ 저장 완료: ${result.path}`);
            alert(`${config.title} 저장 성공!`);
        }
    } catch (e) {
        addLog(`❌ 저장 에러: ${e.message}`);
    }
}

function toggleZoom(id) {
    const box = document.getElementById(id);
    if (box) box.classList.toggle('zoomed');
}

function addLog(msg) {
    const log = document.getElementById('log-content');
    if (!log) return;
    const time = new Date().toLocaleTimeString();
    log.innerHTML += `<div>[${time}] ${msg}</div>`;
    log.scrollTop = log.scrollHeight;
}

function openMegaChat() { document.getElementById('megaChatOverlay')?.classList.add('active'); }
function closeMegaChat() { document.getElementById('megaChatOverlay')?.classList.remove('active'); }

async function sendMegaChatMessage() {
    try {
        const input = document.getElementById('mega-chat-input');
        const msg = input?.value.trim();
        if (!msg) return;
        
        addLog(`💬 질문: ${msg}`);
        const history = document.getElementById('mega-chat-history');
        if (history) {
            history.innerHTML += `<div class="chat-bubble user">${msg}</div>`;
            input.value = "";
        }
        
        const useSearch = document.getElementById('search-toggle')?.checked || false;
        const res = await fetch(`${SERVER_URL}/api/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: msg, use_search: useSearch })
        });
        const data = await res.json();
        if (history) {
            history.innerHTML += `<div class="chat-bubble ai">${data.response}</div>`;
            history.scrollTop = history.scrollHeight;
        }
    } catch (e) {
        addLog(`❌ AI 에러: ${e.message}`);
    }
}

setInterval(async () => {
    try {
        const res = await fetch(`${SERVER_URL}/api/stats`);
        const data = await res.json();
        const cpu = document.getElementById('cpu-usage');
        const ram = document.getElementById('ram-usage');
        const dot = document.getElementById('bridge-dot');
        if (cpu) cpu.innerText = `${data.cpu}%`;
        if (ram) ram.innerText = `${data.ram}%`;
        if (dot) dot.className = "node-dot online";
    } catch (e) {
        const dot = document.getElementById('bridge-dot');
        if (dot) dot.className = "node-dot offline";
    }
}, 3000);
