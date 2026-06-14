from dotenv import load_dotenv
import os

env_path = r'C:\SageMirror_Production\V17_Reborn.env'
# It seems sage_config.py loads C:\SageMirror_Production\V17_Reborn\.env (with a dot before env)
# Let's check both paths.
with open(env_path, 'r', encoding='utf-8') as f:
    content = f.read()

keys = ['GEMINI_API_KEY', 'GOOGLE_API_KEY', 'TAVILY_API_KEY', 'YOUTUBE_API_KEY']
print('--- .env file presence ---')
for k in keys:
    print(f'{k}: {k in content}')

load_dotenv(env_path, override=True)
print('\n--- Process loaded ---')
for k in keys:
    print(f'{k.lower()}_loaded: {bool(os.environ.get(k))}')
