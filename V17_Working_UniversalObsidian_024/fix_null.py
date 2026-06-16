import sys

try:
    with open('app_v17_2_4.py', 'rb') as f:
        content = f.read()
    
    if b'\x00' in content:
        content = content.replace(b'\x00', b'')
        with open('app_v17_2_4.py', 'wb') as f:
            f.write(content)
        print("Null bytes removed.")
    else:
        print("No null bytes found.")
except Exception as e:
    print(f"Error: {e}")
