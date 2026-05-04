import os
from PyPDF2 import PdfReader
from docx import Document

# 경로 설정
raw_dir = r'C:\SageMirror_Production\raw'
output_file = os.path.join(raw_dir, 'extracted_text.txt')

print("🚀 지식 파이프라인 가동 (PDF + Word 통합 추출)...")

with open(output_file, 'w', encoding='utf-8') as out:
    for root, dirs, files in os.walk(raw_dir):
        for file in files:
            file_path = os.path.join(root, file)
            
            # PDF 추출
            if file.lower().endswith('.pdf'):
                try:
                    print(f"📖 PDF 추출 중: {file}")
                    reader = PdfReader(file_path)
                    out.write(f"\n\n--- SOURCE: {file} ---\n")
                    for page in reader.pages:
                        out.write(page.extract_text() + "\n")
                except Exception as e:
                    print(f"❌ PDF 에러 ({file}): {e}")
            
            # Word 추출
            elif file.lower().endswith('.docx'):
                try:
                    print(f"📝 Word 추출 중: {file}")
                    doc = Document(file_path)
                    out.write(f"\n\n--- SOURCE: {file} ---\n")
                    for para in doc.paragraphs:
                        out.write(para.text + "\n")
                except Exception as e:
                    print(f"❌ Word 에러 ({file}): {e}")

print(f"\n✅ 모든 지식이 집결되었습니다: {output_file}")
