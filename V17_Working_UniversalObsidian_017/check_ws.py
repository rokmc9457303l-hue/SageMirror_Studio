import json

ws_path = r'C:\SageMirror_Production\V17_Working_RightChat_009\workspace_state.json'
with open(ws_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print('--- workspace_state.json keys ---')
print(f'gemini_api_key: bool({bool(data.get("gemini_api_key"))})')
print(f'tavily_api_key: bool({bool(data.get("tavily_api_key"))})')
