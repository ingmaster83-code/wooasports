# -*- coding: utf-8 -*-
import json, re, os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXCLUDE_TYPES = {'간이운동장', '기타시설'}

REGION_SLUGS = {
    '서울특별시': ('서울', 'seoul'),
    '부산광역시': ('부산', 'busan'),
    '대구광역시': ('대구', 'daegu'),
    '인천광역시': ('인천', 'incheon'),
    '대전광역시': ('대전', 'daejeon'),
    '울산광역시': ('울산', 'ulsan'),
    '세종특별자치시': ('세종', 'sejong'),
    '경기도': ('경기', 'gyeonggi'),
    '강원특별자치도': ('강원', 'gangwon'),
    '충청북도': ('충북', 'chungbuk'),
    '충청남도': ('충남', 'chungnam'),
    '전북특별자치도': ('전북', 'jeonbuk'),
    '전남광주통합특별시': ('전남·광주', 'jeonnam-gwangju'),
    '경상북도': ('경북', 'gyeongbuk'),
    '경상남도': ('경남', 'gyeongnam'),
    '제주특별자치도': ('제주', 'jeju'),
}

TYPE_ICONS = {
    '축구장': '⚽', '생활체육관': '🏢', '테니스장': '🎾', '수영장': '🏊',
    '구기체육관': '🏀', '기타체육시설(체력단련장)': '💪', '야구장': '⚾',
    '국궁장': '🏹', '육상경기장': '🏃', '풋살장': '⚽', '롤러스케이트장': '🛼',
    '파크골프장': '⛳', '골프연습장': '⛳', '씨름장': '🤼', '투기체육관': '🥊',
    '골프장': '⛳', '실외인공암벽장': '🧗', '빙상장': '⛸️', '사격장': '🎯',
    '양궁장': '🏹', '승마장': '🐎', '실내인공암벽장': '🧗', '요트장': '⛵',
    '하키장': '🏑', '사이클경기장': '🚴', '조정카누장': '🚣',
    '크로스컨트리': '🎿', '스키점프': '🎿', '바이애슬론': '🎿',
    '전천후게이트볼장': '⚪',
}
TYPE_SLUGS = {
    '축구장': 'soccer', '생활체육관': 'gym', '테니스장': 'tennis', '수영장': 'pool',
    '구기체육관': 'ballgame', '기타체육시설(체력단련장)': 'fitness', '야구장': 'baseball',
    '국궁장': 'archery-kr', '육상경기장': 'track', '풋살장': 'futsal', '롤러스케이트장': 'skate',
    '파크골프장': 'parkgolf', '골프연습장': 'golfrange', '씨름장': 'ssireum', '투기체육관': 'martial',
    '골프장': 'golf', '실외인공암벽장': 'climbing-out', '빙상장': 'skating', '사격장': 'shooting',
    '양궁장': 'archery', '승마장': 'horse', '실내인공암벽장': 'climbing-in', '요트장': 'yacht',
    '하키장': 'hockey', '사이클경기장': 'cycling', '조정카누장': 'canoe',
    '크로스컨트리': 'crosscountry', '스키점프': 'skijump', '바이애슬론': 'biathlon',
    '전천후게이트볼장': 'gateball',
}

def sanitize_slug(s):
    s = (s or '').strip()
    s = re.sub(r'[()]', '-', s)
    s = re.sub(r'[\s/\\:<>"|?*]+', '-', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')

d = json.load(open(os.path.join(ROOT, '_rawdata', 'raw_facilities.json'), encoding='utf-8'))
print('raw:', len(d))

active = [i for i in d if i.get('faci_stat_cd') == '00' and i.get('del_yn') == 'N']
kept = [i for i in active if i.get('ftype_nm') not in EXCLUDE_TYPES and i.get('addr_ctpv_nm') in REGION_SLUGS]
print('active+typed+region:', len(kept))

used_slugs = set()
output = []
for it in kept:
    name = it.get('faci_nm', '').strip()
    if not name:
        continue
    ctpv = it.get('addr_ctpv_nm', '')
    region, region_slug = REGION_SLUGS[ctpv]
    city = it.get('addr_cpb_nm', '')
    ftype = it.get('ftype_nm', '')

    base_slug = sanitize_slug(name) or 'facility'
    slug = base_slug
    n = 2
    while slug in used_slugs:
        slug = f'{base_slug}-{n}'
        n += 1
    used_slugs.add(slug)

    output.append({
        'slug': slug,
        'name': name,
        'ftype': ftype,
        'typeSlug': TYPE_SLUGS.get(ftype, 'etc'),
        'typeIcon': TYPE_ICONS.get(ftype, '🏟️'),
        'region': region,
        'regionSlug': region_slug,
        'city': city,
        'dong': it.get('addr_emd_nm', ''),
        'address': it.get('faci_road_addr', ''),
        'lat': it.get('faci_lat', ''),
        'lng': it.get('faci_lot', ''),
        'phone': it.get('faci_mng_user_telno', ''),
        'mngOrg': it.get('fmng_cpb_nm', ''),
        'mngDept': it.get('fmng_dept_nm', ''),
        'homepage': it.get('faci_homepage', ''),
        'area': it.get('faci_gfa', ''),
        'seatCnt': it.get('stand_seat_cnt', ''),
        'capacity': it.get('stand_cpt_psn_cnt', ''),
        'isNational': it.get('nation_yn', '') == 'Y',
    })

with open(os.path.join(ROOT, '_data', 'facilities.json'), 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=1)

print('final:', len(output))
by_region = Counter(o['regionSlug'] for o in output)
by_type = Counter(o['ftype'] for o in output)
print('regions:', dict(by_region))
print('types:', len(by_type))
