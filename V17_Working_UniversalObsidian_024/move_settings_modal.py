import codecs

with codecs.open('sage_popups_v17_2_4.py', 'r', 'utf-8') as f:
    content = f.read()

# I need to extract the entire popup_settings_modal() block and put it AFTER popup_edit_obsidian()
import re
# Find the exact block we inserted
match = re.search(r'(@st\.dialog\("⚙️ 설정"\)\ndef popup_settings_modal\(\):.*?st\.write\("- Agent ON/OFF 설정"\))', content, re.DOTALL)
if match:
    settings_modal_code = match.group(1)
    # Remove it from its current position
    content = content.replace(settings_modal_code + '\n\n', '')
    content = content.replace(settings_modal_code + '\n', '')
    content = content.replace(settings_modal_code, '')
    
    # Now find the end of popup_edit_obsidian()
    # It ends at:
    #         use_container_width=True, key="ob_dl",
    #     )
    end_obsidian = '        use_container_width=True, key="ob_dl",\n    )'
    if end_obsidian in content:
        # Insert settings_modal_code after it
        content = content.replace(end_obsidian, end_obsidian + '\n\n\n' + settings_modal_code + '\n')
        
        with codecs.open('sage_popups_v17_2_4.py', 'w', 'utf-8') as f:
            f.write(content)
        print("Moved popup_settings_modal down successfully.")
    else:
        print("Could not find end of popup_edit_obsidian.")
else:
    print("Could not find popup_settings_modal.")

