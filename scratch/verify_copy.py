import os

files = [
    ('app_v17_1_2.py', 'app_v17_1_3.py'),
    ('sage_popups.py', 'sage_popups_v17_1_3.py')
]

for orig, target in files:
    if not os.path.exists(target):
        print(f"[FAIL] {target} does not exist!")
        continue
    
    with open(orig, 'r', encoding='utf-8', errors='ignore') as f1:
        c1 = f1.read()
    with open(target, 'r', encoding='utf-8', errors='ignore') as f2:
        c2 = f2.read()
        
    l1 = len(c1.splitlines())
    l2 = len(c2.splitlines())
    
    if l1 == l2 and c1 == c2:
        print(f"[OK] {orig} ({l1} lines) -> {target} ({l2} lines) matches perfectly.")
    else:
        print(f"[FAIL] Difference found between {orig} and {target}. lines: {l1} vs {l2}")
