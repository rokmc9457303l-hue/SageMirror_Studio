import os
from docx import Document

file_path = r'C:\SageMirror_Production\raw\추가분\2_하나님메시지.docx'

print(f"📖 하나님 메시지 원문 분석 중: {file_path}")

try:
    doc = Document(file_path)
    content = []
    for para in doc.paragraphs:
        content.append(para.text)
    
    full_text = "\n".join(content)
    print("\n--- CONTENT START ---")
    print(full_text[:2000]) 
    print("--- CONTENT END ---\n")
    
    with open(r'C:\SageMirror_Production\raw\god_message_original_analysis.txt', 'w', encoding='utf-8') as f:
        f.write(full_text)
    print("✅ 분석 완료 및 임시 저장 성공.")
except Exception as e:
    print(f"❌ 에러 발생: {e}")
