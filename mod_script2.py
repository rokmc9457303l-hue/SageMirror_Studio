import re
import os

with open('app_v17_1_26.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Remove the import block
text = re.sub(r'from sage_popups_v17_1_22 import \([\s\S]*?\)', '', text)

# 2. Replace the function calls with pass
text = text.replace('popup_assistant()', 'pass')
text = text.replace('popup_edit_obsidian()', 'pass')
text = text.replace('popup_edit_prompt()', 'pass')

# 3. Wrap the routing block
routing_start_str = 'if part.startswith("파트 0"):'
routing_end_str = 'render_right_panel()'

start_idx = text.find(routing_start_str)
end_idx = text.find(routing_end_str)

if start_idx != -1 and end_idx != -1:
    # get the text to wrap (from start_idx to the end of end_idx's line)
    end_line_idx = text.find('\n', end_idx)
    if end_line_idx == -1:
        end_line_idx = len(text)
        
    block = text[start_idx:end_line_idx]
    
    # Indent the block by 4 spaces
    indented_block = '\n'.join('    ' + line if line.strip() else line for line in block.split('\n'))
    
    wrapper = 'col_main, col_gemma = st.columns([7, 3])\nwith col_gemma:\n    st.subheader("🤖 젬마 어시스턴트")\nwith col_main:\n'
    
    new_block = wrapper + indented_block
    
    text = text[:start_idx] + new_block + text[end_line_idx:]

with open('app_v17_1_26_mod2.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Modification done!")
