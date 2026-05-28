import sys
sys.stdout.reconfigure(encoding="utf-8")
fp = r"C:\SageMirror_Production\sage_popups.py"
with open(fp, "r", encoding="utf-8") as f:
    content = f.read()
old = '''                    try:
                        full_response = run_agent_loop(
                            question=q_stream,
                            sys_ctx=sys_ctx,
                            model=current_model,
                            part_key=current_part_key,
                            max_iterations=4,
                            stream_placeholder=ans_placeholder,
                            status_widget=status_widget,
                        )'''
new = '''                    try:
                        if _current_mode == "A":
                            full_response = call_gemma(q_stream, system=sys_ctx, model=current_model)
                            ans_placeholder.markdown(full_response)
                        else:
                            full_response = run_agent_loop(
                                question=q_stream,
                                sys_ctx=sys_ctx,
                                model=current_model,
                                part_key=current_part_key,
                                max_iterations=4,
                                stream_placeholder=ans_placeholder,
                                status_widget=status_widget,
                            )'''
if old in content:
    content = content.replace(old, new, 1)
    with open(fp, "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS")
else:
    print("ERROR: 찾지 못함")
