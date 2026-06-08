import re
with open('app_v17_1_26.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
in_import = False
start_routing = -1
end_routing = -1

for i, line in enumerate(lines):
    if 'from sage_popups_v17_1_22 import' in line:
        in_import = True
        continue
    if in_import:
        if ')' in line:
            in_import = False
        continue
    
    if 'popup_assistant()' in line:
        line = line.replace('popup_assistant()', 'pass')
    if 'popup_edit_obsidian()' in line:
        line = line.replace('popup_edit_obsidian()', 'pass')
    if 'popup_edit_prompt()' in line:
        line = line.replace('popup_edit_prompt()', 'pass')
        
    if line.startswith('if part.startswith("파트 0"):') and start_routing == -1:
        start_routing = i
        
    if line.startswith('render_right_panel()'):
        end_routing = i
        
    out.append(line)

# Now we need to indent the lines from start_routing to end_routing (inclusive) and wrap with st.columns
if start_routing != -1:
    new_out = out[:start_routing]
    new_out.append('col_main, col_gemma = st.columns([7, 3])\n')
    new_out.append('with col_gemma:\n')
    new_out.append('    st.subheader("🤖 젬마 어시스턴트")\n')
    new_out.append('with col_main:\n')
    
    # Indent everything from start_routing to end_routing (inclusive)
    for i in range(start_routing, end_routing + 1):
        # don't indent empty lines
        if out[i].strip():
            new_out.append('    ' + out[i])
        else:
            new_out.append(out[i])
            
    # Add the rest of the lines
    new_out.extend(out[end_routing + 1:])
    out = new_out

with open('app_v17_1_26_mod.py', 'w', encoding='utf-8') as f:
    f.writelines(out)

print(f'Routing starts at: {start_routing}, ends at: {end_routing}')
