import codecs

with codecs.open('sage_popups_v17_2_4.py', 'r', 'utf-8') as f:
    content = f.read()

# Fix color picker default values to be valid HEX
content = content.replace('value=app_settings.get("button_background_color", "transparent")', 'value=app_settings.get("button_background_color", "#1E293B")')
content = content.replace('value=app_settings.get("button_border_color", "rgba(184, 134, 11, 0.4)")', 'value=app_settings.get("button_border_color", "#B8860B")')
content = content.replace('value=app_settings.get("card_background_color", "rgba(30,41,59,0.45)")', 'value=app_settings.get("card_background_color", "#1E293B")')
content = content.replace('value=app_settings.get("input_background_color", "rgba(15,23,42,0.6)")', 'value=app_settings.get("input_background_color", "#0F172A")')

with codecs.open('sage_popups_v17_2_4.py', 'w', 'utf-8') as f:
    f.write(content)
print("Updated sage_popups_v17_2_4.py")

with codecs.open('app_v17_2_4.py', 'r', 'utf-8') as f:
    content_app = f.read()

content_app = content_app.replace('_app_settings.get("button_background_color", "transparent")', '_app_settings.get("button_background_color", "#1E293B")')
content_app = content_app.replace('_app_settings.get("button_border_color", "rgba(184, 134, 11, 0.4)")', '_app_settings.get("button_border_color", "#B8860B")')
content_app = content_app.replace('_app_settings.get("card_background_color", "rgba(30,41,59,0.45)")', '_app_settings.get("card_background_color", "#1E293B")')
content_app = content_app.replace('_app_settings.get("input_background_color", "rgba(15,23,42,0.6)")', '_app_settings.get("input_background_color", "#0F172A")')

with codecs.open('app_v17_2_4.py', 'w', 'utf-8') as f:
    f.write(content_app)
print("Updated app_v17_2_4.py")
