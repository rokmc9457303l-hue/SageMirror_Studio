import sys
import os
sys.path.append(r'C:\SageMirror_Production\V17_Working_RightChat_003')

from dotenv import load_dotenv
load_dotenv(r'C:\SageMirror_Production\V17_Reborn\.env', override=False)

from app_v17_2_3 import run_right_research_engine

# 1. Gemini without Key
res_gm = run_right_research_engine('gemini-2.5-flash', '안녕')
print('Gemini Result:', res_gm['error_message'])

# 2. Tavily without Key
res_tv = run_right_research_engine('Tavily 웹 검색', '안녕')
print('Tavily Result:', res_tv['error_message'])

# 3. Simulate Obsidian Save
import datetime
from sage_popups_v17_2_3 import _save_raw_wiki
ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
cat = 'RightResearch'
content = '정상 리서치 결과 시뮬레이션입니다.'

_save_raw_wiki(content, title=f'Research_{ts}', source_type='RightResearch', part_key='part0', model_name='gemini-2.5-flash')

base_dir = r'C:\SageMirror_Production\00_Obsidian'
import glob
print('Raw created:', bool(glob.glob(os.path.join(base_dir, '00_Raw', f'*Research_{ts}*'))))
print('Wiki created:', bool(glob.glob(os.path.join(base_dir, '01_Wiki', f'*Research_{ts}*'))))
print('Schema created:', bool(glob.glob(os.path.join(base_dir, '02_Schema', f'*Research_{ts}*'))))
