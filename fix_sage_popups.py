# -*- coding: utf-8 -*-
# fix_sage_popups.py — A모드 sys_ctx 최소화 수정 스크립트

import re

filepath = r"C:\SageMirror_Production\sage_popups.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

OLD = (
    "                # \u2500\u2500 \ud1b5\ud569 \uc2dc\uc2a4\ud15c \ucee8\ud14d\uc2a4\ud2b8 \uad6c\uc131 \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
    "                try:\n"
    "                    from sage_config import RAG_TAG_SYSTEM as _rts\n"
    "                except Exception:\n"
    "                    _rts = \"\"\n"
    "                sys_ctx = SAGE_PERSONA + \"\\n\\n\" + (_rts if _rts else \"\")\n"
    "\n"
    "                # \uc82c\ub9c8 \ud504\ub85c\ud1a0\ucf9c v9.0 \uc8fc\uc785\n"
    "                gemma_protocol = st.session_state.get(\"p1_gemma_protocol\", \"\")\n"
    "                if gemma_protocol:\n"
    "                    sys_ctx += \"[\uc82c\ub9c8 \ud504\ub85c\ud1a0\ucf9c]\\n\" + gemma_protocol + \"\\n\\n\"\n"
    "\n"
    "                sys_ctx += \"[\ud575\uc2ec 3\uc6d0\uce59]\\n\"\n"
    "                sys_ctx += \"HOW (\uc5b4\ub5bb\uac8c \ub9d0\ud558\ub294\uac00) \u2192 \uc790\uc720 (\ucc3d\uc758\u00b7\ud45c\ud604\u00b7\uc11c\uc0ac)\\n\"\n"
    "                sys_ctx += \"WHAT (\ubb34\uc5c7\uc744 \ub9d0\ud558\ub294\uac00) \u2192 \ud1b5\uc81c (\uc0ac\uc2e4 \uae30\ubc18\u00b7\ucd9c\uc798 \ud544\uc218)\\n\"\n"
    "                sys_ctx += \"WHO (\ub204\uad6c\ub85c\uc11c \ub9d0\ud558\ub294\uac00) \u2192 \uace0\uc815 (@Protagonist\u00b7\uae30\uc2b9\uc804\uacb0)\\n\\n\"\n"
    "                sys_ctx += \"[\uc751\ub2f5 \uc6d0\uce59]\\n\"\n"
    "                sys_ctx += \"1. \ubaa8\ub974\uba74 [NEED_RESEARCH: \ud0a4\uc6cc\ub4dc] \ud0dc\uadf8 \ucd9c\ub825. \uc808\ub300 \ucd94\uce21 \uae08\uc9c0.\\n\"\n"
    "                sys_ctx += \"2. \uc625\uc2dc\ub514\uc5b8 \uc790\ub8cc \ud544\uc694\uc2dc [READ_OBSIDIAN: \ud0a4\uc6cc\ub4dc] \ucd9c\ub825.\\n\"\n"
    "                sys_ctx += \"3. \uc790\ub3d9 \uc800\uc7a5 \uc694\uccad\uc2dc [SAVE_MEMORY: \uc81c\ubaa9] \ucd9c\ub825.\\n\"\n"
    "                sys_ctx += \"4. \uc790\uccb4 \uac80\uc99d \ud544\uc694\uc2dc [VERIFY: \ub0b4\uc6a9] \ucd9c\ub825.\\n\"\n"
    "                sys_ctx += \"5. \uc2ec\uce35 \ubd84\uc11d \ud544\uc694\uc2dc [ANALYZE: \uc8fc\uc81c] \ucd9c\ub825.\\n\"\n"
    "                sys_ctx += \"6. \ucd9c\uc138 \ud655\uc778 \ud544\uc694\uc2dc [CHECK_SOURCE: \uc778\uc6a9\uad6c] \ucd9c\ub825.\\n\"\n"
    "                sys_ctx += \"7. [SOURCE: \ucd9c\uc138] \ubc18\ub4dc\uc2dc \uba85\uae30. \uac00\uc9dc \uc131\uacbd \uad6c\uc808\u00b7\ucca0\ud559 \uc778\uc6a9 \uc808\ub300 \uae08\uc9c0.\\n\\n\"\n"
    "                sys_ctx += \"[\ud604\uc7ac \ud30c\ud2b8 \ucee8\ud14d\uc2a4\ud2b8]\\n\" + _build_part_context(current_part_key) + \"\\n\"\n"
    "                sys_ctx += \"[\uc625\uc2dc\ub514\uc5b8 \uaddc\uce59\uc11c]\\n\" + st.session_state.get(\"obsidian_rules\", \"\") + \"\\n\""
)

