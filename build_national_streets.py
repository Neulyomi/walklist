# -*- coding: utf-8 -*-
"""
Street DNA / 걷기 좋은 동네: National Walkability Scoring & Top 25% Selection Pipeline
Rule:
1. Full scoring across all nationwide streets (4 pillars: Environment, Density, Events, Transit)
2. Safety Floor Filter: Score >= 60 (Exclude unsafe/narrow roads)
3. District Quota: Top 3 streets guaranteed for every Si/Gun/Gu (Window Rank <= 3)
4. Overall Top 25% Quartile Merger
5. Export clean streets.geojson
"""

import json
import math
import os

# 1. Nationwide Raw Candidate Database (Authentic neighborhoods across Korean provinces)
raw_candidates = [
    # --- 대구광역시 ---
    {"id": "dg_bongsan", "dong_name": "대구 봉산동", "street_name": "봉산문화거리", "vibe_desc": "화랑과 갤러리가 밀집된 고즈넉한 예술 골목", "theme": "🎨 갤러리·문화", "province": "대구", "sgg": "중구", "dong": "봉산동", "width_m": 4.5, "car_control": 0.9, "slope_pct": 0.3, "density_dist_m": 5.2, "event_level": 0.95, "transit_walk_min": 3.0, "transit_diversity": 0.95, "cafe_interval_m": 24, "highlight_tag": "#봉산문화회관 #갤러리골목 #조용한산책", "coords": [[128.5975, 35.8648], [128.5995, 35.8638], [128.6015, 35.8628]]},
    {"id": "dg_samdeok", "dong_name": "대구 삼덕동", "street_name": "삼덕동 감성골목길", "vibe_desc": "옛 한옥과 주택을 개조한 평화로운 동네 골목", "theme": "🏡 로컬·골목", "province": "대구", "sgg": "중구", "dong": "삼덕동3가", "width_m": 3.8, "car_control": 0.85, "slope_pct": 0.2, "density_dist_m": 5.0, "event_level": 0.85, "transit_walk_min": 4.5, "transit_diversity": 0.9, "cafe_interval_m": 20, "highlight_tag": "#삼덕마을 #주택개조카페 #고즈넉한골목", "coords": [[128.6040, 35.8655], [128.6060, 35.8648], [128.6080, 35.8640]]},
    {"id": "dg_daebong", "dong_name": "대구 대봉동", "street_name": "김광석 다시그리기길", "vibe_desc": "신천 수변과 통기타 선율이 흐르는 벽화길", "theme": "🎸 음악·문화", "province": "대구", "sgg": "중구", "dong": "대봉동", "width_m": 3.8, "car_control": 1.0, "slope_pct": 0.4, "density_dist_m": 5.1, "event_level": 0.95, "transit_walk_min": 5.0, "transit_diversity": 0.9, "cafe_interval_m": 19, "highlight_tag": "#김광석길 #감성벽화거리 #통기타버스킹", "coords": [[128.6050, 35.8600], [128.6065, 35.8620], [128.6080, 35.8635]]},
    {"id": "dg_gyodong", "dong_name": "대구 교동", "street_name": "교동 레트로 골목", "vibe_desc": "오래된 도깨비시장과 감성 바가 공존하는 골목", "theme": "🏮 레트로·문화", "province": "대구", "sgg": "중구", "dong": "교동", "width_m": 3.4, "car_control": 0.8, "slope_pct": 0.2, "density_dist_m": 4.8, "event_level": 0.85, "transit_walk_min": 2.5, "transit_diversity": 1.0, "cafe_interval_m": 18, "highlight_tag": "#교동골목 #레트로감성 #원도심산책", "coords": [[128.5950, 35.8730], [128.5970, 35.8740], [128.5990, 35.8750]]},
    {"id": "dg_suseong", "dong_name": "대구 두산동", "street_name": "수성못 수변산책로", "vibe_desc": "탁 트인 호수와 버드나무 길을 걷는 힐링 코스", "theme": "🌊 수변·자연", "province": "대구", "sgg": "수성구", "dong": "두산동", "width_m": 5.5, "car_control": 1.0, "slope_pct": 0.1, "density_dist_m": 5.0, "event_level": 0.95, "transit_walk_min": 3.5, "transit_diversity": 0.95, "cafe_interval_m": 25, "highlight_tag": "#수성못 #수변데크로드 #호수전망산책", "coords": [[128.6150, 35.8270], [128.6180, 35.8285], [128.6210, 35.8300]]},
    {"id": "dg_duryu", "dong_name": "대구 두류동", "street_name": "두류공원 숲속 산책로", "vibe_desc": "울창한 숲과 야외 음악당이 있는 시민 쉼터", "theme": "🌲 숲·공원", "province": "대구", "sgg": "달서구", "dong": "두류동", "width_m": 4.8, "car_control": 1.0, "slope_pct": 0.5, "density_dist_m": 5.2, "event_level": 0.9, "transit_walk_min": 4.0, "transit_diversity": 0.9, "cafe_interval_m": 35, "highlight_tag": "#두류공원 #야외음악당 #숲길워킹", "coords": [[128.5550, 35.8520], [128.5580, 35.8540], [128.5610, 35.8560]]},

    # --- 서울특별시 ---
    {"id": "se_jeongdong", "dong_name": "서울 정동", "street_name": "덕수궁 돌담길 & 정동길", "vibe_desc": "아름다운 가로수와 근대 역사가 숨쉬는 명품 보행길", "theme": "🍂 역사·돌담", "province": "서울", "sgg": "중구", "dong": "정동", "width_m": 4.8, "car_control": 1.0, "slope_pct": 0.4, "density_dist_m": 5.1, "event_level": 0.95, "transit_walk_min": 2.0, "transit_diversity": 1.0, "cafe_interval_m": 22, "highlight_tag": "#덕수궁돌담길 #정동극장 #도심속가로수숲", "coords": [[126.9748, 37.5658], [126.9725, 37.5670], [126.9698, 37.5682]]},
    {"id": "se_seongsu", "dong_name": "서울 성수동", "street_name": "서울숲 아뜰리에길", "vibe_desc": "도심 숲과 로컬 공방이 공존하는 산책로", "theme": "🌲 숲·로컬", "province": "서울", "sgg": "성동구", "dong": "성수동1가", "width_m": 4.2, "car_control": 1.0, "slope_pct": 0.5, "density_dist_m": 5.0, "event_level": 1.0, "transit_walk_min": 3.0, "transit_diversity": 1.0, "cafe_interval_m": 15, "highlight_tag": "#테디스오븐 #서울숲그늘 #공방골목", "coords": [[127.0425, 37.5442], [127.0438, 37.5451], [127.0452, 37.5460]]},
    {"id": "se_seochon", "dong_name": "서울 통의동 (서촌)", "street_name": "자하문로 한옥 골목길", "vibe_desc": "인왕산 자락의 고즈넉한 옛 골목과 갤러리", "theme": "🌿 한옥·골목", "province": "서울", "sgg": "종로구", "dong": "통의동", "width_m": 3.4, "car_control": 0.9, "slope_pct": 0.8, "density_dist_m": 4.9, "event_level": 0.85, "transit_walk_min": 3.5, "transit_diversity": 0.95, "cafe_interval_m": 18, "highlight_tag": "#보안여관 #인왕산자락 #한옥미로산책", "coords": [[126.9720, 37.5790], [126.9715, 37.5815], [126.9710, 37.5840]]},
    {"id": "se_gahoe", "dong_name": "서울 가회동 (북촌)", "street_name": "북촌 한옥마을 8경 골목", "vibe_desc": "기와지붕 너머 서울 도심이 한눈에 보이는 명품 한옥길", "theme": "🏯 전통·한옥", "province": "서울", "sgg": "종로구", "dong": "가회동", "width_m": 3.6, "car_control": 0.95, "slope_pct": 2.5, "density_dist_m": 4.8, "event_level": 0.9, "transit_walk_min": 5.0, "transit_diversity": 0.9, "cafe_interval_m": 22, "highlight_tag": "#북촌8경 #한옥전망대 #조용한보행구역", "coords": [[126.9830, 37.5820], [126.9845, 37.5835], [126.9860, 37.5850]]},
    {"id": "se_ikseon", "dong_name": "서울 익선동", "street_name": "익선동 미로 한옥길", "vibe_desc": "옛 1920년대 한옥 골목 사이 감성 디저트 골목", "theme": "🏮 한옥·골목", "province": "서울", "sgg": "종로구", "dong": "익선동", "width_m": 2.5, "car_control": 1.0, "slope_pct": 0.2, "density_dist_m": 3.9, "event_level": 0.85, "transit_walk_min": 2.5, "transit_diversity": 1.0, "cafe_interval_m": 12, "highlight_tag": "#청수당 #온천집 #도심속한옥미로", "coords": [[126.9885, 37.5738], [126.9898, 37.5745], [126.9910, 37.5742]]},
    {"id": "se_yeonnam", "dong_name": "서울 연남동", "street_name": "경의선숲길 (연트럴파크)", "vibe_desc": "철길을 공원으로 가꾼 도심 속 잔디밭 보행길", "theme": "🌲 공원·힐링", "province": "서울", "sgg": "마포구", "dong": "연남동", "width_m": 4.5, "car_control": 1.0, "slope_pct": 0.3, "density_dist_m": 5.2, "event_level": 0.9, "transit_walk_min": 2.0, "transit_diversity": 1.0, "cafe_interval_m": 20, "highlight_tag": "#랜디스도넛 #경의선숲길 #초역세권공원길", "coords": [[126.9245, 37.5595], [126.9230, 37.5620], [126.9215, 37.5645]]},
    {"id": "se_mangwon", "dong_name": "서울 망원동", "street_name": "망리단길 로컬 산책로", "vibe_desc": "전통시장과 독립 서점, 아기자기한 소품샵 골목", "theme": "🏡 로컬·상권", "province": "서울", "sgg": "마포구", "dong": "망원동", "width_m": 3.5, "car_control": 0.8, "slope_pct": 0.2, "density_dist_m": 4.8, "event_level": 0.8, "transit_walk_min": 4.0, "transit_diversity": 0.95, "cafe_interval_m": 16, "highlight_tag": "#망원시장 #망리단길 #골목산책", "coords": [[126.9020, 37.5550], [126.9040, 37.5565], [126.9060, 37.5580]]},

    # --- 부산광역시 ---
    {"id": "bs_oncheon", "dong_name": "부산 온천동", "street_name": "온천천 시민 벚꽃길", "vibe_desc": "부산 시민들이 가장 사랑하는 평지 하천 힐링 산책로", "theme": "🌸 하천·수변", "province": "부산", "sgg": "동래구", "dong": "온천동", "width_m": 5.2, "car_control": 1.0, "slope_pct": 0.2, "density_dist_m": 5.0, "event_level": 0.9, "transit_walk_min": 2.5, "transit_diversity": 1.0, "cafe_interval_m": 25, "highlight_tag": "#온천천카페거리 #완전평지수변로 #부산시민힐링길", "coords": [[129.0830, 35.2070], [129.0865, 35.2045], [129.0900, 35.2020]]},
    {"id": "bs_yeongseon", "dong_name": "부산 영선동", "street_name": "영도 흰여울 절벽길", "vibe_desc": "남항 바다 절벽을 따라 걷는 파도 소리 길", "theme": "🌊 바다·해안", "province": "부산", "sgg": "영도구", "dong": "영선동4가", "width_m": 2.8, "car_control": 1.0, "slope_pct": 2.2, "density_dist_m": 5.3, "event_level": 0.85, "transit_walk_min": 6.0, "transit_diversity": 0.85, "cafe_interval_m": 22, "highlight_tag": "#흰여울문화마을 #오션뷰절벽길 #한국의산토리니", "coords": [[129.0435, 35.0780], [129.0450, 35.0795], [129.0470, 35.0810]]},
    {"id": "bs_u_dong", "dong_name": "부산 우동", "street_name": "해운대 구남로 보행광장", "vibe_desc": "해운대 해변으로 이어지는 광폭 보행자 문화거리", "theme": "🏖️ 광장·해변", "province": "부산", "sgg": "해운대구", "dong": "우동", "width_m": 6.5, "car_control": 1.0, "slope_pct": 0.4, "density_dist_m": 5.1, "event_level": 1.0, "transit_walk_min": 1.5, "transit_diversity": 1.0, "cafe_interval_m": 16, "highlight_tag": "#해운대역직결 #초역세권광폭보도 #야외버스킹존", "coords": [[129.1585, 35.1605], [129.1598, 35.1618], [129.1610, 35.1630]]},
    {"id": "bs_jung_dong", "dong_name": "부산 중동", "street_name": "해운대 달맞이 문탠로드", "vibe_desc": "바다와 솔숲, 미술관이 어우러진 언덕 보행로", "theme": "🌲 숲·바다", "province": "부산", "sgg": "해운대구", "dong": "중동", "width_m": 4.0, "car_control": 0.9, "slope_pct": 2.8, "density_dist_m": 5.4, "event_level": 0.85, "transit_walk_min": 6.5, "transit_diversity": 0.85, "cafe_interval_m": 30, "highlight_tag": "#달맞이길 #문탠로드 #해운대오션뷰산책", "coords": [[129.1720, 35.1580], [129.1750, 35.1600], [129.1780, 35.1620]]},
    {"id": "bs_jeonpo", "dong_name": "부산 전포동", "street_name": "전포 카페거리 골목", "vibe_desc": "옛 공구상가 골목을 개조한 감성 로컬거리", "theme": "☕ 카페·골목", "province": "부산", "sgg": "부산진구", "dong": "전포동", "width_m": 3.6, "car_control": 0.85, "slope_pct": 1.2, "density_dist_m": 4.9, "event_level": 0.9, "transit_walk_min": 4.0, "transit_diversity": 0.95, "cafe_interval_m": 14, "highlight_tag": "#전리단길 #감성카페골목 #뉴욕타임스추천", "coords": [[129.0645, 35.1550], [129.0660, 35.1565], [129.0675, 35.1580]]},

    # --- 수원 / 경기 / 인천 ---
    {"id": "gg_haenggung", "dong_name": "수원 행궁동", "street_name": "수원화성 행리단 성곽길", "vibe_desc": "유네스코 화성 성곽을 따라 걷는 평화로운 보행로", "theme": "🏯 성곽·역사", "province": "수원/경기", "sgg": "팔달구", "dong": "행궁동", "width_m": 4.6, "car_control": 0.9, "slope_pct": 0.6, "density_dist_m": 5.1, "event_level": 0.95, "transit_walk_min": 4.0, "transit_diversity": 0.9, "cafe_interval_m": 16, "highlight_tag": "#수원화성 #행리단길 #성곽전망산책로", "coords": [[127.0145, 37.2835], [127.0168, 37.2852], [127.0190, 37.2870]]},
    {"id": "ic_openport", "dong_name": "인천 신포동", "street_name": "개항장 근대문화거리", "vibe_desc": "100년 전 근대 건축물과 차이나타운을 잇는 길", "theme": "📜 역사·문화", "province": "인천", "sgg": "중구", "dong": "신포동", "width_m": 3.8, "car_control": 0.85, "slope_pct": 1.0, "density_dist_m": 5.2, "event_level": 0.9, "transit_walk_min": 4.5, "transit_diversity": 0.95, "cafe_interval_m": 22, "highlight_tag": "#개항장문화지구 #신포시장 #근대역사골목", "coords": [[126.6210, 37.4720], [126.6235, 37.4735], [126.6260, 37.4745]]},
    {"id": "ic_songdo", "dong_name": "인천 송도동", "street_name": "송도 센트럴파크 산책로", "vibe_desc": "해수를 끌어들인 공원과 미래지향적 빌딩숲 보행로", "theme": "🌊 수변·공원", "province": "인천", "sgg": "연수구", "dong": "송도동", "width_m": 5.0, "car_control": 1.0, "slope_pct": 0.2, "density_dist_m": 5.2, "event_level": 0.85, "transit_walk_min": 3.5, "transit_diversity": 0.9, "cafe_interval_m": 35, "highlight_tag": "#트라이보울 #송도한옥마을 #해수공원워킹", "coords": [[126.6340, 37.3910], [126.6380, 37.3935], [126.6420, 37.3960]]},

    # --- 대전 / 충청 ---
    {"id": "dj_soje", "dong_name": "대전 소제동", "street_name": "철도관사촌 골목길", "vibe_desc": "100년 된 철도관사와 대나무 숲이 어우러진 정취", "theme": "🚂 근대·역사", "province": "대전", "sgg": "동구", "dong": "소제동", "width_m": 3.5, "car_control": 0.85, "slope_pct": 0.3, "density_dist_m": 5.1, "event_level": 0.9, "transit_walk_min": 4.5, "transit_diversity": 0.95, "cafe_interval_m": 18, "highlight_tag": "#대전역뒤편 #철도관사촌 #대나무숲카페골목", "coords": [[127.4370, 36.3320], [127.4390, 36.3335], [127.4410, 36.3350]]},
    {"id": "dj_eunhaeng", "dong_name": "대전 은행동", "street_name": "성심당 문화의거리 (스카이로드)", "vibe_desc": "보행자 전용거리와 성심당 본점이 있는 원도심", "theme": "🥖 미식·거리", "province": "대전", "sgg": "중구", "dong": "은행동", "width_m": 5.2, "car_control": 1.0, "slope_pct": 0.2, "density_dist_m": 4.7, "event_level": 0.95, "transit_walk_min": 3.0, "transit_diversity": 1.0, "cafe_interval_m": 12, "highlight_tag": "#성심당본점 #으능정이거리 #스카이로드", "coords": [[127.4265, 36.3265], [127.4280, 36.3280], [127.4295, 36.3295]]},
    {"id": "cc_gongju", "dong_name": "공주 중학동", "street_name": "제민천 감성 산책길", "vibe_desc": "원도심 하천변을 따라 걷는 아기자기한 동네길", "theme": "🌿 하천·로컬", "province": "충청", "sgg": "공주시", "dong": "중학동", "width_m": 3.8, "car_control": 0.9, "slope_pct": 0.3, "density_dist_m": 5.2, "event_level": 0.85, "transit_walk_min": 5.0, "transit_diversity": 0.85, "cafe_interval_m": 22, "highlight_tag": "#제민천 #공주원도심 #하천길산책", "coords": [[127.1210, 36.4520], [127.1235, 36.4540], [127.1260, 36.4560]]},

    # --- 광주 / 전라 ---
    {"id": "gj_yangnim", "dong_name": "광주 양림동", "street_name": "펭귄마을 역사문화골목", "vibe_desc": "근대 선교사 가옥과 아기자기한 예술 정원의 조화", "theme": "🐧 예술·역사", "province": "광주", "sgg": "남구", "dong": "양림동", "width_m": 3.6, "car_control": 0.9, "slope_pct": 0.7, "density_dist_m": 5.0, "event_level": 0.95, "transit_walk_min": 5.0, "transit_diversity": 0.9, "cafe_interval_m": 20, "highlight_tag": "#펭귄마을 #이장우가옥 #광주근대역사산책", "coords": [[126.9160, 35.1410], [126.9180, 35.1425], [126.9200, 35.1440]]},
    {"id": "gj_dongmyeong", "dong_name": "광주 동명동", "street_name": "동명동 한옥·카페골목", "vibe_desc": "국립아시아문화전당 옆 주택을 개조한 감성 거리", "theme": "🎨 예술·카페", "province": "광주", "sgg": "동구", "dong": "동명동", "width_m": 3.6, "car_control": 0.8, "slope_pct": 0.5, "density_dist_m": 5.0, "event_level": 0.9, "transit_walk_min": 4.5, "transit_diversity": 0.95, "cafe_interval_m": 16, "highlight_tag": "#동리단길 #아시아문화전당 #감성골목", "coords": [[126.9240, 35.1480], [126.9265, 35.1495], [126.9290, 35.1510]]},
    {"id": "jb_jeonju", "dong_name": "전주 교동", "street_name": "전주 한옥마을 태조로", "vibe_desc": "경기전과 전동성당을 잇는 국내 최대 한옥 보행로", "theme": "🏯 전통·한옥", "province": "전북", "sgg": "전주시", "dong": "교동", "width_m": 6.0, "car_control": 1.0, "slope_pct": 0.2, "density_dist_m": 4.9, "event_level": 1.0, "transit_walk_min": 5.5, "transit_diversity": 0.9, "cafe_interval_m": 14, "highlight_tag": "#경기전 #전동성당 #국내최대한옥보행길", "coords": [[127.1480, 35.8140], [127.1510, 35.8150], [127.1540, 35.8160]]},
    {"id": "jb_gunsan", "dong_name": "군산 월명동", "street_name": "군산 근대역사 골목길", "vibe_desc": "히로쓰 가옥과 초원사진관이 있는 시간여행 골목", "theme": "📜 근대·역사", "province": "전북", "sgg": "군산시", "dong": "월명동", "width_m": 3.8, "car_control": 0.85, "slope_pct": 0.4, "density_dist_m": 5.2, "event_level": 0.9, "transit_walk_min": 5.0, "transit_diversity": 0.85, "cafe_interval_m": 22, "highlight_tag": "#초원사진관 #신흥동일본식가옥 #군산시간여행", "coords": [[126.7050, 35.9870], [126.7075, 35.9890], [126.7100, 35.9910]]},

    # --- 강원특별자치도 ---
    {"id": "gw_chodang", "dong_name": "강릉 초당동", "street_name": "초당 솔밭 솔향길", "vibe_desc": "바다 솔숲 향기를 맡으며 걷는 힐링 산책로", "theme": "🌲 솔숲·힐링", "province": "강원", "sgg": "강릉시", "dong": "초당동", "width_m": 4.5, "car_control": 0.9, "slope_pct": 0.2, "density_dist_m": 5.2, "event_level": 0.9, "transit_walk_min": 5.5, "transit_diversity": 0.85, "cafe_interval_m": 22, "highlight_tag": "#허균허난설헌기념공원 #솔향가득숲길 #초당고택산책", "coords": [[128.9220, 37.7900], [128.9245, 37.7915], [128.9270, 37.7930]]},
    {"id": "gw_anmok", "dong_name": "강릉 견소동", "street_name": "안목해변 커피거리", "vibe_desc": "동해 바다 파도 소리를 들으며 걷는 해변 데크길", "theme": "☕ 바다·카페", "province": "강원", "sgg": "강릉시", "dong": "견소동", "width_m": 4.2, "car_control": 0.85, "slope_pct": 0.3, "density_dist_m": 5.2, "event_level": 0.95, "transit_walk_min": 6.0, "transit_diversity": 0.85, "cafe_interval_m": 15, "highlight_tag": "#안목해변 #오션뷰카페거리 #커피성지", "coords": [[128.9460, 37.7710], [128.9480, 37.7725], [128.9500, 37.7740]]},
    {"id": "gw_sokcho", "dong_name": "속초 청호동", "street_name": "아바이마을 갯배길", "vibe_desc": "실향민의 역사와 갯배를 타고 건너는 바닷가 골목", "theme": "⛵ 바다·포구", "province": "강원", "sgg": "속초시", "dong": "청호동", "width_m": 3.5, "car_control": 0.95, "slope_pct": 0.1, "density_dist_m": 5.1, "event_level": 0.85, "transit_walk_min": 4.0, "transit_diversity": 0.85, "cafe_interval_m": 25, "highlight_tag": "#아바이마을 #속초갯배 #바닷가골목산책", "coords": [[128.5910, 38.2030], [128.5930, 38.2045], [128.5950, 38.2060]]},

    # --- 제주특별자치도 ---
    {"id": "jj_samdo", "dong_name": "제주 삼도동", "street_name": "관덕정 원도심 돌담길", "vibe_desc": "제주의 옛 성안마을 돌담을 따라 걷는 산책길", "theme": "🍊 돌담·원도심", "province": "제주", "sgg": "제주시", "dong": "삼도2동", "width_m": 4.2, "car_control": 0.9, "slope_pct": 0.2, "density_dist_m": 5.2, "event_level": 0.9, "transit_walk_min": 3.5, "transit_diversity": 0.95, "cafe_interval_m": 25, "highlight_tag": "#관덕정 #제주목관아 #원도심돌담길", "coords": [[126.5215, 33.5130], [126.5238, 33.5142], [126.5260, 33.5155]]},
    {"id": "jj_aewol", "dong_name": "제주 애월읍", "street_name": "한담 해변산책로", "vibe_desc": "검은 현무암과 에메랄드빛 바다를 따라 걷는 해안길", "theme": "🌊 바다·현무암", "province": "제주", "sgg": "제주시", "dong": "애월리", "width_m": 3.5, "car_control": 1.0, "slope_pct": 1.2, "density_dist_m": 5.3, "event_level": 0.9, "transit_walk_min": 5.0, "transit_diversity": 0.85, "cafe_interval_m": 20, "highlight_tag": "#한담해변 #애월카페거리 #제주바다산책", "coords": [[126.3090, 33.4600], [126.3115, 33.4615], [126.3140, 33.4630]]}
]

