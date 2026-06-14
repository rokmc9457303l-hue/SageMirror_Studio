import sys
with open('app_v17_2_3.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

content = content.replace(
    'elif sidebar_part.startswith("파트 1"):   sidebar_part_key = "part1"',
    'if sidebar_part.startswith("파트 1"):   sidebar_part_key = "part1"'
)

with open('app_v17_2_3.py', 'w', encoding='utf-8-sig') as f:
    f.write(content)
print("Syntax error fixed.")
