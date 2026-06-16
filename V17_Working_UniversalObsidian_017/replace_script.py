import re

with open('new_top_panel.py', 'r', encoding='utf-8-sig') as f:
    new_func = f.read()

with open('app_v17_2_4.py', 'r', encoding='utf-8-sig') as f:
    original = f.read()

# We know the function starts at "def render_top_panel():" and ends before "# =====================================================================" 
# followed by "# Part 1 엔진 API 로직"
# Let's find the exact indices
start_idx = original.find("def render_top_panel():")
end_idx = original.find("# =====================================================================\n\n# Part 1 엔진 API 로직", start_idx)

if start_idx != -1 and end_idx != -1:
    # replace
    modified = original[:start_idx] + new_func + "\n\n\n" + original[end_idx:]
    with open('app_v17_2_4.py', 'w', encoding='utf-8-sig') as f:
        f.write(modified)
    print("Success: replaced render_top_panel")
else:
    print(f"Error: could not find indices. start: {start_idx}, end: {end_idx}")
