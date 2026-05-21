import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

target_file = r'C:\SageMirror_Production\app_v15_9_1.py'

with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"File loaded. Total chars: {len(content)}")

# =============================================================================
# 작업 1: 버튼 명칭 변경 확인 (이미 했음)
# =============================================================================
btn_text = chr(0x1f916) + ' ' + chr(0xC82C) + chr(0xB9C8) + ' ' + chr(0xC5B4) + chr(0xC2DC) + chr(0xC2A4) + chr(0xD134) + chr(0xD2B8)
btn_full = '"' + btn_text + '"'
count1 = content.count(btn_full)
count2 = content.count('"' + chr(0x1f916) + ' Sage Pop-up"')
print(f"[Button] 젬마 어시스턴트: {count1}, Sage Pop-up remaining: {count2}")

# =============================================================================
# 작업 2: 파이프 라벨 CSS - 빈 줄이 포함된 형태로 교체
# =============================================================================
# 실제 파일에는 각 줄 사이에 빈 줄이 있음 (개행이 \n\n 형태)
old_pipe = '    .sage-pipe-label {\n\n        font-size: 0.70em;\n\n        color: #cbd5e1;\n\n        text-align: center;\n\n        white-space: nowrap;\n\n        line-height: 1.3;\n\n        font-weight: 500;\n\n    }'
new_pipe = '    .sage-pipe-label {\n        font-size: 0.82em;\n        color: #e2e8f0;\n        text-align: center;\n        white-space: nowrap;\n        line-height: 1.4;\n        font-weight: 600;\n        letter-spacing: 0.01em;\n    }'

pipe_count = content.count(old_pipe)
print(f"[Pipe CSS] Found old pattern: {pipe_count}")

if pipe_count > 0:
    content = content.replace(old_pipe, new_pipe)
    print("[Pipe CSS] Replaced!")
else:
    # 줄 바꿈 패턴 다르게 시도
    old_pipe2 = '    .sage-pipe-label {\r\n\r\n        font-size: 0.70em;'
    cnt2 = content.count(old_pipe2)
    print(f"  CRLF version count: {cnt2}")
    
    # 실제 텍스트 덤프
    idx = content.find('.sage-pipe-label {')
    if idx >= 0:
        chunk = content[idx:idx+200]
        print(f"  Actual text: {repr(chunk)}")

# =============================================================================
# 작업 3: glass-control-box CSS 추가 (header-model-wrapper 앞에)
# =============================================================================
glass_css = '''    .glass-control-box {
        background: linear-gradient(135deg, rgba(40, 20, 10, 0.85) 0%, rgba(60, 30, 15, 0.75) 100%);
        border: 1px solid rgba(212,175,106,0.35);
        border-radius: 12px;
        padding: 4px 8px;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.4), inset 0 1px 0 rgba(212,175,106,0.2);
    }
'''

# header-model-wrapper CSS 찾기
old_model_wrapper = '    .header-model-wrapper {'
if old_model_wrapper in content:
    # 앞에 glass-control-box 삽입
    first_idx = content.index(old_model_wrapper)
    content = content[:first_idx] + glass_css + content[first_idx:]
    print("[Glass CSS] 글래스모피즘 박스 CSS 추가 완료!")
else:
    print("[Glass CSS] header-model-wrapper 미발견")
    # 찾아보기
    idx = content.find('header-model-wrapper')
    print(f"  Alternative search: {repr(content[max(0,idx-50):idx+100]) if idx >= 0 else 'Not found'}")

# =============================================================================
# 파일 저장
# =============================================================================
with open(target_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nSaved! Total lines: {len(content.split(chr(10)))}")
