with open(r'C:\SageMirror_Production\sage_right_panel_v3.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_render = False

for i, line in enumerate(lines):
    if line.startswith('import streamlit as st'):
        new_lines.append(line)
        new_lines.append('from streamlit_float import *\n')
        continue
    
    if line.startswith('def render_right_panel():'):
        in_render = True
        new_lines.append(line)
        new_lines.append('    float_init()\n')
        continue
    
    if in_render:
        if line.strip() == '_rp_init()':
            new_lines.append('    _rp_init()\n')
            new_lines.append('    panel_container = st.container()\n')
            new_lines.append('    with panel_container:\n')
            continue
        
        # indent if it's inside render_right_panel
        if line.strip() == '':
            new_lines.append('\n')
        elif line.startswith('    '):
            new_lines.append('    ' + line)
        else:
            # this shouldn't happen for a well formatted python file, but just in case
            if line.startswith('#'):
                 new_lines.append('    ' + line)
            else:
                 new_lines.append('    ' + line)
    else:
        new_lines.append(line)

new_lines.append('''
    panel_container.float(
        "position:fixed;right:0;top:0;"
        "width:320px;height:100vh;"
        "overflow-y:auto;background:#0b0b10;"
        "z-index:999;"
        "border-left:1px solid rgba(155,89,182,0.2);"
    )
''')

with open(r'C:\SageMirror_Production\sage_right_panel_v3.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
