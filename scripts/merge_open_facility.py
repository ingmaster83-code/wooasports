# -*- coding: utf-8 -*-
"""
전국공공시설개방정보표준데이터(data.go.kr 15013117)를 기존 facilities.json에 병합.
- 회의실/강의실/강당류(체육시설 아님)는 제외
- 캠핑장은 wooacamp와 겹치므로 제외
- 매칭되면 기존 시설에 요금/운영시간/휴관일/사진/신청방법 등을 보강
- 매칭 안 되는 신규 체육시설(농구장/배드민턴장/족구장/배구장/탁구장/볼링장 등)은 새 시설로 추가
"""
import json, re, os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REGION_SLUGS = {
    '서울특별시': ('서울', 'seoul'), '서울시': ('서울', 'seoul'),
    '부산광역시': ('부산', 'busan'),
    '대구광역시': ('대구', 'daegu'),
    '인천광역시': ('인천', 'incheon'),
    '대전광역시': ('대전', 'daejeon'),
    '울산광역시': ('울산', 'ulsan'),
    '세종특별자치시': ('세종', 'sejong'),
    '경기도': ('경기', 'gyeonggi'),
    '강원특별자치도': ('강원', 'gangwon'), '강원도': ('강원', 'gangwon'),
    '충청북도': ('충북', 'chungbuk'),
    '충청남도': ('충남', 'chungnam'),
    '전북특별자치도': ('전북', 'jeonbuk'), '전라북도': ('전북', 'jeonbuk'),
    '전라남도': ('전남·광주', 'jeonnam-gwangju'), '광주광역시': ('전남·광주', 'jeonnam-gwangju'),
    '전남광주통합특별시': ('전남·광주', 'jeonnam-gwangju'),
    '경상북도': ('경북', 'gyeongbuk'),
    '경상남도': ('경남', 'gyeongnam'),
    '제주특별자치도': ('제주', 'jeju'),
}

# 개방시설유형구분 -> (ftype 라벨, typeSlug, typeIcon). None이면 체육시설 아님(제외).
TYPE_MAP = {
    '체육관': ('생활체육관', 'gym', '🏢'),
    '축구장': ('축구장', 'soccer', '⚽'),
    '다목적경기장': ('다목적경기장', 'multipurpose', '🏟️'),
    '테니스장': ('테니스장', 'tennis', '🎾'),
    '풋살경기장': ('풋살장', 'futsal', '⚽'),
    '족구장': ('족구장', 'jokgu', '🏐'),
    '야구장': ('야구장', 'baseball', '⚾'),
    '농구장': ('농구장', 'basketball', '🏀'),
    '배드맨턴장': ('배드민턴장', 'badminton', '🏸'),
    '배드민턴장': ('배드민턴장', 'badminton', '🏸'),
    '골프장': ('골프장', 'golf', '⛳'),
    '배구장': ('배구장', 'volleyball', '🏐'),
    '기타(게이트볼장)': ('전천후게이트볼장', 'gateball', '⚪'),
    '기타(파크골프장)': ('파크골프장', 'parkgolf', '⛳'),
    '기타(수영장)': ('수영장', 'pool', '🏊'),
    '기타(탁구장)': ('탁구장', 'pingpong', '🏓'),
    '기타(헬스장)': ('기타체육시설(체력단련장)', 'fitness', '💪'),
    '기타(볼링장)': ('볼링장', 'bowling', '🎳'),
}
EXCLUDE_EXACT = {'캠핑장'}  # wooacamp 영역이라 제외

