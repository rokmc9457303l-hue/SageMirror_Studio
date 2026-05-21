import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

target_file = r'C:\SageMirror_Production\app_v15_9_1.py'

with open(target_file, 'rb') as f:
    raw = f.read()

# BOM 처리
if raw[:3] == b'\xef\xbb\xbf':
    content = raw[3:].decode('utf-8')
    had_bom = True
else:
    content = raw.decode('utf-8')
    had_bom = False

print(f"BOM: {had_bom}, Chars: {len(content)}")

# =============================================================================
# 작업 1: 버튼 명칭 변경 "Sage Pop-up" -> "젬마 어시스턴트"
# =============================================================================
old_btn = '"' + '\U0001f916' + ' Sage Pop-up"'
new_btn = '"' + '\U0001f916' + ' \uc82c\ub9c8 \uc5b4\uc2dc\uc2a4\ud134\ud2b8"'
count1 = content.count(old_btn)
content = content.replace(old_btn, new_btn)
print(f"[1] 버튼 교체: {count1}개")

# =============================================================================
# 작업 2: .sage-pipe-label 폰트 크기 교체 (빈줄 포함 패턴)
# =============================================================================
# 실제 파일에서 빈 줄 사이 패턴 찾기
pipe_idx = content.find('    .sage-pipe-label {')
if pipe_idx >= 0:
    # 닫힘 }까지 찾기
    close_idx = content.find('\n    }', pipe_idx)
    old_block = content[pipe_idx:close_idx + 6]
    print(f"[2] Old block: {repr(old_block[:60])}...")
    
    new_block = '''    .sage-pipe-label {
        font-size: 0.82em;
        color: #e2e8f0;
        text-align: center;
        white-space: nowrap;
        line-height: 1.4;
        font-weight: 600;
        letter-spacing: 0.01em;
    }'''
    content = content[:pipe_idx] + new_block + content[close_idx + 6:]
    print("[2] 파이프 라벨 CSS 교체 완료!")
else:
    print("[2] sage-pipe-label 미발견")

# =============================================================================
# 작업 3: glass-control-box CSS 추가
# =============================================================================
# /* 모델 셀렉트박스 스타일링 */ 앞에 삽입
comment_marker = '    /* 모델 셀렉트박스 스타일링 */'
if comment_marker in content:
    idx = content.index(comment_marker)
    glass_css = '''    /* ═══ 글래스모피즘 컨트롤 박스 — 파트 헤더 우측 통합 박스 ═══ */
    .glass-control-box {
        background: linear-gradient(135deg, rgba(30, 15, 5, 0.92) 0%, rgba(50, 25, 10, 0.88) 100%);
        border: 1.5px solid rgba(212,175,106,0.40);
        border-radius: 14px;
        padding: 5px 10px;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        box-shadow: 0 6px 24px rgba(0,0,0,0.5), inset 0 1px 0 rgba(212,175,106,0.25);
        margin-top: 3px;
    }

'''
    content = content[:idx] + glass_css + content[idx:]
    print("[3] glass-control-box CSS 삽입 완료!")
else:
    print("[3] 모델 셀렉트박스 주석 미발견, 대체 방법 시도")
    # header-pop-wrapper button 앞에 삽입
    alt_marker = '    .header-pop-wrapper button {'
    if alt_marker in content:
        idx = content.index(alt_marker)
        glass_css = '''    /* ═══ 글래스모피즘 컨트롤 박스 ═══ */
    .glass-control-box {
        background: linear-gradient(135deg, rgba(30, 15, 5, 0.92) 0%, rgba(50, 25, 10, 0.88) 100%);
        border: 1.5px solid rgba(212,175,106,0.40);
        border-radius: 14px;
        padding: 5px 10px;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        box-shadow: 0 6px 24px rgba(0,0,0,0.5), inset 0 1px 0 rgba(212,175,106,0.25);
    }

'''
        content = content[:idx] + glass_css + content[idx:]
        print("[3] glass-control-box CSS 삽입 완료 (대체)!")

# =============================================================================
# 작업 4: 버전 헤더 업데이트
# =============================================================================
old_ver = 'Master App v15.9\r\n'
new_ver = 'Master App v15.9.1\r\n'
if old_ver in content:
    content = content.replace(old_ver, new_ver, 1)
    print("[4] 버전 업데이트: v15.9 → v15.9.1")
elif 'Master App v15.9\n' in content:
    content = content.replace('Master App v15.9\n', 'Master App v15.9.1\n', 1)
    print("[4] 버전 업데이트 (LF): v15.9 → v15.9.1")
else:
    print("[4] 버전 패턴 미발견")

# =============================================================================
# 저장
# =============================================================================
with open(target_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nSaved! Lines: {len(content.split(chr(10)))}")

# 컴파일 체크
import subprocess
result = subprocess.run(['C:\\Python314\\python.exe', '-m', 'py_compile', target_file], 
                      capture_output=True, text=True)
if result.returncode == 0:
    print("COMPILE: OK!")
else:
    print(f"COMPILE ERROR: {result.stderr}")
