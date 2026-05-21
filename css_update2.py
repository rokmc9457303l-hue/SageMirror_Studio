import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

target_file = r'C:\SageMirror_Production\app_v15_9_1.py'

with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 실제 header-model-wrapper 위치 찾기
idx = content.find('.header-model-wrapper div[data-baseweb')
if idx >= 0:
    # 이 CSS 블록 앞에 glass-control-box 삽입
    # header-model-wrapper 전체 블록 시작점 찾기
    # 뒤로 찾아가서 가장 가까운 /* 주석 */을 찾자
    search_back = content.rfind('/* ', 0, idx)
    chunk = content[search_back:search_back+200]
    print(f"Found comment: {repr(chunk[:80])}")
    
    # 주석 앞에 glass-control-box 추가
    glass_css = '''    /* 글래스모피즘 컨트롤 박스 - 파트 헤더 우측 */
    .glass-control-box {
        background: linear-gradient(135deg, rgba(30, 15, 5, 0.9) 0%, rgba(50, 25, 10, 0.85) 100%);
        border: 1.5px solid rgba(212,175,106,0.40);
        border-radius: 14px;
        padding: 5px 10px;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        box-shadow: 0 6px 24px rgba(0,0,0,0.5), inset 0 1px 0 rgba(212,175,106,0.25);
        margin-top: 2px;
    }

'''
    insert_pos = search_back
    content = content[:insert_pos] + glass_css + content[insert_pos:]
    print("Glass CSS inserted!")
else:
    print("header-model-wrapper div not found")

# =============================================================================
# 버전 헤더 업데이트 (v15.9 -> v15.9.1)
# =============================================================================
old_ver = 'Master App v15.9\n'
new_ver = 'Master App v15.9.1\n'
if old_ver in content:
    content = content.replace(old_ver, new_ver, 1)
    print("Version updated: v15.9 -> v15.9.1")
else:
    # \r\n 버전 시도
    old_ver2 = 'Master App v15.9\r\n'
    if old_ver2 in content:
        content = content.replace(old_ver2, 'Master App v15.9.1\r\n', 1)
        print("Version updated (CRLF): v15.9 -> v15.9.1")
    else:
        print(f"Version pattern not found")

# 파일 저장
with open(target_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Saved! Total lines: {len(content.split(chr(10)))}")
print("\n=== 최종 확인 ===")

with open(target_file, 'r', encoding='utf-8') as f:
    content2 = f.read()

btn_full = '"' + chr(0x1f916) + ' ' + chr(0xC82C) + chr(0xB9C8) + ' ' + chr(0xC5B4) + chr(0xC2DC) + chr(0xC2A4) + chr(0xD134) + chr(0xD2B8) + '"'
print(f"[1] 젬마 어시스턴트 버튼: {content2.count(btn_full)}개 (목표: 9)")
print(f"[2] Sage Pop-up 잔존: {content2.count('Sage Pop-up')}개 (목표: 0)")
print(f"[3] 0.82em 폰트: {content2.count('0.82em')}개")
print(f"[4] glass-control-box: {content2.count('glass-control-box')}개")
print(f"[5] v15.9.1: {content2.count('v15.9.1')}개")
