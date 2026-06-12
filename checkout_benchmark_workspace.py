import os
import shutil
from pathlib import Path
import json

source_dir = Path(r"C:\SageMirror_Production\V17_Completed_RightResearchPanel_UICheckpoint_001_20260610")
base_target = r"C:\SageMirror_Production\V17_Working_Part1Benchmark_{:03d}"

idx = 1
while True:
    target_dir = Path(base_target.format(idx))
    if not target_dir.exists():
        break
    idx += 1

def ignore_forbidden(dir, contents):
    forbidden = {
        '.env', 'local_secrets.json', 'google_token.json', 
        'credentials.json', 'client_secret.json', '__pycache__'
    }
    ignore_list = [c for c in contents if c in forbidden or c.endswith('.env') or c.endswith('.token') or c.endswith('.key') or c.endswith('.pem') or c.endswith('.pyc')]
    return ignore_list

shutil.copytree(source_dir, target_dir, ignore=ignore_forbidden)

# Clear any remaining pyc or pycache
for r, dirs, files in os.walk(target_dir, topdown=False):
    for name in files:
        if name.endswith('.pyc') or name.endswith('.token') or name.endswith('.key') or name.endswith('.pem') or name.endswith('.env'):
            os.remove(os.path.join(r, name))
    for name in dirs:
        if name == '__pycache__':
            shutil.rmtree(os.path.join(r, name))

with open('checkout_report2.json', 'w', encoding='utf-8') as f:
    json.dump({"source": str(source_dir), "target": str(target_dir)}, f)

print(f"Checkout completed to {target_dir}")
