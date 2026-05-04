import os

file_path = r'C:\SageMirror_Production\raw\extracted_text.txt'
map_path = r'C:\SageMirror_Production\raw\knowledge_map.txt'

print(f"🗺️ 지식 지도를 그리는 중... ({file_path})")

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        with open(map_path, 'w', encoding='utf-8') as out:
            for i, line in enumerate(f, 1):
                if line.startswith('--- SOURCE:'):
                    out.write(f"Line {i}: {line}")
                    print(f"📍 발견: {line.strip()} (Line {i})")
    print(f"\n✅ 지식 지도가 완성되었습니다: {map_path}")
except Exception as e:
    print(f"❌ 에러 발생: {e}")
