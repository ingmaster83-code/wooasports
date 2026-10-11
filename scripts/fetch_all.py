# -*- coding: utf-8 -*-
import urllib.request, urllib.parse, json, time, os

def _need_key():
    import os, sys
    return os.environ.get("DATA_GO_KR_API_KEY") or sys.exit("환경변수 DATA_GO_KR_API_KEY 가 필요합니다(키를 코드에 넣지 마세요).")


KEY = _need_key()
URL = 'https://apis.data.go.kr/B551014/SRVC_SFMS_FACIL_INFO/TODZ_SFMS_FACIL_INFO'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUM_ROWS = 1000

def call(page, retries=3):
    params = {'serviceKey': KEY, 'numOfRows': str(NUM_ROWS), 'pageNo': str(page), 'resultType': 'json'}
    full = URL + '?' + urllib.parse.urlencode(params)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(full, timeout=30) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(3)

first = call(1)
total = first['response']['body']['totalCount']
print(f'총 {total}개, {NUM_ROWS}개씩 {(total // NUM_ROWS) + 1}페이지')

all_items = list(first['response']['body']['items']['item'])
page = 2
while len(all_items) < total:
    data = call(page)
    items = data['response']['body']['items'].get('item', [])
    if not items:
        break
    all_items.extend(items)
    print(f'[{page}] 누적 {len(all_items)}/{total}')
    page += 1
    time.sleep(0.2)

with open(os.path.join(ROOT, '_rawdata', 'raw_facilities.json'), 'w', encoding='utf-8') as f:
    json.dump(all_items, f, ensure_ascii=False)

print(f'완료: {len(all_items)}개 저장')
