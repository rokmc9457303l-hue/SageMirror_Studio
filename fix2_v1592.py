import sys, io, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

target_file = r'C:\SageMirror_Production\app_v15_9_2.py'

with open(target_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"[로드] 총 줄 수: {len(lines)}")

# 5203~5210 문제 구간 찾아서 수정
# 깨진 f-string 패턴을 찾아 한 줄로 재조합
problem_start = -1
for i, ln in enumerate(lines):
    if 'candidates_text +=' in ln and 'Title:' in ln and 'f"' in ln:
        problem_start = i
        print(f"문제 줄 {i+1}: {repr(ln[:80])}")
        break

if problem_start >= 0:
    # 다음 몇 줄을 확인하여 끊긴 부분 합치기
    print("주변 줄:")
    for j in range(max(0, problem_start-2), min(len(lines), problem_start+10)):
        print(f"  {j+1}: {repr(lines[j][:100])}")
    
    # 새로운 한 줄 f-string으로 교체
    new_line = '                        candidates_text += "[" + str(i+1) + "] " + r.get("title","") + "\\n URL: " + r.get("url","") + "\\n Content: " + r.get("content","")[:200] + "\\n\\n"\n'
    
    # 문제 줄부터 빈줄/닫힘까지 삭제하고 새 줄로 교체
    # 끊긴 f-string의 끝을 찾기
    end_line = problem_start
    for j in range(problem_start, min(len(lines), problem_start + 8)):
        if lines[j].strip() in ['', '"']:
            end_line = j
        elif j > problem_start and 'candidates_text' not in lines[j] and 'filter_prompt' in lines[j]:
            end_line = j - 1
            break
    
    print(f"교체 범위: {problem_start+1} ~ {end_line+1}")
    lines = lines[:problem_start] + [new_line] + lines[end_line+1:]
    print("[수정] f-string 한 줄로 재조합 완료!")

content = ''.join(lines)

# 세션스테이트 초기화 — keys_to_save 리스트나 초기화 dict에 추가
# 정확한 위치 탐색
ss_marker = '"youtube_api_key"'
for i, ln in enumerate(lines if lines else content.split('\n')):
    if ss_marker in str(ln) and 'text_input' not in str(ln):
        print(f"세션스테이트 위치 {i+1}: {repr(str(ln)[:80])}")
        break

# 세션스테이트 초기화 추가 — DEFAULT_SESSION 딕셔너리 위치
init_marker = '"youtube_api_key": ""'
if init_marker in content:
    content = content.replace(
        '"youtube_api_key": ""',
        '"youtube_api_key": "",\n        "gemini_api_key": "AIzaSyAhLlLIgnFXNwZY5ARLXYvOMsPHvK82X7Q",\n        "p1_gemini_model": "gemini-2.0-flash-exp",\n        "p1_channel_top10": [],\n        "p1_benchmark_channel": {},\n        "p1_search_keywords": []',
        1
    )
    print("[세션스테이트] 초기화 완료!")
else:
    print(f"[세션스테이트] '{init_marker}' 패턴 없음 — 다른 위치 탐색")
    idx = content.find('"youtube_api_key"')
    if idx >= 0:
        print(f"  발견 위치: {content[max(0,idx-20):idx+60]!r}")

# 저장
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
    print(f"COMPILE ERROR: {err[:400]}")
    import re
    match = re.search(r'line (\d+)', err)
    if match:
        err_line = int(match.group(1))
        lines2 = content.split('\n')
        print("에러 주변:")
        for j in range(max(0, err_line-4), min(len(lines2), err_line+4)):
            print(f"  {j+1}: {repr(lines2[j][:90])}")