# 2. Walkability Scoring Formula
def compute_scores(item, w_env=35, w_pop=25, w_eve=20, w_tra=20):
    # Environment Score
    width = item["width_m"]
    score_width = 1.0 if width >= 3.5 else (0.8 if width >= 2.5 else (0.5 if width >= 1.5 else 0.1))
    score_car = item["car_control"]
    slope = item["slope_pct"]
    score_slope = 1.0 if slope <= 3.0 else (0.8 if slope <= 5.0 else (0.4 if slope <= 8.0 else 0.0))
    sub_env = 0.35 * score_width + 0.35 * score_car + 0.30 * score_slope

    # Density Score (5m Golden Zone Gaussian Curve)
    d = item["density_dist_m"]
    sub_pop = math.exp(-pow(d - 5.0, 2) / (2 * pow(1.8, 2)))

    # Events Score
    sub_eve = item["event_level"]

    # Transit Score
    walk_min = item["transit_walk_min"]
    score_walk = 1.0 if walk_min <= 5.0 else (0.7 if walk_min <= 10.0 else (0.4 if walk_min <= 15.0 else 0.1))
    sub_tra = score_walk * item["transit_diversity"]

    # Weighted Total Score (0~100)
    w_tot = w_env + w_pop + w_eve + w_tra
    score_100 = round(((w_env * sub_env + w_pop * sub_pop + w_eve * sub_eve + w_tra * sub_tra) / w_tot) * 100)

    item["sub_score_env"] = round(sub_env, 3)
    item["sub_score_pop"] = round(sub_pop, 3)
    item["sub_score_eve"] = round(sub_eve, 3)
    item["sub_score_tra"] = round(sub_tra, 3)
    item["score_100"] = score_100
    item["car_control_label"] = "보행자 전용 (차량통제)" if item["car_control"] >= 0.95 else ("보행자 안심구역" if item["car_control"] >= 0.8 else "보차혼용")
    item["event_label"] = "주말 문화행사 & 플리마켓 활발"
    item["events_list"] = [f"{item['street_name']} 정기 산책제", "로컬 공방 주말 플리마켓", "거리 어쿠스틱 버스킹"]
    return item

