# -*- coding: utf-8 -*-
"""버튼 명칭 교체 스크립트"""

target_file = r'C:\SageMirror_Production\app_v15_9_1.py'

with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

old_text = '\u00f0\u009f\u00a4\u0096 Sage Pop-up'
new_text = '\U0001f916 젬마 어시스턴트'

# 실제 원본 문자열로 검색
import re
old_pattern = '"🤖 Sage Pop-up"'
new_pattern = '"🤖 젬마 어시스턴트"'

count = content.count(old_pattern)
print(f'Found: {count} occurrences of old text')

content_new = content.replace(old_pattern, new_pattern)
count2 = content_new.count('젬마 어시스턴트')
print(f'After replace: {count2} occurrences of new text')

with open(target_file, 'w', encoding='utf-8') as f:
    f.write(content_new)

print('File saved successfully!')
