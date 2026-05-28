import os

files = [
    ('app_v17_1_2.py', r'00_History\app_v17_1_2_backup_before_v17_1_3_20260529_0226.py'),
    ('sage_popups.py', r'00_History\sage_popups_backup_before_v17_1_3_20260529_0226.py'),
]
for orig, bak in files:
    with open(orig, 'rb') as f:
        oc = f.read().count(b'\n')
    with open(bak, 'rb') as f:
        bc = f.read().count(b'\n')
    status = 'OK' if oc == bc else 'MISMATCH'
    print(f'[{status}] {orig}: {oc}줄 vs 백업: {bc}줄')

sess = r'C:\SageMirror_Outputs\00_Session_States'
for fn in ['popup_chat_EP001.json', 'workspace_state_EP001.json']:
    fp = os.path.join(sess, fn)
    print(f'[세션] {fn}: {"존재" if os.path.exists(fp) else "없음"}')