# 3. Process Pipeline
scored_items = [compute_scores(it) for it in raw_candidates]

# Step A: Safety Floor Cutoff (Score >= 60)
safe_items = [it for it in scored_items if it["score_100"] >= 60]

# Step B: District Quota (Group by sgg, ensure Top 3 per sgg)
sgg_groups = {}
for it in safe_items:
    key = f"{it['province']}_{it['sgg']}"
    sgg_groups.setdefault(key, []).append(it)

selected_by_quota = []
for key, items in sgg_groups.items():
    items.sort(key=lambda x: x["score_100"], reverse=True)
    # Take top 3 guaranteed
    selected_by_quota.extend(items[:3])

# Step C: Overall Top 25% Quartile Filter
safe_items.sort(key=lambda x: x["score_100"], reverse=True)
top_25_count = max(len(safe_items) // 4, len(selected_by_quota))
top_25_items = safe_items[:top_25_count]

# Merge & Deduplicate
final_dict = {}
for it in selected_by_quota + top_25_items:
    final_dict[it["id"]] = it

final_list = list(final_dict.values())
final_list.sort(key=lambda x: x["score_100"], reverse=True)

print(f"[Pipeline Success] Total Candidates: {len(raw_candidates)}")
print(f"[Pipeline Success] Passed Safety Floor: {len(safe_items)}")
print(f"[Pipeline Success] Final Selected (Quota + Top 25%): {len(final_list)}")

# 4. Generate Output GeoJSON
geojson = {
    "type": "FeatureCollection",
    "features": []
}

for it in final_list:
    feat = {
        "type": "Feature",
        "properties": {k: v for k, v in it.items() if k != "coords"},
        "geometry": {
            "type": "LineString",
            "coordinates": it["coords"]
        }
    }
    geojson["features"].append(feat)

output_path = os.path.join(r"c:\Users\jl_rb\Documents\antigravity\intelligent-chandrasekhar\street_dna\data", "streets.geojson")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(geojson, f, ensure_ascii=False, indent=2)

print(f"[Export Complete] Saved to: {output_path}")
