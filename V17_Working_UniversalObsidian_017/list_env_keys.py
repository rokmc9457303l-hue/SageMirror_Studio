env_path = r'C:\SageMirror_Production\V17_Reborn\.env'
with open(env_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'): continue
        if '=' in line:
            print(line.split('=')[0].strip())
