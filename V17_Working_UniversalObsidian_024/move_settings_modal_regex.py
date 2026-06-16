import codecs
import re

with codecs.open('sage_popups_v17_2_4.py', 'r', 'utf-8') as f:
    content = f.read()

match = re.search(r'(@st\.dialog\("⚙️ 설정"\)\ndef popup_settings_modal\(\):.*?st\.write\("- Agent ON/OFF 설정"\))', content, re.DOTALL)
if match:
    settings_modal_code = match.group(1)
    # Remove it from its current position
    content = content.replace(settings_modal_code + '\n\n', '')
    content = content.replace(settings_modal_code + '\n', '')
    content = content.replace(settings_modal_code, '')
    
    # Use regex to find the end of the obsidian edit popup
    end_obsidian_regex = r'(use_container_width=True, key="ob_dl",\s*\n\s*\))'
    match_end = re.search(end_obsidian_regex, content)
    if match_end:
        end_obsidian = match_end.group(1)
        # Insert settings_modal_code after it
        content = content.replace(end_obsidian, end_obsidian + '\n\n\n' + settings_modal_code + '\n')
        
        with codecs.open('sage_popups_v17_2_4.py', 'w', 'utf-8') as f:
            f.write(content)
        print("Moved popup_settings_modal down successfully.")
    else:
        print("Could not find end of popup_edit_obsidian.")
else:
    print("Could not find popup_settings_modal.")

