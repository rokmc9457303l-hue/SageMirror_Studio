import codecs

with codecs.open('app_v17_2_4.py', 'r', 'utf-8') as f:
    content = f.read()

old_root = '''<style>
:root {{
    --v17-bg: {_bg_color};
    --v17-sidebar: {_sidebar_color};
    --v17-accent: {_accent_color};
    --v17-text: {_text_color};
}}'''

new_root = '''<style>
:root {{
    --v17-bg: {_bg_color};
    --v17-sidebar: {_sidebar_color};
    --v17-accent: {_accent_color};
    --v17-text: {_text_color};
    --v17-btn-bg: {_btn_bg};
    --v17-btn-txt: {_btn_txt};
    --v17-btn-brd: {_btn_brd};
    --v17-btn-edit: {_btn_edit};
    --v17-btn-save: {_btn_save};
    --v17-btn-send: {_btn_send};
    --v17-card-bg: {_card_bg};
    --v17-inp-bg: {_inp_bg};
    --v17-inp-txt: {_inp_txt};
    --v17-pop-bg: {_pop_bg};
    --v17-pop-txt: {_pop_txt};
}}'''

if old_root in content:
    content = content.replace(old_root, new_root)
    with codecs.open('app_v17_2_4.py', 'w', 'utf-8') as f:
        f.write(content)
    print("Fixed root block")
else:
    print("Could not find root block")

