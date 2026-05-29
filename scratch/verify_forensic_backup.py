import os

files = [
    ('app_v17_1_3.py', r'00_History\app_v17_1_3_backup_before_v17_1_4A_20260529_0255.py'),
    ('sage_popups_v17_1_3.py', r'00_History\sage_popups_v17_1_3_backup_before_v17_1_4A_20260529_0255.py'),
    ('RUN_APP.bat', r'00_History\RUN_APP_backup_before_v17_1_4A_20260529_0255.bat'),
    ('RUN_DEBUG.bat', r'00_History\RUN_DEBUG_backup_before_v17_1_4A_20260529_0255.py'), # bat 이지만 복사 검증
    ('RUN_APP.vbs', r'00_History\RUN_APP_backup_before_v17_1_4A_20260529_0255.vbs'),
]

for orig, bak in files:
    # RUN_DEBUG.bat 백업 명칭 정정
    if 'RUN_DEBUG' in orig:
        bak = r'00_History\RUN_DEBUG_backup_before_v17_1_4A_20260529_0255.bat'
        
    if not os.path.exists(bak):
        print(f"[FAIL] {bak} not found!")
        continue
    with open(orig, 'r', encoding='utf-8', errors='ignore') as f1:
        c1 = f1.read()
    with open(bak, 'r', encoding='utf-8', errors='ignore') as f2:
        c2 = f2.read()
    l1 = len(c1.splitlines())
    l2 = len(c2.splitlines())
    if l1 == l2 and c1 == c2:
        print(f"[OK] {orig} ({l1} lines) matches backup exactly.")
    else:
        print(f"[FAIL] {orig} line mismatch: {l1} vs {l2}")
