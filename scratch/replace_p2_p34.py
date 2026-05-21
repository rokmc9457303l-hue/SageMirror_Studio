import sys

def main():
    target_file = r"C:\SageMirror_Production\app_v13_28.py"
    new_p2_research_tab_file = r"C:\SageMirror_Production\scratch\p2_research_tab.txt"
    new_p2_plan_tab_file = r"C:\SageMirror_Production\scratch\p2_plan_tab.txt"
    new_p34_step3_file = r"C:\SageMirror_Production\scratch\p34_step3_tabs.txt"

    with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    with open(new_p2_research_tab_file, "r", encoding="utf-8") as f:
        p2_research_new = f.read()
    with open(new_p2_plan_tab_file, "r", encoding="utf-8") as f:
        p2_plan_new = f.read()
    with open(new_p34_step3_file, "r", encoding="utf-8") as f:
        p34_step3_new = f.read()

    lines = content.splitlines()
    n = len(lines)

    # 1) Part 3-4 Step 3 탭 교체 범위 탐색
    # 시작: c_narr, c_img, c_cap = st.columns(3
    p34_step3_start = -1
    for i, line in enumerate(lines):
        if "c_narr, c_img, c_cap = st.columns(3" in line:
            p34_step3_start = i
            break

    # 종료: st.divider() 바로 위에 있는 마지막 'with c_cap:' 블록 다음
    # 전체 대본 옵시디언 자동 백업 버튼 라인 탐색
    p34_step3_end = -1
    for i in range(p34_step3_start + 1, n):
        if "Part 3-4" in lines[i] and "button" in lines[i] and "backup" in lines[i].lower():
            p34_step3_end = i - 2
            break

    # 2) Part 2 research 탭 교체 범위 탐색
    p2_research_start = -1
    for i, line in enumerate(lines):
        if "with tab_research:" in line and 2300 < i < 2600:
            p2_research_start = i
            break

    # 종료: @st.dialog("[TARGET] 이미지 파트 마스터 프롬프트 편집" 직전
    p2_end = -1
    for i, line in enumerate(lines):
        if '@st.dialog("[TARGET]' in line and '이미지 파트' in line:
            p2_end = i
            break

    if p34_step3_start == -1:
        print(f"Error: Part3-4 Step3 columns not found (searched c_narr,c_img,c_cap)")
        sys.exit(1)
    if p34_step3_end == -1:
        print(f"Error: Part3-4 Step3 end not found")
        sys.exit(1)
    if p2_research_start == -1:
        print(f"Error: Part2 research tab not found")
        sys.exit(1)
    if p2_end == -1:
        print(f"Error: Part2 end marker not found")
        sys.exit(1)

    print(f"Part3-4 Step3: lines {p34_step3_start+1} ~ {p34_step3_end+1}")
    print(f"Part2 research tab: lines {p2_research_start+1} ~ {p2_end}")

    # 교체 순서: 뒤쪽부터 교체해야 라인번호가 안 밀림
    # A) Part 3-4 Step 3 먼저 교체 (더 뒤에 있음)
    updated = lines[:p34_step3_start] + [p34_step3_new] + lines[p34_step3_end+1:]

    # B) Part 2 research+plan 탭 교체 (앞에 있음)
    # Part 2 search 위치 재탐색 (A 교체 후 라인번호가 달라졌으므로)
    p2_research_start2 = -1
    for i, line in enumerate(updated):
        if "with tab_research:" in line and 2300 < i < 2600:
            p2_research_start2 = i
            break

    p2_end2 = -1
    for i, line in enumerate(updated):
        if '@st.dialog("[TARGET]' in line and '이미지 파트' in line:
            p2_end2 = i
            break

    if p2_research_start2 == -1 or p2_end2 == -1:
        print(f"Error: Part2 markers not found after Step3 replacement (p2_research_start2={p2_research_start2}, p2_end2={p2_end2})")
        sys.exit(1)

    print(f"Part2 (after step3 fix): research tab lines {p2_research_start2+1} ~ {p2_end2}")
    final = updated[:p2_research_start2] + [p2_research_new + "\n" + p2_plan_new] + updated[p2_end2:]

    line_ending = "\r\n" if "\r\n" in content else "\n"
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(line_ending.join(final))

    print("SUCCESS: Part2 + Part3-4 Step3 all replaced!")

if __name__ == "__main__":
    main()
