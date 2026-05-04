import os
from docx import Document

file_path = r'C:\SageMirror_Production\raw\추가분\기독교 유튜브 콘텐츠 생성기 (묵상_기도문_말씀_위로).docx'

print(f"📖 마스터 생성기 분석 중: {file_path}")

try:
    doc = Document(file_path)
    content = []
    for para in doc.paragraphs:
        content.append(para.text)
    
    full_text = "\n".join(content)
    print("\n--- CONTENT START ---")
    print(full_text[:3000]) # 생성기 로직은 길 수 있으므로 더 많이 출력
    print("--- CONTENT END ---\n")
    
    with open(r'C:\SageMirror_Production\raw\christian_generator_analysis.txt', 'w', encoding='utf-8') as f:
        f.write(full_text)
    print("✅ 분석 완료 및 임시 저장 성공.")
except Exception as e:
    print(f"❌ 에러 발생: {e}")