def sanitize_slug(s):
    s = (s or '').strip()
    s = re.sub(r'[()]', '-', s)
    s = re.sub(r'[\s/\\:<>"|?*]+', '-', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')

def norm_name(s):
    s = (s or '').strip()
    s = re.sub(r'\s+', '', s)
    s = re.sub(r'[()]', '', s)
    return s

def find_region(addr):
    for full, pair in REGION_SLUGS.items():
        if addr.startswith(full):
            return pair
    return None, None

def parse_fee(row):
    if row.get('PCHRG_USE_YN') != 'Y':
        return '무료'
    fee = (row.get('RNTFEE') or '').strip()
    unit = (row.get('USE_STDR_TIME') or '').strip()
    if not fee:
        return ''
    if fee.isdigit() and unit.isdigit():
        return f'{int(fee):,}원 / {unit}시간'
    return fee  # 복잡한 요금체계(문자열)는 그대로 저장

def build_open_fields(row):
    return {
        'closedDays': (row.get('RSTDE') or '').strip(),
        'weekdayOpen': (row.get('WEEKDAY_OPER_OPEN_HHMM') or '').strip(),
        'weekdayClose': (row.get('WEEKDAY_OPER_COLSE_HHMM') or '').strip(),
        'weekendOpen': (row.get('WKEND_OPER_OPEN_HHMM') or '').strip(),
        'weekendClose': (row.get('WKEND_OPER_CLOSE_HHMM') or '').strip(),
        'feeInfo': parse_fee(row),
        'applicationMethod': (row.get('SBSCRPTN_MTH_SE') or '').strip(),
        'photoUrl': (row.get('FCLTY_PIC_INFO') or '').strip(),
        'etcFacility': (row.get('ETC_FCLTY') or '').strip(),
    }

def has_open_data(f):
    return bool(f.get('weekdayOpen') or f.get('feeInfo') or f.get('closedDays'))

def main():
    with open(os.path.join(ROOT, '_data', 'facilities.json'), encoding='utf-8') as f:
        existing = json.load(f)
    with open(os.path.join(ROOT, '_rawdata', 'open_facility_raw.json'), encoding='utf-8') as f:
        raw = json.load(f)

    print('기존 시설:', len(existing))
    print('신규 원본:', len(raw))

    # 체육시설 관련 행만 필터링
    sport_rows = []
    for r in raw:
        t = (r.get('OPEN_FCLTY_TYPE') or '').strip()
        if t in EXCLUDE_EXACT:
            continue
        if t in TYPE_MAP:
            sport_rows.append(r)
    print('체육시설 관련 행:', len(sport_rows))

    # 매칭 인덱스: (regionSlug, city, normalized name) -> facility
    index = {}
    for f in existing:
        key = (f.get('regionSlug'), f.get('city'), norm_name(f.get('name')))
        index[key] = f
        # 부분 이름 매칭 보조 인덱스 (도시 단위)
        index.setdefault(('CITY', f.get('regionSlug'), f.get('city')), []).append(f) if False else None

    matched = 0
    added = 0
    used_slugs = {f['slug'] for f in existing}

    for r in sport_rows:
        fname = (r.get('OPEN_FCLTY_NM') or '').strip()
        if not fname:
            continue
        addr = (r.get('RDNMADR') or r.get('LNMADR') or '').strip()
        region, region_slug = find_region(addr)
        if not region:
            continue
        # 시/군/구 추출 (주소 두번째 토큰)
        parts = addr.split()
        city = parts[1] if len(parts) > 1 else ''

        nname = norm_name(fname)
        key = (region_slug, city, nname)
        target = index.get(key)

        # 완전 일치 실패시, 같은 지역+도시 안에서 부분 문자열 포함 매칭 시도
        if not target:
            for f in existing:
                if f.get('regionSlug') != region_slug or f.get('city') != city:
                    continue
                en = norm_name(f.get('name'))
                if en and (en in nname or nname in en) and len(nname) >= 3:
                    target = f
                    break

        open_fields = build_open_fields(r)

        if target:
            # 기존 시설 보강 (빈 값만 채움 + open_fields는 항상 채움)
            if not target.get('phone'):
                target['phone'] = (r.get('PHONE_NUMBER') or '').strip()
            if not target.get('homepage'):
                target['homepage'] = (r.get('HOMEPAGE_URL') or '').strip()
            if not target.get('area'):
                target['area'] = (r.get('AR') or '').strip()
            if not target.get('capacity'):
                target['capacity'] = (r.get('ACEPTNC_POSBL_CO') or '').strip()
            for k, v in open_fields.items():
                if v:
                    target[k] = v
            matched += 1
        else:
            # 신규 시설로 추가
            ftype, type_slug, type_icon = TYPE_MAP[r.get('OPEN_FCLTY_TYPE').strip()]
            base_slug = sanitize_slug(fname) or 'facility'
            slug = base_slug
            n = 2
            while slug in used_slugs:
                slug = f'{base_slug}-{n}'
                n += 1
            used_slugs.add(slug)

            new_f = {
                'slug': slug,
                'name': fname,
                'ftype': ftype,
                'typeSlug': type_slug,
                'typeIcon': type_icon,
                'region': region,
                'regionSlug': region_slug,
                'city': city,
                'dong': '',
                'address': addr,
                'lat': (r.get('LATITUDE') or '').strip(),
                'lng': (r.get('LONGITUDE') or '').strip(),
                'phone': (r.get('PHONE_NUMBER') or '').strip(),
                'mngOrg': (r.get('INSTITUTION_NM') or '').strip(),
                'mngDept': (r.get('CHRG_DEPT_NM') or '').strip(),
                'homepage': (r.get('HOMEPAGE_URL') or '').strip(),
                'area': (r.get('AR') or '').strip(),
                'seatCnt': '',
                'capacity': (r.get('ACEPTNC_POSBL_CO') or '').strip(),
                'isNational': False,
            }
            new_f.update(open_fields)
            existing.append(new_f)
            added += 1

    print('매칭되어 정보 보강:', matched)
    print('신규 시설로 추가:', added)
    print('최종 총합:', len(existing))

    with_open = sum(1 for f in existing if has_open_data(f))
    print('요금/시간 정보 있는 시설:', with_open)

    by_type = Counter(f['ftype'] for f in existing)
    print('타입 수:', len(by_type))

    with open(os.path.join(ROOT, '_data', 'facilities.json'), 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main()
