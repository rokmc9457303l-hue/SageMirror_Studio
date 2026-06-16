with open('app_v17_2_3.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_call = '_save_raw_wiki(last_success_msg["content"], category=cat, custom_filename=f"research_{ts}")'
new_call = '_save_raw_wiki(last_success_msg["content"], title=f"Research_{ts}", source_type="RightResearch", part_key="part0", model_name=last_success_msg["engine"])'

if old_call in text:
    text = text.replace(old_call, new_call)
    with open('app_v17_2_3.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Fixed!")
else:
    print("Could not find the old call.")
