import os
from docx import Document

file_path = r'C:\SageMirror_Production\raw\추가분\오디시언  지식  구조화 프롬프트.docx'

print(f"📖 마스터 프롬프트 분석 중: {file_path}")

try:
    doc = Document(file_path)
    content = []
    for para in doc.paragraphs:
        content.append(para.text)
    
    full_text = "\n".join(content)
    print("\n--- CONTENT START ---")
    print(full_text)
    print("--- CONTENT END ---\n")
    
    # 분석 결과를 임시 파일로 저장하여 제가 정독할 수 있게 합니다.
    with open(r'C:\SageMirror_Production\raw\master_prompt_analysis.txt', 'w', encoding='utf-8') as f:
        f.write(full_text)
    print("✅ 분석 완료 및 임시 저장 성공.")
except Exception as e:
    print(f"❌ 에러 발생: {e}")
