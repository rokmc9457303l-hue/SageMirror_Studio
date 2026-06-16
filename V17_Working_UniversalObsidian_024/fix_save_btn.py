import codecs

with codecs.open('sage_popups_v17_2_4.py', 'r', 'utf-8') as f:
    content = f.read()

target = '''            if "save_workspace_state" in globals():
                save_workspace_state()'''
replacement = '''            _safe_call_app_save_workspace_state()'''

if target in content:
    content = content.replace(target, replacement)
    with codecs.open('sage_popups_v17_2_4.py', 'w', 'utf-8') as f:
        f.write(content)
    print("Fixed save button logic.")
else:
    print("Target not found.")

