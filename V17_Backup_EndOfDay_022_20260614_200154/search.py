import os
import codecs

keywords1 = ['Episode Control Center', '현자의 거울', "Sage's Mirror", 'MIRROR', '옵시디언 아카이브', 'Obsidian Archive', 'SageMirror_Studio', 'GitHub', 'PAT', 'Tavily API', 'YouTube API', 'Gemini API', 'OpenAI', 'Claude', 'Anthropic', 'Ollama', 'LM Studio', 'Google Drive', 'Docs', 'NotebookLM', 'CapCut', 'theme', 'color', 'sidebar', 'selected_profile', 'profile_name']

keywords2 = ['def render_sidebar', 'def render_left', 'def settings', 'app_settings', 'workspace_state', '.env', 'secrets', 'st.sidebar', 'st.expander', 'st.popover', 'st.text_input', 'st.selectbox']

def search_files(directory, keywords, out_f):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with codecs.open(path, 'r', 'utf-8-sig') as f:
                        lines = f.readlines()
                    for i, line in enumerate(lines):
                        for kw in keywords:
                            if kw.lower() in line.lower():
                                out_f.write(f'{file}:{i+1}: {line.strip()}\n')
                                break
                except Exception as e:
                    pass

with codecs.open('search_results2.txt', 'w', 'utf-8') as out_f:
    out_f.write('--- Search 1 ---\n')
    search_files('.', keywords1, out_f)
    out_f.write('--- Search 2 ---\n')
    search_files('.', keywords2, out_f)