NEW = (
    "                # \u2500\u2500 \ud1b5\ud569 \uc2dc\uc2a4\ud15c \ucee8\ud14d\uc2a4\ud2b8 \uad6c\uc131 \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
    "                _current_mode = st.session_state.get(\"popup_gemma_mode\", \"A\")\n"
    "                if _current_mode == \"A\":\n"
    "                    # A\ubaa8\ub4dc: SAGE_PERSONA\ub9cc \uc0ac\uc6a9 (\ube60\ub978 \uc751\ub2f5)\n"
    "                    sys_ctx = SAGE_PERSONA\n"
    "                else:\n"
    "                    # B\ubaa8\ub4dc: \uc804\uccb4 \ucee8\ud14d\uc2a4\ud2b8 \uc8fc\uc785\n"
    "                    try:\n"
    "                        from sage_config import RAG_TAG_SYSTEM as _rts\n"
    "                    except Exception:\n"
    "                        _rts = \"\"\n"
    "                    sys_ctx = SAGE_PERSONA + \"\\n\\n\" + (_rts if _rts else \"\")\n"
    "\n"
    "                    # \uc82c\ub9c8 \ud504\ub85c\ud1a0\ucf9c v9.0 \uc8fc\uc785\n"
    "                    gemma_protocol = st.session_state.get(\"p1_gemma_protocol\", \"\")\n"
    "                    if gemma_protocol:\n"
    "                        sys_ctx += \"[\uc82c\ub9c8 \ud504\ub85c\ud1a0\ucf9c]\\n\" + gemma_protocol + \"\\n\\n\"\n"
    "\n"
    "                    sys_ctx += \"[\ud575\uc2ec 3\uc6d0\uce59]\\n\"\n"
    "                    sys_ctx += \"HOW (\uc5b4\ub5bb\uac8c \ub9d0\ud558\ub294\uac00) \u2192 \uc790\uc720 (\ucc3d\uc758\u00b7\ud45c\ud604\u00b7\uc11c\uc0ac)\\n\"\n"
    "                    sys_ctx += \"WHAT (\ubb34\uc5c7\uc744 \ub9d0\ud558\ub294\uac00) \u2192 \ud1b5\uc81c (\uc0ac\uc2e4 \uae30\ubc18\u00b7\ucd9c\uc798 \ud544\uc218)\\n\"\n"
    "                    sys_ctx += \"WHO (\ub204\uad6c\ub85c\uc11c \ub9d0\ud558\ub294\uac00) \u2192 \uace0\uc815 (@Protagonist\u00b7\uae30\uc2b9\uc804\uacb0)\\n\\n\"\n"
    "                    sys_ctx += \"[\uc751\ub2f5 \uc6d0\uce59]\\n\"\n"
    "                    sys_ctx += \"1. \ubaa8\ub974\uba74 [NEED_RESEARCH: \ud0a4\uc6cc\ub4dc] \ud0dc\uadf8 \ucd9c\ub825. \uc808\ub300 \ucd94\uce21 \uae08\uc9c0.\\n\"\n"
    "                    sys_ctx += \"2. \uc625\uc2dc\ub514\uc5b8 \uc790\ub8cc \ud544\uc694\uc2dc [READ_OBSIDIAN: \ud0a4\uc6cc\ub4dc] \ucd9c\ub825.\\n\"\n"
    "                    sys_ctx += \"3. \uc790\ub3d9 \uc800\uc7a5 \uc694\uccad\uc2dc [SAVE_MEMORY: \uc81c\ubaa9] \ucd9c\ub825.\\n\"\n"
    "                    sys_ctx += \"4. \uc790\uccb4 \uac80\uc99d \ud544\uc694\uc2dc [VERIFY: \ub0b4\uc6a9] \ucd9c\ub825.\\n\"\n"
    "                    sys_ctx += \"5. \uc2ec\uce35 \ubd84\uc11d \ud544\uc694\uc2dc [ANALYZE: \uc8fc\uc81c] \ucd9c\ub825.\\n\"\n"
    "                    sys_ctx += \"6. \ucd9c\uc138 \ud655\uc778 \ud544\uc694\uc2dc [CHECK_SOURCE: \uc778\uc6a9\uad6c] \ucd9c\ub825.\\n\"\n"
    "                    sys_ctx += \"7. [SOURCE: \ucd9c\uc138] \ubc18\ub4dc\uc2dc \uba85\uae30. \uac00\uc9dc \uc131\uacbd \uad6c\uc808\u00b7\ucca0\ud559 \uc778\uc6a9 \uc808\ub300 \uae08\uc9c0.\\n\\n\"\n"
    "                    sys_ctx += \"[\ud604\uc7ac \ud30c\ud2b8 \ucee8\ud14d\uc2a4\ud2b8]\\n\" + _build_part_context(current_part_key) + \"\\n\"\n"
    "                    sys_ctx += \"[\uc625\uc2dc\ub514\uc5b8 \uaddc\uce59\uc11c]\\n\" + st.session_state.get(\"obsidian_rules\", \"\") + \"\\n\""
)

if OLD in content:
    new_content = content.replace(OLD, NEW, 1)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("SUCCESS: sage_popups.py 수정 완료")
else:
    print("ERROR: 교체할 텍스트를 찾지 못했습니다")
    print("수동 확인 필요")
