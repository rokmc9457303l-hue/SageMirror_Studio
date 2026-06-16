import os

def replace_functions():
    app_path = "app_v17_2_4.py"
    with open(app_path, "r", encoding="utf-8-sig") as f:
        original = f.read()
        
    with open("new_top_panel.py", "r", encoding="utf-8-sig") as f:
        new_top = f.read()
        
    with open("new_right_panel.py", "r", encoding="utf-8-sig") as f:
        new_right = f.read()

    # Replace render_top_panel
    top_start = original.find("def render_top_panel():")
    top_end = original.find("# =====================================================================\n\n# Part 1 엔진 API 로직", top_start)
    if top_start != -1 and top_end != -1:
        original = original[:top_start] + new_top + "\n\n\n" + original[top_end:]
    else:
        print("Error: render_top_panel boundaries not found.")
        return

    # Replace render_right_gemma_panel
    right_start = original.find("def render_right_gemma_panel():")
    # Finding the end of render_right_gemma_panel
    # It ends when "# =====================================================================" is found
    # after right_start
    right_end = original.find("# =====================================================================", right_start)
    if right_start != -1 and right_end != -1:
        original = original[:right_start] + new_right + "\n\n\n" + original[right_end:]
    else:
        print("Error: render_right_gemma_panel boundaries not found.")
        return

    with open(app_path, "w", encoding="utf-8-sig") as f:
        f.write(original)
        
    print("Success: replaced both functions.")

if __name__ == "__main__":
    replace_functions()
