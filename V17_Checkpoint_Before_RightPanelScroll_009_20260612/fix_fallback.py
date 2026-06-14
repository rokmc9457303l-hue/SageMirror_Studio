import sys
with open('app_v17_2_3.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

content = content.replace(
    'prompt_key, prompt_title = part_mapping.get(sidebar_part_key, ("base_prompt_rules", "🤖 파트 0 젬마 스튜디오 마스터 프롬프트"))',
    'prompt_key, prompt_title = part_mapping.get(sidebar_part_key, ("p1_master_prompt", "[Part 1] 벤치마킹 & 자료조사 마스터 프롬프트"))'
)

with open('app_v17_2_3.py', 'w', encoding='utf-8-sig') as f:
    f.write(content)
print("Fallback prompt fixed.")
