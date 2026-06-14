# AGENT_SYSTEM.md
> SAGE Studio V18 — 11개 에이전트 운영 시스템 구현 설계
> 작성: 2026-06-14 | 버전: v19.0.0

---

# 0. 이 문서의 정체

11개 에이전트를 실제 코드로 어떻게 구현할지 명시. `core/agents/` 폴더 구조와 각 에이전트 인터페이스를 정의.

---

# 1. 폴더 구조

```
core/
└── agents/
    ├── __init__.py
    ├── base.py              ← BaseAgent 추상 클래스
    ├── conductor.py         ← 지휘자
    ├── librarian.py         ← Part 1
    ├── architect.py         ← Part 2
    ├── writer.py            ← Part 3
    ├── artist.py            ← Part 4
    ├── director.py          ← Part 5
    ├── composer.py          ← Part 6
    ├── editor.py            ← Part 7
    ├── assembler.py         ← Part 8
    ├── critic.py            ← 보조: 검수
    ├── curator.py           ← 보조: 옵시디언 관리
    └── scout.py             ← 보조: 자료 보강
```

---

# 2. BaseAgent 추상 클래스

```python
# core/agents/base.py
from abc import ABC, abstractmethod
from typing import Optional
from core.state import get_state, set_state
from core.brain import call_model


class BaseAgent(ABC):
    """모든 에이전트의 기반 클래스"""
    
    name: str = "BaseAgent"
    role: str = ""
    default_model: str = "gemma4:e2b"
    
    def __init__(self, channel_profile: dict = None):
        self.profile = channel_profile or self._load_default_profile()
        self.system_prompt = self._build_system_prompt()
    
    def _load_default_profile(self) -> dict:
        """현재 채널 Profile 로드"""
        from core.profile_loader import load_current_profile
        return load_current_profile()
    
    def _build_system_prompt(self) -> str:
        """채널 Profile을 시스템 프롬프트에 주입"""
        return f"""
당신은 {self.name}입니다.
역할: {self.role}

채널 정보:
- 채널명: {self.profile.get('channel_name', '')}
- 타깃: {self.profile.get('target_audience', '')}
- 톤: {self.profile.get('tone', '')}
- 시각 스타일: {self.profile.get('visual_style', '')}
- 금지 표현: {self.profile.get('forbidden_expressions', [])}
- 선호 표현: {self.profile.get('preferred_expressions', [])}

{self.specific_instructions()}
"""
    
    @abstractmethod
    def specific_instructions(self) -> str:
        """각 에이전트별 고유 지시사항"""
        pass
    
    @abstractmethod
    def execute(self, input_data: dict) -> dict:
        """에이전트 실행 — 결과 dict 반환"""
        pass
    
    def call_ai(self, prompt: str, model: str = None) -> str:
        """AI 호출 (Gemma / Gemini)"""
        return call_model(
            prompt=prompt,
            system=self.system_prompt,
            model=model or self.default_model,
        )
    
    def log(self, message: str):
        """03_Logs에 작업 기록"""
        from core.obsidian import log_agent_action
        log_agent_action(self.name, message)
```

---

# 3. Conductor (지휘자)

```python
# core/agents/conductor.py
from core.agents.base import BaseAgent


class ConductorAgent(BaseAgent):
    name = "🎼 Conductor"
    role = "전체 흐름 조율 · Part 전환 결정 · 사용자 입력 라우팅"
    default_model = "gemma4:e2b"
    
    def specific_instructions(self) -> str:
        return """
당신은 SAGE Studio의 지휘자입니다.
사용자가 우측 대화창에 입력할 때마다 호출됩니다.

당신의 판단:
1. 이 메시지가 어느 Part에 해당하는가
2. 새로운 작업 시작인가, 기존 작업 보강인가
3. 검수가 필요한가
4. 어느 보조 에이전트(Critic / Curator / Scout)를 호출할 것인가

반드시 JSON으로 응답:
{
  "target_part": 1-8 or "current",
  "intent": "start | continue | review | revise | save",
  "needs_critic": true/false,
  "needs_scout": true/false,
  "user_message_summary": "..."
}
"""
    
    def execute(self, input_data: dict) -> dict:
        """사용자 메시지 라우팅"""
        user_msg = input_data.get("user_message", "")
        current_part = input_data.get("current_part", 1)
        
        prompt = f"""
[현재 Part] Part {current_part}
[사용자 메시지] {user_msg}

라우팅 판단하세요.
"""
        result = self.call_ai(prompt)
        self.log(f"Routed: {user_msg[:50]}")
        return {"routing": result}
```

---

# 4. Librarian (Part 1)

