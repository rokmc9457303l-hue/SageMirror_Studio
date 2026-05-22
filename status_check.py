import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open(r'C:\SageMirror_Production\app_v15_9_1.py', 'r', encoding='utf-8') as f:
    content = f.read()

print("=== 현재 app_v15_9_1.py 상태 점검 ===")
print(f"[1] 총 줄 수: {len(content.splitlines())}")
print(f"[2] 젬마 어시스턴트 버튼: {content.count('젬마 어시스턴트')}개 (목표: 9)")
print(f"[3] Sage Pop-up 잔존: {content.count('Sage Pop-up')}개 (목표: 0)")
print(f"[4] 파이프라벨 0.82em: {content.count('0.82em')}개 (목표: 1이상)")
print(f"[5] 파이프라벨 0.70em 구버전: {content.count('0.70em')}개 (목표: 0)")
print(f"[6] glass-control-box CSS: {content.count('glass-control-box')}개")
print(f"[7] OBS_RAG_CLICK 버튼 잔존: {content.count('OBS_RAG_CLICK')}개 (미구현)")
print(f"[8] GIT_CLICK 버튼 잔존: {content.count('GIT_CLICK')}개 (미구현)")
print(f"[9] glass-control-box HTML div: {content.count('glass-control-box')}개")

print("")
print("=== 미적용 항목 분석 ===")

# 4가지 주문 중 미완성 확인
not_done = []
if content.count('OBS_RAG_CLICK') > 0:
    not_done.append("주문1: OBS_RAG_CLICK/GIT_CLICK 버튼 → 팝오버 변환 (미완성)")
if 'glass-control-box' not in content or content.count('class="glass-control-box"') == 0:
    not_done.append("주문4: 파트 헤더 우측 3개 위젯 → glass-control-box div 래핑 (HTML 미적용)")
if content.count('0.82em') == 0:
    not_done.append("주문2: 파이프라벨 폰트 확대 (미적용)")
    
for item in not_done:
    print(f"  ❌ {item}")

if not not_done:
    print("  모든 작업 완료!")

# RUN_APP.bat 확인
with open(r'C:\SageMirror_Production\RUN_APP.bat', 'r') as f:
    bat = f.read()
print(f"\n[RUN_APP.bat] 실행 파일: {'app_v15_9_1.py' if 'app_v15_9_1' in bat else 'OLD VERSION!'}")
