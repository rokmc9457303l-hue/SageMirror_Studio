import os

keys = ['GEMINI_API_KEY', 'GOOGLE_API_KEY', 'TAVILY_API_KEY', 'YOUTUBE_API_KEY']
print('--- Current Windows Env ---')
for k in keys:
    print(f'{k.lower()}_loaded: {bool(os.environ.get(k))}')