```python
# core/agents/librarian.py
from core.agents.base import BaseAgent
from core.agents.scout import ScoutAgent
from core.agents.curator import CuratorAgent


class LibrarianAgent(BaseAgent):
    name = "📚 Librarian"
    role = "유튜브 채널 분석 · 댓글 기반 주제 10개 발굴"
    default_model = "gemma4:e4b"
    
    def specific_instructions(self) -> str:
        return """
당신은 유튜브 떡상 영상 발굴 전문가입니다.

절대 원칙:
1. 실제 검색 결과의 채널·영상만 분석합니다. 창작 금지.
2. 댓글에서 실제 시청자의 고통·후회·외로움·관계 상처를 발견합니다.
3. 댓글을 근거로 시청자가 "내 이야기 같다"고 느낄 주제 10개 이상 생성합니다.

금지:
- 댓글 근거 없는 추상적 주제
- 일반론·교과서 같은 주제
- 채널명·URL·구독자수·조회수 창작

출력: Comment Topic Packet JSON (최소 10개 topic_candidates)
"""
    
    def execute(self, input_data: dict) -> dict:
        """Part 1 전체 흐름 실행"""
        user_topic = input_data.get("user_topic")
        channel_url = input_data.get("channel_url")
        
        # 1. YouTube/Tavily 검색
        channels = self._search_channels(user_topic, channel_url)
        
        # 2. 댓글 수집 (대표 영상)
        comments = self._collect_comments(channels)
        
        # 3. 감정 분석 + 주제 후보 생성
        topics = self._generate_topics(comments)
        
        # 4. Curator 호출: Obsidian 저장
        curator = CuratorAgent(self.profile)
        save_paths = curator.execute({
            "raw_content": comments,
            "wiki_content": topics,
            "category": "감정",
            "source_type": "youtube_comments",
        })
        
        # 5. Comment Topic Packet 생성
        packet = self._build_packet(channels, topics, save_paths)
        return packet
    
    def _search_channels(self, topic, url):
        """YouTube Data API + Tavily 검색"""
        # 구현: 기존 part1_자료수집.py의 run_benchmark() 활용
        pass
    
    def _collect_comments(self, channels):
        """댓글 200개 수집"""
        pass
    
    def _generate_topics(self, comments) -> list:
        """주제 후보 10개 이상 생성"""
        prompt = f"""
[수집된 댓글 200개]
{comments[:5000]}

위 댓글에서 시청자의 실제 고통과 경험을 찾아 주제 후보 10개 이상 생성하세요.

각 주제 형식:
{{
  "topic_id": "T001",
  "topic": "...",
  "title_candidate": "...",
  "comment_basis": "댓글에서 직접 인용한 근거",
  "recommendation_reason": "...",
  "expected_reaction": "...",
  "expected_effect": "...",
  "emotions": [],
  "risk_notes": "",
  "planning_hint": "Part 2 감정 흐름..."
}}
"""
        result = self.call_ai(prompt, model="gemma4:e4b")
        return result
    
    def _build_packet(self, channels, topics, paths) -> dict:
        return {
            "packet_type": "comment_based_topic_candidates",
            "source_part": "Part1",
            "target_part": "Part2",
            "channel_profile": self.profile.get("channel_name"),
            "topic_candidates": topics,
            "minimum_count": 10,
            "raw_path": paths.get("raw"),
            "wiki_path": paths.get("wiki"),
            "schema_path": paths.get("schema"),
        }
```

---

# 5. Critic (보조 — 검수)

```python
# core/agents/critic.py
from core.agents.base import BaseAgent


class CriticAgent(BaseAgent):
    name = "🔍 Critic"
    role = "모든 Part 결과물 자동 검수"
    default_model = "gemma4:e4b"
    
    def specific_instructions(self) -> str:
        return """
당신은 엄격한 검수자입니다.

검수 항목:
□ 자료 근거가 있는가
□ 헛소리가 없는가
□ 논리 흐름이 맞는가
□ 사용자 의도와 맞는가
□ 채널 Profile과 맞는가
□ 복제 위험이 없는가
□ 다음 Part가 사용할 수 있는가
□ 순번이 맞는가

판정:
- PASS: 모든 항목 통과
- NEEDS_DATA: 자료 근거 부족 → Scout 호출 필요
- NEEDS_FIX: 논리/형식 오류 → 재작성 필요

반드시 JSON으로 응답:
{
  "verdict": "PASS | NEEDS_DATA | NEEDS_FIX",
  "score": 0.0-1.0,
  "issues": [],
  "missing_data": [],
  "suggestions": []
}
"""
    
    def execute(self, input_data: dict) -> dict:
        result = input_data.get("part_result")
        part_num = input_data.get("part_num")
        
        prompt = f"""
[Part {part_num} 결과]
{result}

[채널 Profile]
{self.profile}

위 결과를 검수하세요.
"""
        verdict = self.call_ai(prompt)
        self.log(f"Reviewed Part {part_num}: {verdict[:50]}")
        return {"critic_verdict": verdict}
```

