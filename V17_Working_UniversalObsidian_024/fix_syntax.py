import codecs

with codecs.open('app_v17_2_4.py', 'r', 'utf-8') as f:
    content = f.read()

# Remove the bad injection
bad_inject = '''                import streamlit as st
from ui.research_campus import render_research_campus'''
content = content.replace(bad_inject, '                import streamlit as st')

# Add the proper import at the top
content = 'from ui.research_campus import render_research_campus\n' + content

with codecs.open('app_v17_2_4.py', 'w', 'utf-8') as f:
    f.write(content)
print("Fixed syntax error")
