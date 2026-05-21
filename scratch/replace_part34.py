import sys

def main():
    target_file = r"C:\SageMirror_Production\app_v13_27.py"
    new_code_file = r"C:\SageMirror_Production\scratch\part34_new_steps.txt"

    with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    with open(new_code_file, "r", encoding="utf-8") as f:
        new_code = f.read()

    lines = content.splitlines()

    step2_start = -1
    for i, line in enumerate(lines):
        if "Step 2. Architect" in line and "subheader" in line:
            step2_start = i
            break

    routing_start = -1
    for i, line in enumerate(lines):
        if "# 파트 라우팅 블록" in line:
            routing_start = i
            break

    if step2_start == -1 or routing_start == -1:
        print(f"Error: range not found (step2_start={step2_start}, routing_start={routing_start})")
        sys.exit(1)

    print(f"Replacing lines {step2_start+1} to {routing_start}")

    line_ending = "\r\n" if "\r\n" in content else "\n"
    updated_lines = lines[:step2_start] + [new_code] + lines[routing_start:]

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(line_ending.join(updated_lines))

    print("SUCCESS: Part34 Step2+3 replaced!")

if __name__ == "__main__":
    main()
