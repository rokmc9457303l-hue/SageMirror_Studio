from dotenv import load_dotenv
import os

env_path1 = r'C:\SageMirror_Production\V17_Reborn.env'
env_path2 = r'C:\SageMirror_Production\V17_Reborn\.env'
env_path = env_path2 if os.path.exists(env_path2) else env_path1

print(f'Using path: {env_path}')
with open(env_path, 'r', encoding='utf-8') as f:
    content = f.read()

keys = ['GEMINI_API_KEY', 'GOOGLE_API_KEY', 'TAVILY_API_KEY', 'YOUTUBE_API_KEY']
print('\n--- .env file presence ---')
for k in keys:
    print(f'{k}: {k in content}')

load_dotenv(env_path, override=True)
print('\n--- Process loaded ---')
for k in keys:
    print(f'{k.lower()}_loaded: {bool(os.environ.get(k))}')
