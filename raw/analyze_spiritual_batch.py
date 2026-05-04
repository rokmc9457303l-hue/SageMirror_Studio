import os
from docx import Document

files_to_analyze = [
    '2_기도_유튜브_콘텐츠.docx',
    '3_위로와희망_유튜브_콘텐츠.docx',
    '4_경고와깨달음_유튜브_콘텐츠.docx',
    '5_믿음성장_유튜브_콘텐츠.docx'
]

base_path = r'C:\SageMirror_Production\raw\추가분'

print("🌪️ 영성 콘텐츠 통합 분석 및 아카이빙 시작...")

all_content = ""

for file_name in files_to_analyze:
    file_path = os.path.join(base_path, file_name)
    try:
        print(f"📖 분석 중: {file_name}")
        doc = Document(file_path)
        all_content += f"\n\n--- SOURCE: {file_name} ---\n"
        for para in doc.paragraphs:
            all_content += para.text + "\n"
    except Exception as e:
        print(f"❌ 에러 발생 ({file_name}): {e}")

# 통합 분석 결과 저장
output_path = r'C:\SageMirror_Production\raw\spiritual_contents_analysis.txt'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(all_content)

print(f"\n✅ 분석 완료: {output_path}")
