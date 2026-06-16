import codecs
with codecs.open('app_v17_2_4.py', 'r', 'utf-8') as f:
    content = f.read()
content = content.replace('popup_edit_obsidian, popup_edit_prompt, popup_assistant,', 'popup_edit_obsidian, popup_edit_prompt, popup_assistant, popup_settings_modal,')
with codecs.open('app_v17_2_4.py', 'w', 'utf-8') as f:
    f.write(content)
