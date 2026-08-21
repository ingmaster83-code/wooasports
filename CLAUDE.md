# wooasports 프로젝트 지침

## 프로젝트 개요
**wooasports.wooahouse.com** — 전국 공공체육시설 정보 사이트 (Jekyll)

## 데이터 파이프라인 ⚠️ 순서 중요

`_data/facilities.json`은 두 개의 서로 다른 공공데이터 소스를 병합한 결과물이다. **반드시 아래 순서대로 실행**해야 하며, `process.py`만 단독 실행하면 2번 단계에서 병합한 요금/운영시간/사진 정보가 전부 사라진다.

1. `python scripts/fetch_all.py` — 국민체육진흥공단 전국체육시설현황 API(`SRVC_SFMS_FACIL_INFO`) 원본을 `_rawdata/raw_facilities.json`으로 저장
2. `python scripts/process.py` — 원본을 정제해 `_data/facilities.json`을 **처음부터 새로 생성** (여기서 기존 병합 데이터 다 날아감)
3. `python scripts/merge_open_facility.py` — data.go.kr `전국공공시설개방정보표준데이터`(15013117)를 병합해 요금·운영시간·휴관일·사진·신청방법 정보 보강 + 새 종목(농구장·배드민턴장·족구장·배구장·탁구장·볼링장 등) 추가

**1~2번만 다시 돌렸다면 반드시 3번도 이어서 실행할 것.**

### 전국공공시설개방정보표준데이터 재다운로드 방법
API 키 승인 없이 아래 URL로 바로 전체 데이터(JSON, 로그인 불필요) 다운로드 가능:
```
https://www.data.go.kr/download/standard.json?publicDataPk=15013117&colNmList=OPEN_FCLTY_NM&colNmList=OPEN_LC_NM&colNmList=OPEN_FCLTY_TYPE&colNmList=RSTDE&colNmList=WEEKDAY_OPER_OPEN_HHMM&colNmList=WEEKDAY_OPER_COLSE_HHMM&colNmList=WKEND_OPER_OPEN_HHMM&colNmList=WKEND_OPER_CLOSE_HHMM&colNmList=PCHRG_USE_YN&colNmList=USE_STDR_TIME&colNmList=RNTFEE&colNmList=EXCESS_USE_UNIT_TIME&colNmList=EXCESS_RNTFEE&colNmList=ACEPTNC_POSBL_CO&colNmList=AR&colNmList=ETC_FCLTY&colNmList=SBSCRPTN_MTH_SE&colNmList=FCLTY_PIC_INFO&colNmList=RDNMADR&colNmList=LNMADR&colNmList=INSTITUTION_NM&colNmList=CHRG_DEPT_NM&colNmList=PHONE_NUMBER&colNmList=HOMEPAGE_URL&colNmList=LATITUDE&colNmList=LONGITUDE&colNmList=REFERENCE_DATE&totalCount=7329&svcTableNm=tn_pubr_public_pblfclt_opn_info_svc&perPage=10000&page=1
```
`totalCount`는 매 분기 데이터가 갱신되므로 재다운로드 전에 `data.go.kr/data/15013117/standard.do` 페이지에서 실제 값을 다시 확인할 것(다를 경우 일부 레코드 누락). 저장 위치: `_rawdata/open_facility_raw.json`.

`merge_open_facility.py`의 `TYPE_MAP`에 없는 `개방시설유형구분` 값(회의실/강의실/강당/다목적실/전시실 등)은 체육시설이 아니므로 자동으로 제외되고, `캠핑장`은 wooacamp와 겹쳐서 명시적으로 제외한다.

## 관련 사이트
- 캠핑장은 wooacamp가 담당 — 이 데이터셋에 캠핑장이 섞여 있어도 merge 스크립트가 자동 제외
- 파크골프장은 wooaparkgolf와 일부 겹칠 수 있음(`기타(파크골프장)` 타입) — 중복 노출 자체는 문제 없음(사이트가 다름)

## 기술 스택
- Jekyll (`_plugins/sports_generator.rb`가 facility/region/type 페이지 대량 생성)
- 데이터: `_data/facilities.json` (9,338개 시설, 36개 종목)
- 광고: Google AdSense, GA: G-9ZGENFSXWC
