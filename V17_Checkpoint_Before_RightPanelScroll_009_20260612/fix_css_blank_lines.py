import sys

with open('app_v17_2_3.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# We need to remove all blank lines inside the <style> block of render_right_gemma_panel()
start_idx = content.find('<style>', content.find('def render_right_gemma_panel():'))
end_idx = content.find('</style>', start_idx)

if start_idx != -1 and end_idx != -1:
    style_block = content[start_idx:end_idx]
    # Remove blank lines (lines containing only whitespace)
    new_style_block = '\n'.join([line for line in style_block.split('\n') if line.strip() != ''])
    
    content = content[:start_idx] + new_style_block + content[end_idx:]

with open('app_v17_2_3.py', 'w', encoding='utf-8-sig') as f:
    f.write(content)
print("Removed blank lines from <style> block to fix Markdown parsing leak.")
