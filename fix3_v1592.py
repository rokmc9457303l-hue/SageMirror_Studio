import sys, io, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

target_file = r'C:\SageMirror_Production\app_v15_9_2.py'

with open(target_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"[로드] 총 줄 수: {len(lines)}")

# 1. 5269줄 근처의 st.error(f"채널 탐색 오류: {e}\n→ API Key 확인 또는 다른 모델을 선택해 보세요.") 수정
# 파이썬 f-string 안의 줄바꿈 에러 해결
for i, ln in enumerate(lines):
    if 'st.error(f"채널 탐색 오류:' in ln or 'st.error(f"ä Ž :' in ln:
        print(f"발견! 줄 {i+1}: {repr(ln[:80])}")
        # 다음 두 줄을 합침
        lines[i] = '                    st.error(f"채널 탐색 오류: {e} -> API Key 확인 또는 다른 모델을 선택해 보세요.")\n'
        # 다음 줄이 "→ API Key 확인 또는 다른 모델을 선택해 보세요.")" 형태일 것이므로 비워줌
        if 'API Key' in lines[i+1] or '모델을 선택' in lines[i+1]:
            print(f"비울 다음 줄 {i+2}: {repr(lines[i+1][:80])}")
            lines[i+1] = '\n'
        break

content = ''.join(lines)

# 2. 세션스테이트 초기화 부분 확인
# 'youtube_api_key'를 찾아서 초기화 딕셔너리에 추가
# "youtube_api_key": "" 대신 다른 초기화 스타일이 있는지 확인
idx = content.find('"youtube_api_key"')
if idx >= 0:
    print(f"youtube_api_key 발견 컨텍스트: {repr(content[idx-100:idx+200])}")
    # "youtube_api_key": st.session_state.get("youtube_api_key", "") 이런 형태인가?
    # 아니면 딕셔너리 리터럴인가?
    # 'load_workspace_state()' 안이나 초기 세션 상태 설정 부분을 찾아보자.

# 3. py_compile 테스트
with open(target_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n[저장] 줄 수: {len(content.splitlines())}")

result = subprocess.run(
    ['C:\\Python314\\python.exe', '-m', 'py_compile', target_file],
    capture_output=True, text=True, encoding='utf-8', errors='replace'
)
if result.returncode == 0:
    print("COMPILE: OK!")
else:
    err = result.stderr
    print(f"COMPILE ERROR: {err[:600]}")
    import re
    match = re.search(r'line (\d+)', err)
    if match:
        err_line = int(match.group(1))
        lines2 = content.split('\n')
        print("에러 주변:")
        for j in range(max(0, err_line-4), min(len(lines2), err_line+4)):
            print(f"  {j+1}: {repr(lines2[j][:90])}")
