import codecs
with codecs.open('sage_config.py', 'r', 'utf-8') as f:
    in_css = False
    for line in f:
        if 'GLOBAL_CSS =' in line:
            in_css = True
        if in_css:
            print(line.strip()[:100])
            if '\"\"\"' in line and not 'GLOBAL_CSS =' in line:
                break
