import sys, io, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

target_file = r'C:\SageMirror_Production\app_v15_9_2.py'

with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. init_session_state 의 defaults 딕셔너리에 추가
old_defaults_target = '"tavily_api_key": "",'
new_defaults_target = (
    '"tavily_api_key": "",\n'
    '        "youtube_api_key": "",\n'
    '        "gemini_api_key": "AIzaSyAhLlLIgnFXNwZY5ARLXYvOMsPHvK82X7Q",\n'
    '        "p1_gemini_model": "gemini-2.0-flash-exp",\n'
    '        "p1_channel_top10": [],\n'
    '        "p1_benchmark_channel": {},\n'
    '        "p1_search_keywords": [],'
)

if old_defaults_target in content:
    content = content.replace(old_defaults_target, new_defaults_target)
    print("defaults 딕셔너리에 Gemini 키 추가 완료!")
else:
    print("defaults 타겟 문자열 찾지 못함!")

# 2. save_workspace_state 의 keys_to_save 리스트에 추가
old_keys_target = '"tavily_api_key", "youtube_api_key",'
new_keys_target = (
    '"tavily_api_key", "youtube_api_key", "gemini_api_key", "p1_gemini_model", '
    '"p1_channel_top10", "p1_benchmark_channel", "p1_search_keywords",'
)

if old_keys_target in content:
    content = content.replace(old_keys_target, new_keys_target)
    print("keys_to_save 리스트에 Gemini 키 추가 완료!")
else:
    print("keys_to_save 타겟 문자열 찾지 못함!")

# 저장 및 컴파일 검증
with open(target_file, 'w', encoding='utf-8') as f:
    f.write(content)

result = subprocess.run(
    ['C:\\Python314\\python.exe', '-m', 'py_compile', target_file],
    capture_output=True, text=True, encoding='utf-8', errors='replace'
)
if result.returncode == 0:
    print("COMPILE: ✅ OK!")
else:
    print(f"COMPILE ERROR:\n{result.stderr}")