---

# 6. Curator (보조 — 옵시디언 관리)

```python
# core/agents/curator.py
from datetime import datetime
from pathlib import Path
import json
import hashlib
from core.agents.base import BaseAgent
from core.config import OBSIDIAN_PATH


class CuratorAgent(BaseAgent):
    name = "📦 Curator"
    role = "옵시디언 Raw / Wiki / Schema 자동 저장 및 분류"
    default_model = "gemma4:e2b"
    
    def specific_instructions(self) -> str:
        return """
당신은 옵시디언 큐레이터입니다.

자료 입력 시:
1. 카테고리 자동 분류 (감정/철학/심리학/성경/유튜브전략/채널운영/제작자료)
2. 키워드 추출 (3~8개)
3. 태그 추출 (3~8개)
4. 채널 관련성 점수 (0.0~1.0)
5. 관련 Part 번호 추론

출력: 메타데이터 JSON
"""
    
    def execute(self, input_data: dict) -> dict:
        raw_content = input_data.get("raw_content", "")
        wiki_content = input_data.get("wiki_content", "")
        source_type = input_data.get("source_type", "unknown")
        
        # 1. 메타데이터 추출
        meta = self._extract_metadata(raw_content)
        
        # 2. 채널별 동적 경로
        channel = self.profile.get("channel_name", "default")
        raw_dir = OBSIDIAN_PATH / "00_Raw_Data" / f"채널_{channel}"
        wiki_dir = OBSIDIAN_PATH / "01_Wiki" / meta["categories"][0]
        schema_dir = OBSIDIAN_PATH / "02_Schema"
        
        for d in [raw_dir, wiki_dir, schema_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # 3. 저장
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_id = f"SRC_{ts}"
        
        raw_path = raw_dir / f"{source_id}_raw.md"
        wiki_path = wiki_dir / f"{source_id}_wiki.md"
        schema_path = schema_dir / f"{source_id}.json"
        
        raw_path.write_text(raw_content, encoding="utf-8")
        wiki_path.write_text(self._build_wiki(wiki_content, meta), encoding="utf-8")
        
        # 4. Schema JSON
        schema = {
            "source_id": source_id,
            "source_type": source_type,
            "title": meta.get("title", ""),
            "channel_name": channel,
            "categories": meta["categories"],
            "tags": meta["tags"],
            "keywords": meta["keywords"],
            "raw_path": str(raw_path),
            "wiki_path": str(wiki_path),
            "hash": hashlib.sha256(raw_content.encode()).hexdigest()[:16],
            "created_at": datetime.now().isoformat(),
            "channel_relevance": meta.get("relevance", 0.5),
            "related_parts": meta.get("parts", [1]),
            "status": "indexed",
        }
        schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
        
        self.log(f"Saved: {source_id}")
        
        return {
            "raw": str(raw_path),
            "wiki": str(wiki_path),
            "schema": str(schema_path),
            "source_id": source_id,
        }
    
    def _extract_metadata(self, content: str) -> dict:
        """Gemma로 메타데이터 추출"""
        prompt = f"""
다음 자료의 메타데이터를 추출하세요:

{content[:2000]}

JSON 형식:
{{
  "title": "...",
  "categories": ["감정"],
  "tags": ["배신감", "후회"],
  "keywords": ["참다", "떠나다"],
  "relevance": 0.0-1.0,
  "parts": [1, 2]
}}
"""
        # 간단 구현: AI 호출 결과 파싱
        # 실제 구현 시 JSON 파싱 + 오류 처리
        return {
            "title": "",
            "categories": ["감정"],
            "tags": [],
            "keywords": [],
            "relevance": 0.5,
            "parts": [1],
        }
    
    def _build_wiki(self, content: str, meta: dict) -> str:
        """Wiki 노트 포맷"""
        return f"""---
title: {meta.get('title', '')}
categories: {meta['categories']}
tags: {meta['tags']}
keywords: {meta['keywords']}
created: {datetime.now().isoformat()}
relevance: {meta.get('relevance', 0.5)}
parts: {meta.get('parts', [])}
---

{content}
"""
```

---

# 7. Scout (보조 — 자료 보강)

