import os
from docx import Document

file_path = r'C:\SageMirror_Production\raw\추가분\유튜브 영상 기획_ 철학, 심리, 성경 융합.docx'

print(f"📖 대규모 융합 기획안 분석 중 (3MB): {file_path}")

try:
    doc = Document(file_path)
    content = []
    # 3MB 문서는 매우 크므로 상위 500개 문단(약 50~100페이지 분량)을 우선적으로 읽습니다.
    for i, para in enumerate(doc.paragraphs):
        if i > 500: break 
        content.append(para.text)
    
    full_text = "\n".join(content)
    print("\n--- CONTENT START (PARTIAL) ---")
    print(full_text[:3000]) 
    print("--- CONTENT END (PARTIAL) ---\n")
    
    with open(r'C:\SageMirror_Production\raw\fusion_planning_analysis.txt', 'w', encoding='utf-8') as f:
        f.write(full_text)
    print("✅ 분석 완료 및 임시 저장 성공.")
except Exception as e:
    print(f"❌ 에러 발생: {e}")
