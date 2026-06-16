import codecs
with codecs.open('app_v17_2_4.py', 'r', 'utf-8') as f:
    in_global = False
    for line in f:
        if 'GLOBAL_CSS =' in line:
            in_global = True
        if in_global:
            print(line.strip())
            if '\"\"\"' in line and not 'GLOBAL_CSS =' in line:
                break