```python
# core/agents/scout.py
import requests
import streamlit as st
from core.agents.base import BaseAgent
from core.agents.curator import CuratorAgent


class ScoutAgent(BaseAgent):
    name = "🛰️ Scout"
    role = "자료 부족 시 Tavily 검색 + Obsidian 자동 저장"
    default_model = "gemma4:e2b"
    
    def specific_instructions(self) -> str:
        return """
당신은 자료 정찰병입니다.
Critic이 NEEDS_DATA 판정 시 호출됩니다.
부족한 자료를 Tavily 웹 검색으로 찾아 옵시디언에 저장합니다.
"""
    
    def execute(self, input_data: dict) -> dict:
        query = input_data.get("query")
        missing_topics = input_data.get("missing_data", [])
        
        api_key = st.session_state.get("api_tavily", "")
        if not api_key:
            return {"success": False, "message": "Tavily 키 필요"}
        
        # 1. Tavily 검색
        results = self._tavily_search(query, api_key)
        
        # 2. Curator 호출하여 저장
        curator = CuratorAgent(self.profile)
        saved_count = 0
        for item in results:
            content = item.get("content", "")
            if len(content) < 100:
                continue
            curator.execute({
                "raw_content": content,
                "wiki_content": content,
                "source_type": "tavily_supplement",
            })
            saved_count += 1
        
        self.log(f"Supplemented {saved_count} items for: {query}")
        return {
            "success": True,
            "saved_count": saved_count,
            "query": query,
        }
    
    def _tavily_search(self, query, api_key, max_results=5):
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "advanced",
            },
            timeout=30,
        )
        if resp.status_code != 200:
            return []
        return resp.json().get("results", [])
```

---

# 8. 에이전트 협업 흐름 (코드 예시)

```python
# 사용자가 Part 1 "🔎 채널 찾기 & 주제 발굴" 버튼 클릭

def run_part1_full_flow(user_topic: str, channel_url: str):
    """Part 1 전체 흐름 — 에이전트 협업"""
    
    from core.profile_loader import load_current_profile
    from core.agents.librarian import LibrarianAgent
    from core.agents.critic import CriticAgent
    from core.agents.scout import ScoutAgent
    
    profile = load_current_profile()
    
    # 1. Librarian 실행
    librarian = LibrarianAgent(profile)
    packet = librarian.execute({
        "user_topic": user_topic,
        "channel_url": channel_url,
    })
    
    # 2. Critic 자동 검수
    critic = CriticAgent(profile)
    verdict = critic.execute({
        "part_result": packet,
        "part_num": 1,
    })
    
    # 3. NEEDS_DATA 시 Scout 호출
    if "NEEDS_DATA" in verdict["critic_verdict"]:
        scout = ScoutAgent(profile)
        scout.execute({
            "query": user_topic,
            "missing_data": verdict.get("missing_data", []),
        })
        # 보강 후 Librarian 재실행
        packet = librarian.execute({
            "user_topic": user_topic,
            "channel_url": channel_url,
        })
    
    # 4. 사용자에게 표시 (DRAFT 상태)
    set_state("p1_packet", packet)
    set_state("p1_status", "DRAFT")
    
    return packet
```

---

# 9. Channel Profile 로더

```python
# core/profile_loader.py
import yaml
from pathlib import Path
from core.state import get_state, set_state


def load_profile(channel_name: str) -> dict:
    """특정 채널 Profile 로드"""
    path = Path("profiles") / f"{channel_name}.yaml"
    if not path.exists():
        return load_template()
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_current_profile() -> dict:
    """현재 선택된 채널 Profile"""
    channel = get_state("current_channel", "sage_mirror")
    return load_profile(channel)


def load_template() -> dict:
    """기본 템플릿"""
    path = Path("profiles") / "_template.yaml"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def list_available_profiles() -> list:
    """사용 가능한 Profile 목록"""
    profiles_dir = Path("profiles")
    if not profiles_dir.exists():
        return []
    return [p.stem for p in profiles_dir.glob("*.yaml") if not p.stem.startswith("_")]


def save_profile(channel_name: str, profile_data: dict):
    """Profile 저장"""
    path = Path("profiles") / f"{channel_name}.yaml"
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(profile_data, f, allow_unicode=True, sort_keys=False)
```

---

# 10. 구축 우선순위

## 즉시 (1단계)
```
1. core/agents/ 폴더 생성
2. core/agents/base.py — BaseAgent 추상 클래스
3. core/profile_loader.py
4. profiles/_template.yaml + profiles/sage_mirror.yaml
5. 사이드바에 채널 선택 드롭다운 추가
```

## 2단계
```
6. core/agents/curator.py — Obsidian 저장 시스템
7. core/agents/scout.py — Tavily 보강
8. core/agents/critic.py — 검수
9. core/agents/librarian.py — Part 1 리팩토링
```

## 3단계
```
10. Conductor — 전체 흐름 통제
11. Part 2~8 에이전트 순차 구축
```

---

**문서 끝 — 에이전트 구현은 이 문서를 기준으로.**
