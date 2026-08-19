import json
import math
import os

def calculate_sub_scores(props):
    # 1. 도보 환경 (Environment)
    width = props.get("width_m", 3.5)
    score_width = 1.0 if width >= 3.5 else (0.8 if width >= 2.5 else (0.5 if width >= 1.5 else 0.1))
    score_car = props.get("car_control", 0.7)
    slope = props.get("slope_pct", 1.0)
    score_slope = 1.0 if slope <= 3.0 else (0.8 if slope <= 5.0 else (0.4 if slope <= 8.0 else 0.0))
    score_env = (0.35 * score_width) + (0.35 * score_car) + (0.30 * score_slope)

    # 2. 인구밀도 (Population Density) - 5m Golden Zone
    d = props.get("density_dist_m", 5.0)
    score_pop = math.exp(-pow(d - 5.0, 2) / (2 * pow(1.8, 2)))

    # 3. 이벤트 (Events / Culture)
    score_eve = props.get("event_level", 0.5)

    # 4. 대중교통 (Transit)
    walk_min = props.get("transit_walk_min", 5.0)
    score_walk = 1.0 if walk_min <= 5.0 else (0.7 if walk_min <= 10.0 else (0.4 if walk_min <= 15.0 else 0.1))
    score_tra = score_walk * props.get("transit_diversity", 0.8)

    # 기본 가중치 (35:25:20:20) 적용 종합점수 (100점 만점)
    score_100 = round((35 * score_env) + (25 * score_pop) + (20 * score_eve) + (20 * score_tra), 1)

    props["sub_score_env"] = round(score_env, 3)
    props["sub_score_pop"] = round(score_pop, 3)
    props["sub_score_eve"] = round(score_eve, 3)
    props["sub_score_tra"] = round(score_tra, 3)
    props["score_100"] = round(score_100)
    props["score_raw"] = score_100
    return props

# 전국 전수 동네 후보군 데이터베이스 (전국 주요 시·군·구 전수 후보군)
candidates = [
    # ==================== 대구광역시 ====================
    # 수성구
    {
        "id": "dg_suseong_dusan", "dong_name": "대구 두산동", "street_name": "수성못 수변산책로",
        "vibe_desc": "탁 트인 호수와 버드나무 길을 걷는 대구 대표 힐링 코스", "theme": "🌊 수변·자연",
        "province": "대구", "sgg": "수성구", "dong": "두산동", "width_m": 5.8, "car_control": 1.0,
        "car_control_label": "수변공원 완전 보행전용길", "slope_pct": 0.1, "density_dist_m": 5.0,
        "event_level": 0.95, "event_label": "수성못 페스티벌 & 호수 야외 버스킹",
        "events_list": ["수성못 야간 음악분수 버스킹", "수변 시민 플리마켓", "호수 낭만 산책제"],
        "cafe_interval_m": 22, "transit_walk_min": 3.0, "transit_diversity": 0.95,
        "highlight_tag": "#수성못 #호수전망산책로 #수변데크로드", "is_landmark": True,
        "coords": [[128.6140, 35.8265], [128.6175, 35.8280], [128.6210, 35.8300]]
    },
    {
        "id": "dg_suseong_beomeo", "dong_name": "대구 범어동", "street_name": "범어천 생태 산책로",
        "vibe_desc": "도심 속 흐르는 맑은 하천과 징검다리 숲길", "theme": "🌿 하천·도심",
        "province": "대구", "sgg": "수성구", "dong": "범어동", "width_m": 4.2, "car_control": 0.9,
        "car_control_label": "하천변 보행전용길", "slope_pct": 0.3, "density_dist_m": 4.9,
        "event_level": 0.85, "event_label": "범어천 숲길 작은 음악회",
        "events_list": ["범어 숲 산책 버스킹"], "cafe_interval_m": 20, "transit_walk_min": 3.5, "transit_diversity": 0.95,
        "highlight_tag": "#범어천 #도심속생태하천 #징검다리산책", "is_landmark": False,
        "coords": [[128.6250, 35.8580], [128.6270, 35.8560], [128.6290, 35.8540]]
    },
    {
        "id": "dg_suseong_manchon", "dong_name": "대구 만촌동", "street_name": "형봉산 둘레 숲길",
        "vibe_desc": "완만한 흙길과 피톤치드가 가득한 숲속 힐링로", "theme": "🌲 숲·힐링",
        "province": "대구", "sgg": "수성구", "dong": "만촌동", "width_m": 3.8, "car_control": 1.0,
        "car_control_label": "숲속 보행전용로", "slope_pct": 2.1, "density_dist_m": 5.2,
        "event_level": 0.75, "event_label": "만촌 숲길 자연 힐링 워크",
        "events_list": ["형봉산 숲 해설 투어"], "cafe_interval_m": 35, "transit_walk_min": 5.0, "transit_diversity": 0.85,
        "highlight_tag": "#만촌숲길 #피톤치드산책 #흙길워킹", "is_landmark": False,
        "coords": [[128.6480, 35.8520], [128.6500, 35.8540], [128.6520, 35.8560]]
    },
    {
        "id": "dg_suseong_hwanggeum", "dong_name": "대구 황금동", "street_name": "국립대구박물관 정원 산책로",
        "vibe_desc": "유물 야외 전시장과 고목이 어우러진 조용한 공원길", "theme": "🏛️ 역사·정원",
        "province": "대구", "sgg": "수성구", "dong": "황금동", "width_m": 4.5, "car_control": 1.0,
        "car_control_label": "박물관 공원 보행전용로", "slope_pct": 0.5, "density_dist_m": 5.1,
        "event_level": 0.8, "event_label": "박물관 주말 야외 문화축제",
        "events_list": ["대구박물관 문화가 있는 날"], "cafe_interval_m": 30, "transit_walk_min": 4.0, "transit_diversity": 0.9,
        "highlight_tag": "#국립대구박물관 #정원산책 #고즈넉한쉼터", "is_landmark": False,
        "coords": [[128.6360, 35.8450], [128.6385, 35.8465], [128.6410, 35.8480]]
    },
    # 중구
    {
        "id": "dg_jung_bongsan", "dong_name": "대구 봉산동", "street_name": "봉산문화거리",
        "vibe_desc": "화랑과 갤러리가 밀집된 고즈넉한 예술 골목", "theme": "🎨 갤러리·문화",
        "province": "대구", "sgg": "중구", "dong": "봉산동", "width_m": 4.5, "car_control": 0.9,
        "car_control_label": "보행자 우선도로 (차량 서행)", "slope_pct": 0.3, "density_dist_m": 5.2,
        "event_level": 0.95, "event_label": "봉산미술제 & 갤러리 골목 투어",
        "events_list": ["봉산 야외 갤러리 전시", "로컬 아티스트 공방 마켓", "골목 버스킹"],
        "cafe_interval_m": 24, "transit_walk_min": 3.0, "transit_diversity": 0.95,
        "highlight_tag": "#봉산문화회관 #갤러리골목 #조용한예술산책", "is_landmark": True,
        "coords": [[128.5975, 35.8648], [128.5995, 35.8638], [128.6015, 35.8628]]
    },
    {
        "id": "dg_jung_daebong", "dong_name": "대구 대봉동", "street_name": "김광석 다시그리기길",
        "vibe_desc": "신천 수변과 통기타 선율이 흐르는 벽화길", "theme": "🎸 음악·문화",
        "province": "대구", "sgg": "중구", "dong": "대봉동", "width_m": 3.8, "car_control": 1.0,
        "car_control_label": "음악문화 보행전용길", "slope_pct": 0.4, "density_dist_m": 5.1,
        "event_level": 0.95, "event_label": "거리 어쿠스틱 콘서트 & 벽화거리",
        "events_list": ["김광석 음악 버스킹 콘서트", "대봉동 예술 마켓"],
        "cafe_interval_m": 19, "transit_walk_min": 5.0, "transit_diversity": 0.9,
        "highlight_tag": "#김광석길 #감성벽화거리 #통기타버스킹", "is_landmark": True,
        "coords": [[128.6050, 35.8600], [128.6065, 35.8620], [128.6080, 35.8635]]
    },
    {
        "id": "dg_jung_samdeok", "dong_name": "대구 삼덕동", "street_name": "삼덕동 감성골목길",
        "vibe_desc": "옛 한옥과 주택을 개조한 평화로운 동네 골목", "theme": "🏡 로컬·골목",
        "province": "대구", "sgg": "중구", "dong": "삼덕동3가", "width_m": 3.8, "car_control": 0.85,
        "car_control_label": "보행자 안심골목", "slope_pct": 0.2, "density_dist_m": 5.0,
        "event_level": 0.85, "event_label": "동네 플리마켓 & 작은 책방 투어",
        "events_list": ["삼덕 골목 소품 마켓", "동네 책방 야간 북토크"],
        "cafe_interval_m": 20, "transit_walk_min": 4.5, "transit_diversity": 0.9,
        "highlight_tag": "#삼덕마을 #주택개조카페 #고즈넉한골목", "is_landmark": True,
        "coords": [[128.6040, 35.8655], [128.6060, 35.8648], [128.6080, 35.8640]]
    },
    {
        "id": "dg_jung_gyodong", "dong_name": "대구 교동", "street_name": "교동 레트로 문화거리",
        "vibe_desc": "레트로 감성과 젊은 문화가 공존하는 보행 골목", "theme": "☕ 레트로·골목",
        "province": "대구", "sgg": "중구", "dong": "교동", "width_m": 3.6, "car_control": 0.9,
        "car_control_label": "보행우선거리", "slope_pct": 0.2, "density_dist_m": 4.8,
        "event_level": 0.9, "event_label": "교동 밤마실 플리마켓",
        "events_list": ["교동 도깨비 야시장", "빈티지 마켓"], "cafe_interval_m": 15, "transit_walk_min": 2.5, "transit_diversity": 1.0,
        "highlight_tag": "#교동카페거리 #레트로감성골목 #대구역도보5분", "is_landmark": False,
        "coords": [[128.5980, 35.8720], [128.6000, 35.8715], [128.6020, 35.8710]]
    },
    # 달서구
    {
        "id": "dg_dalseo_duryu", "dong_name": "대구 두류동", "street_name": "두류공원 숲속 산책로 & 야당",
        "vibe_desc": "울창한 숲과 야외 음악당 잔디밭이 펼쳐진 시민 쉼터", "theme": "🌲 숲·공원",
        "province": "대구", "sgg": "달서구", "dong": "두류동", "width_m": 5.0, "car_control": 1.0,
        "car_control_label": "공원 완전 보행전용길", "slope_pct": 0.5, "density_dist_m": 5.2,
        "event_level": 0.9, "event_label": "야외음악당 치맥 페스타 & 버스킹",
        "events_list": ["두류 야외음악당 콘서트", "달서 숲길 걷기대회"],
        "cafe_interval_m": 35, "transit_walk_min": 4.0, "transit_diversity": 0.9,
        "highlight_tag": "#두류공원 #야외음악당 #숲길워킹", "is_landmark": True,
        "coords": [[128.5550, 35.8520], [128.5580, 35.8540], [128.5610, 35.8560]]
    },
    {
        "id": "dg_dalseo_wolseong", "dong_name": "대구 월성동", "street_name": "월성 선사유적 숲길",
        "vibe_desc": "선사시대 유적 공원과 푸른 가로수 산책로", "theme": "🏛️ 역사·공원",
        "province": "대구", "sgg": "달서구", "dong": "월성동", "width_m": 4.0, "car_control": 0.9,
        "car_control_label": "보행자 안심산책로", "slope_pct": 0.3, "density_dist_m": 5.0,
        "event_level": 0.8, "event_label": "선사문화축제 & 공원 버스킹",
        "events_list": ["선사유적 달빛 산책"], "cafe_interval_m": 22, "transit_walk_min": 4.5, "transit_diversity": 0.9,
        "highlight_tag": "#선사유적공원 #달서문화거리 #월성숲길", "is_landmark": False,
        "coords": [[128.5280, 35.8280], [128.5305, 35.8300], [128.5330, 35.8320]]
    },
    {
        "id": "dg_dalseo_sangin", "dong_name": "대구 상인동", "street_name": "월곡역사공원 대나무숲길",
        "vibe_desc": "울창한 대나무숲과 연못이 어우러진 도심 속 쉼터", "theme": "🎋 대나무·힐링",
        "province": "대구", "sgg": "달서구", "dong": "상인동", "width_m": 3.8, "car_control": 1.0,
        "car_control_label": "공원 보행전용길", "slope_pct": 0.4, "density_dist_m": 5.1,
        "event_level": 0.8, "event_label": "월곡 대나무숲 야간조명 산책",
        "events_list": ["대나무숲 힐링 산책"], "cafe_interval_m": 25, "transit_walk_min": 4.0, "transit_diversity": 0.9,
        "highlight_tag": "#월곡역사공원 #대나무숲길 #도심힐링", "is_landmark": False,
        "coords": [[128.5420, 35.8190], [128.5445, 35.8210], [128.5470, 35.8230]]
    },
    # 남구
    {
        "id": "dg_nam_daemyeong", "dong_name": "대구 대명동", "street_name": "앞산 빨래터공원 & 해맞이길",
        "vibe_desc": "앞산 해넘이전망대와 아늑한 카페거리 산책로", "theme": "🌄 전망·숲",
        "province": "대구", "sgg": "남구", "dong": "대명동", "width_m": 4.6, "car_control": 0.95,
        "car_control_label": "공원 전망 보행데크로", "slope_pct": 1.8, "density_dist_m": 5.1,
        "event_level": 0.9, "event_label": "앞산 빨래터 문화축제 & 야간 버스킹",
        "events_list": ["앞산 해넘이 음악회", "빨래터 플리마켓"],
        "cafe_interval_m": 18, "transit_walk_min": 4.0, "transit_diversity": 0.9,
        "highlight_tag": "#앞산카페거리 #해넘이전망대 #빨래터공원", "is_landmark": True,
        "coords": [[128.5720, 35.8320], [128.5750, 35.8335], [128.5780, 35.8350]]
    },
    {
        "id": "dg_nam_icheon", "dong_name": "대구 이천동", "street_name": "이천동 고미술거리",
        "vibe_desc": "골동품과 예술 소품이 전시된 한적한 문화 골목", "theme": "🏺 고미술·문화",
        "province": "대구", "sgg": "남구", "dong": "이천동", "width_m": 3.6, "car_control": 0.85,
        "car_control_label": "보행안심거리", "slope_pct": 0.3, "density_dist_m": 5.2,
        "event_level": 0.8, "event_label": "이천 고미술 축제 & 벼룩시장",
        "events_list": ["고미술 갤러리 투어"], "cafe_interval_m": 25, "transit_walk_min": 4.5, "transit_diversity": 0.9,
        "highlight_tag": "#이천고미술거리 #골동품골목 #한적한산책", "is_landmark": False,
        "coords": [[128.5960, 35.8500], [128.5985, 35.8515], [128.6010, 35.8530]]
    },
    {
        "id": "dg_nam_bongdeok", "dong_name": "대구 봉덕동", "street_name": "신천 맛길 수변데크로",
        "vibe_desc": "신천 하천변을 따라 시원한 바람을 맞으며 걷는 길", "theme": "🌊 하천·수변",
        "province": "대구", "sgg": "남구", "dong": "봉덕동", "width_m": 4.8, "car_control": 1.0,
        "car_control_label": "신천 수변 보행전용길", "slope_pct": 0.2, "density_dist_m": 5.0,
        "event_level": 0.8, "event_label": "신천 수변 야간 걷기대회",
        "events_list": ["신천 달빛 걷기"], "cafe_interval_m": 22, "transit_walk_min": 3.5, "transit_diversity": 0.95,
        "highlight_tag": "#신천수변공원 #물소리산책 #남구힐링길", "is_landmark": False,
        "coords": [[128.6010, 35.8420], [128.6035, 35.8440], [128.6060, 35.8460]]
    },
    # 북구
    {
        "id": "dg_buk_chimsan", "dong_name": "대구 침산동", "street_name": "침산정 벚꽃 숲길",
        "vibe_desc": "신천 전망과 봄철 벚꽃 터널이 펼쳐지는 명품길", "theme": "🌸 벚꽃·전망",
        "province": "대구", "sgg": "북구", "dong": "침산동", "width_m": 4.2, "car_control": 1.0,
        "car_control_label": "침산공원 보행전용로", "slope_pct": 1.5, "density_dist_m": 5.1,
        "event_level": 0.85, "event_label": "침산정 달빛 산책제",
        "events_list": ["침산 벚꽃 축제"], "cafe_interval_m": 24, "transit_walk_min": 5.0, "transit_diversity": 0.9,
        "highlight_tag": "#침산정 #침산공원 #벚꽃전망길", "is_landmark": False,
        "coords": [[128.5860, 35.8920], [128.5885, 35.8940], [128.5910, 35.8960]]
    },
    {
        "id": "dg_buk_bokhyeon", "dong_name": "대구 복현동", "street_name": "경북대 백양로 캠퍼스길",
        "vibe_desc": "수령 높은 메타세쿼이아 가로수와 잔디밭이 어우러진 낭만길", "theme": "🌲 캠퍼스·가로수",
        "province": "대구", "sgg": "북구", "dong": "복현동", "width_m": 5.5, "car_control": 0.95,
        "car_control_label": "캠퍼스 보행자 전용도로", "slope_pct": 0.3, "density_dist_m": 5.0,
        "event_level": 0.9, "event_label": "대학 축제 & 청년 플리마켓",
        "events_list": ["경북대 가을 숲 산책제"], "cafe_interval_m": 16, "transit_walk_min": 3.0, "transit_diversity": 0.95,
        "highlight_tag": "#경북대백양로 #메타세쿼이아 #캠퍼스산책", "is_landmark": False,
        "coords": [[128.6100, 35.8900], [128.6125, 35.8915], [128.6150, 35.8930]]
    },
    {
        "id": "dg_buk_guam", "dong_name": "대구 구암동", "street_name": "구암서원 옻골 숲길",
        "vibe_desc": "고택 서원과 울창한 솔숲이 어우러진 고즈넉한 힐링길", "theme": "🏯 고택·솔숲",
        "province": "대구", "sgg": "북구", "dong": "구암동", "width_m": 3.8, "car_control": 1.0,
        "car_control_label": "서원 숲 보행전용로", "slope_pct": 0.6, "density_dist_m": 5.2,
        "event_level": 0.8, "event_label": "구암서원 전통 문화체험",
        "events_list": ["서원 고택 야행"], "cafe_interval_m": 30, "transit_walk_min": 5.0, "transit_diversity": 0.85,
        "highlight_tag": "#구암서원 #고택산책 #솔숲힐링", "is_landmark": False,
        "coords": [[128.5620, 35.9280], [128.5645, 35.9300], [128.5670, 35.9320]]
    },
    # 동구
    {
        "id": "dg_dong_yulha", "dong_name": "대구 율하동", "street_name": "율하체육공원 수변생태길",
        "vibe_desc": "금호강 수변과 푸른 잔디밭이 시원하게 펼쳐진 산책로", "theme": "🌊 수변·체육공원",
        "province": "대구", "sgg": "동구", "dong": "율하동", "width_m": 5.0, "car_control": 1.0,
        "car_control_label": "공원 완전 보행전용길", "slope_pct": 0.1, "density_dist_m": 5.0,
        "event_level": 0.85, "event_label": "율하 수변 달빛 버스킹",
        "events_list": ["율하 플리마켓"], "cafe_interval_m": 22, "transit_walk_min": 4.0, "transit_diversity": 0.9,
        "highlight_tag": "#율하체육공원 #금호강자전거산책 #탁트인시야", "is_landmark": False,
        "coords": [[128.6920, 35.8620], [128.6950, 35.8640], [128.6980, 35.8660]]
    },
    {
        "id": "dg_dong_bullo", "dong_name": "대구 불로동", "street_name": "불로동 고분군 초원길",
        "vibe_desc": "삼국시대 고분 사이로 펼쳐진 드넓은 초원 산책로", "theme": "🌾 고분·초원",
        "province": "대구", "sgg": "동구", "dong": "불로동", "width_m": 4.5, "car_control": 1.0,
        "car_control_label": "유적지 보행전용로", "slope_pct": 0.8, "density_dist_m": 5.2,
        "event_level": 0.85, "event_label": "불로 고분군 노을 힐링제",
        "events_list": ["고분군 노을 사진전"], "cafe_interval_m": 28, "transit_walk_min": 5.5, "transit_diversity": 0.85,
        "highlight_tag": "#불로동고분군 #노을명소 #초원힐링산책", "is_landmark": False,
        "coords": [[128.6380, 35.9180], [128.6410, 35.9200], [128.6440, 35.9220]]
    },
    {
        "id": "dg_dong_sincheon", "dong_name": "대구 신천동", "street_name": "동대구역 복합환승 숲길",
        "vibe_desc": "초역세권에 조성된 도심 쌈지공원과 가로수길", "theme": "🚆 역세권·도심",
        "province": "대구", "sgg": "동구", "dong": "신천동", "width_m": 4.2, "car_control": 0.9,
        "car_control_label": "보행우선도로", "slope_pct": 0.2, "density_dist_m": 4.8,
        "event_level": 0.85, "event_label": "동대구 청년 팝업 페스타",
        "events_list": ["동대구 광장 버스킹"], "cafe_interval_m": 12, "transit_walk_min": 2.0, "transit_diversity": 1.0,
        "highlight_tag": "#동대구역직결 #신세계백화점연계 #초역세권보행", "is_landmark": False,
        "coords": [[128.6280, 35.8780], [128.6305, 35.8795], [128.6330, 35.8810]]
    },
    # 달성군
    {
        "id": "dg_dalseong_dasa", "dong_name": "대구 다사읍 (강정보)", "street_name": "디아크 강정보 수변길",
        "vibe_desc": "낙동강과 금호강이 만나는 웅장한 수변과 야경 산책로", "theme": "🌊 강변·야경",
        "province": "대구", "sgg": "달성군", "dong": "다사읍", "width_m": 6.5, "car_control": 1.0,
        "car_control_label": "강변 완전 보행자 전용로", "slope_pct": 0.1, "density_dist_m": 5.1,
        "event_level": 0.95, "event_label": "디아크 야간 미디어파사드 & 버스킹",
        "events_list": ["디아크 달빛 음악회", "강정보 노을 워킹"],
        "cafe_interval_m": 25, "transit_walk_min": 6.0, "transit_diversity": 0.85,
        "highlight_tag": "#디아크 #강정보 #대구최대강변산책로", "is_landmark": True,
        "coords": [[128.4680, 35.8580], [128.4715, 35.8600], [128.4750, 35.8620]]
    },

    # ==================== 서울특별시 ====================
    # 중구
    {
        "id": "se_jung_jeongdong", "dong_name": "서울 정동", "street_name": "덕수궁 돌담길 & 정동길",
        "vibe_desc": "아름다운 가로수와 근대 역사가 숨쉬는 명품 보행길", "theme": "🍂 역사·돌담",
        "province": "서울", "sgg": "중구", "dong": "정동", "width_m": 4.8, "car_control": 1.0,
        "car_control_label": "차없는거리 & 보행전용구간", "slope_pct": 0.4, "density_dist_m": 5.1,
        "event_level": 0.95, "event_label": "정동 야행 & 국악 버스킹",
        "events_list": ["정동 문화축제", "서울시립미술관 야외 전시", "돌담길 버스킹"],
        "cafe_interval_m": 22, "transit_walk_min": 2.0, "transit_diversity": 1.0,
        "highlight_tag": "#덕수궁돌담길 #정동극장 #도심속가로수숲", "is_landmark": True,
        "coords": [[126.9748, 37.5658], [126.9725, 37.5670], [126.9698, 37.5682]]
    },
    {
        "id": "se_jung_pil", "dong_name": "서울 필동", "street_name": "남산골 한옥마을길",
        "vibe_desc": "남산 자락 한옥 정원과 전통 연못이 펼쳐진 도심 오아시스", "theme": "🏯 한옥·남산",
        "province": "서울", "sgg": "중구", "dong": "필동", "width_m": 4.2, "car_control": 1.0,
        "car_control_label": "한옥마을 보행전용로", "slope_pct": 0.8, "density_dist_m": 5.0,
        "event_level": 0.9, "event_label": "남산골 전통 공예 축제 & 달빛 야행",
        "events_list": ["남산골 전통 국악 공연"], "cafe_interval_m": 20, "transit_walk_min": 3.0, "transit_diversity": 1.0,
        "highlight_tag": "#남산골한옥마을 #충무로역세권 #전통정원산책", "is_landmark": False,
        "coords": [[126.9930, 37.5585], [126.9950, 37.5595], [126.9970, 37.5605]]
    },
    # 종로구
    {
        "id": "se_jongno_gahoe", "dong_name": "서울 가회동 (북촌)", "street_name": "북촌 한옥마을 8경 골목",
        "vibe_desc": "기와지붕 너머 서울 도심이 한눈에 보이는 명품 한옥길", "theme": "🏯 전통·한옥",
        "province": "서울", "sgg": "종로구", "dong": "가회동", "width_m": 3.6, "car_control": 0.95,
        "car_control_label": "보행자 전용 안심구역", "slope_pct": 2.5, "density_dist_m": 4.8,
        "event_level": 0.9, "event_label": "북촌 공예주간 & 한옥 오픈하우스",
        "events_list": ["북촌 한옥 야행", "전통 공예 체험 투어"],
        "cafe_interval_m": 22, "transit_walk_min": 5.0, "transit_diversity": 0.9,
        "highlight_tag": "#북촌8경 #한옥전망대 #조용한보행구역", "is_landmark": True,
        "coords": [[126.9830, 37.5820], [126.9845, 37.5835], [126.9860, 37.5850]]
    },
    {
        "id": "se_jongno_tongui", "dong_name": "서울 통의동 (서촌)", "street_name": "자하문로 한옥 골목길",
        "vibe_desc": "인왕산 자락의 고즈넉한 옛 골목과 갤러리", "theme": "🌿 한옥·골목",
        "province": "서울", "sgg": "종로구", "dong": "통의동", "width_m": 3.4, "car_control": 0.9,
        "car_control_label": "보행자 우선 안심구역", "slope_pct": 0.8, "density_dist_m": 4.9,
        "event_level": 0.85, "event_label": "서촌 골목 예술제 & 독립서점 투어",
        "events_list": ["서촌 예술산책", "보안여관 야외 전시"],
        "cafe_interval_m": 18, "transit_walk_min": 3.5, "transit_diversity": 0.95,
        "highlight_tag": "#보안여관 #인왕산자락 #한옥미로산책", "is_landmark": True,
        "coords": [[126.9720, 37.5790], [126.9715, 37.5815], [126.9710, 37.5840]]
    },
    {
        "id": "se_jongno_ikseon", "dong_name": "서울 익선동", "street_name": "익선동 한옥 갤러리골목",
        "vibe_desc": "100년 된 도시형 한옥과 트렌디한 카페가 융합된 골목", "theme": "☕ 한옥·카페",
        "province": "서울", "sgg": "종로구", "dong": "익선동", "width_m": 2.8, "car_control": 1.0,
        "car_control_label": "완전 보행전용 골목", "slope_pct": 0.1, "density_dist_m": 4.5,
        "event_level": 0.95, "event_label": "익선 골목 팝업 페스티벌",
        "events_list": ["익선 한옥 플리마켓"], "cafe_interval_m": 8, "transit_walk_min": 2.0, "transit_diversity": 1.0,
        "highlight_tag": "#익선동한옥마을 #종로3가역직결 #골목카페투어", "is_landmark": False,
        "coords": [[126.9890, 37.5730], [126.9910, 37.5740], [126.9930, 37.5750]]
    },
    # 성동구
    {
        "id": "se_seongdong_seongsu", "dong_name": "서울 성수동", "street_name": "서울숲 아뜰리에길",
        "vibe_desc": "도심 숲과 로컬 공방이 공존하는 산책로", "theme": "🌲 숲·로컬",
        "province": "서울", "sgg": "성동구", "dong": "성수동1가", "width_m": 4.2, "car_control": 1.0,
        "car_control_label": "보행자 전용도로", "slope_pct": 0.5, "density_dist_m": 5.0,
        "event_level": 1.0, "event_label": "서울숲 플리마켓 & 친환경 팝업",
        "events_list": ["서울숲 아뜰리에 마켓", "친환경 라이프스타일 팝업"],
        "cafe_interval_m": 15, "transit_walk_min": 3.0, "transit_diversity": 1.0,
        "highlight_tag": "#테디스오븐 #서울숲그늘 #공방골목", "is_landmark": True,
        "coords": [[127.0425, 37.5442], [127.0438, 37.5451], [127.0452, 37.5460]]
    },
    {
        "id": "se_seongdong_yeonmu", "dong_name": "서울 성수동2가", "street_name": "연무장길 팝업 스트리트",
        "vibe_desc": "글로벌 브랜드 팝업과 붉은 벽돌 공장이 어우러진 거리", "theme": "🎪 팝업·패션",
        "province": "서울", "sgg": "성동구", "dong": "성수동2가", "width_m": 4.5, "car_control": 0.9,
        "car_control_label": "보행우선특화거리", "slope_pct": 0.2, "density_dist_m": 4.7,
        "event_level": 1.0, "event_label": "성수 팝업 페스티벌 & 디자인위크",
        "events_list": ["성수 아트 팝업", "성수 로컬 디자인 마켓"],
        "cafe_interval_m": 10, "transit_walk_min": 3.0, "transit_diversity": 1.0,
        "highlight_tag": "#연무장길 #성수팝업스토어 #붉은벽돌거리", "is_landmark": False,
        "coords": [[127.0540, 37.5420], [127.0570, 37.5435], [127.0600, 37.5450]]
    },
    # 마포구
    {
        "id": "se_mapo_yeonnam", "dong_name": "서울 연남동", "street_name": "경의선숲길 (연트럴파크)",
        "vibe_desc": "철길을 공원으로 가꾼 도심 속 잔디밭 보행길", "theme": "🌲 공원·힐링",
        "province": "서울", "sgg": "마포구", "dong": "연남동", "width_m": 4.5, "car_control": 1.0,
        "car_control_label": "공원 보행전용로", "slope_pct": 0.3, "density_dist_m": 5.2,
        "event_level": 0.9, "event_label": "연트럴 야외 어쿠스틱 버스킹",
        "events_list": ["연트럴 주말 플리마켓", "잔디밭 버스킹"],
        "cafe_interval_m": 20, "transit_walk_min": 2.0, "transit_diversity": 1.0,
        "highlight_tag": "#랜디스도넛 #경의선숲길 #초역세권공원길", "is_landmark": True,
        "coords": [[126.9245, 37.5595], [126.9230, 37.5620], [126.9215, 37.5645]]
    },
    {
        "id": "se_mapo_hapjeong", "dong_name": "서울 합정동", "street_name": "토정로 독립서점 골목",
        "vibe_desc": "당인리 발전소 공원과 아늑한 출판 독립서점이 모인 길", "theme": "📚 책·문화",
        "province": "서울", "sgg": "마포구", "dong": "합정동", "width_m": 3.8, "car_control": 0.85,
        "car_control_label": "보행자 안심도로", "slope_pct": 0.4, "density_dist_m": 5.1,
        "event_level": 0.85, "event_label": "마포 독립출판 북마켓",
        "events_list": ["합정 야간 북토크"], "cafe_interval_m": 18, "transit_walk_min": 4.0, "transit_diversity": 0.95,
        "highlight_tag": "#당인리발전소공원 #독립서점골목 #조용한책산책", "is_landmark": False,
        "coords": [[126.9120, 37.5480], [126.9145, 37.5495], [126.9170, 37.5510]]
    },
    # 용산구
    {
        "id": "se_yongsan_hangang", "dong_name": "서울 한강로동 (용리단길)", "street_name": "용리단 감성골목길",
        "vibe_desc": "이국적인 맛집과 감각적인 카페가 줄지은 보행 골목", "theme": "🍽️ 미식·트렌드",
        "province": "서울", "sgg": "용산구", "dong": "한강로2가", "width_m": 4.0, "car_control": 0.85,
        "car_control_label": "보행자 안심골목", "slope_pct": 0.2, "density_dist_m": 4.8,
        "event_level": 0.95, "event_label": "용리단 로컬 고메 페스타",
        "events_list": ["용리단 골목 미식 투어"], "cafe_interval_m": 12, "transit_walk_min": 2.5, "transit_diversity": 1.0,
        "highlight_tag": "#용리단길 #신용산역세권 #트렌디골목", "is_landmark": False,
        "coords": [[126.9700, 37.5300], [126.9720, 37.5315], [126.9740, 37.5330]]
    },
    # 송파구
    {
        "id": "se_songpa_seokchon", "dong_name": "서울 석촌동", "street_name": "석촌호수 벚꽃 수변길",
        "vibe_desc": "호수를 둘러싼 벚나무 터널과 롯데월드타워 전망", "theme": "🌸 호수·벚꽃",
        "province": "서울", "sgg": "송파구", "dong": "석촌동", "width_m": 5.5, "car_control": 1.0,
        "car_control_label": "호수 완전 보행전용길", "slope_pct": 0.1, "density_dist_m": 4.9,
        "event_level": 1.0, "event_label": "석촌호수 벚꽃축제 & 루미나리에 야경",
        "events_list": ["석촌호수 벚꽃 버스킹", "호수 낭만 음악회"],
        "cafe_interval_m": 16, "transit_walk_min": 3.0, "transit_diversity": 1.0,
        "highlight_tag": "#석촌호수 #송리단길연계 #벚꽃수변산책", "is_landmark": True,
        "coords": [[127.1020, 37.5080], [127.1055, 37.5095], [127.1090, 37.5110]]
    },
    # 강남구
    {
        "id": "se_gangnam_sinsa", "dong_name": "서울 신사동", "street_name": "신사 가로수길 & 세로수길",
        "vibe_desc": "은행나무 가로수 아래 펼쳐진 글로벌 패션과 카페 골목", "theme": "🍂 패션·가로수",
        "province": "서울", "sgg": "강남구", "dong": "신사동", "width_m": 4.8, "car_control": 0.9,
        "car_control_label": "가로수 특화 보행길", "slope_pct": 0.3, "density_dist_m": 4.8,
        "event_level": 0.95, "event_label": "가로수길 패션위크 & 팝업 페스타",
        "events_list": ["신사 가로수 아트마켓"], "cafe_interval_m": 14, "transit_walk_min": 3.5, "transit_diversity": 1.0,
        "highlight_tag": "#신사가로수길 #은행나무거리 #세로수길카페", "is_landmark": False,
        "coords": [[127.0200, 37.5180], [127.0225, 37.5200], [127.0250, 37.5220]]
    },

    # ==================== 부산광역시 ====================
    # 해운대구
    {
        "id": "bs_haeundae_u", "dong_name": "부산 우동", "street_name": "해운대 구남로 보행광장",
        "vibe_desc": "해운대 해변으로 이어지는 광폭 보행자 문화거리", "theme": "🏖️ 광장·해변",
        "province": "부산", "sgg": "해운대구", "dong": "우동", "width_m": 6.5, "car_control": 1.0,
        "car_control_label": "완전 보행전용 광장거리", "slope_pct": 0.4, "density_dist_m": 5.1,
        "event_level": 1.0, "event_label": "상설 야외 버스킹 & 해변 음악제",
        "events_list": ["구남로 버스킹 페스타", "해운대 아트마켓"],
        "cafe_interval_m": 16, "transit_walk_min": 1.5, "transit_diversity": 1.0,
        "highlight_tag": "#해운대역직결 #초역세권광폭보도 #야외버스킹존", "is_landmark": True,
        "coords": [[129.1585, 35.1605], [129.1598, 35.1618], [129.1610, 35.1630]]
    },
    {
        "id": "bs_haeundae_jung", "dong_name": "부산 중동", "street_name": "달맞이길 해송 숲길",
        "vibe_desc": "해운대 바다를 굽어보며 해송 숲길을 걷는 힐링 코스", "theme": "🌲 해송·바다전망",
        "province": "부산", "sgg": "해운대구", "dong": "중동", "width_m": 4.5, "car_control": 0.9,
        "car_control_label": "해안전망 보행데크로", "slope_pct": 2.2, "density_dist_m": 5.2,
        "event_level": 0.9, "event_label": "달맞이 언덕 예술제 & 갤러리 투어",
        "events_list": ["달맞이길 달빛 걷기", "해월정 버스킹"],
        "cafe_interval_m": 22, "transit_walk_min": 5.5, "transit_diversity": 0.85,
        "highlight_tag": "#달맞이길 #해월정 #해운대바다전망", "is_landmark": True,
        "coords": [[129.1720, 35.1610], [129.1750, 35.1625], [129.1780, 35.1640]]
    },
    # 동래구
    {
        "id": "bs_dongnae_oncheon", "dong_name": "부산 온천동", "street_name": "온천천 시민 벚꽃길",
        "vibe_desc": "부산 시민들이 가장 사랑하는 평지 하천 힐링 산책로", "theme": "🌸 하천·수변",
        "province": "부산", "sgg": "동래구", "dong": "온천동", "width_m": 5.2, "car_control": 1.0,
        "car_control_label": "하천변 완전 보행전용길 (차량 차단)", "slope_pct": 0.2, "density_dist_m": 5.0,
        "event_level": 0.9, "event_label": "온천천 봄꽃축제 & 수변 버스킹",
        "events_list": ["온천천 벚꽃 버스킹", "수변 시민 나눔장터"],
        "cafe_interval_m": 25, "transit_walk_min": 2.5, "transit_diversity": 1.0,
        "highlight_tag": "#온천천카페거리 #완전평지수변로 #부산시민힐링길", "is_landmark": True,
        "coords": [[129.0830, 35.2070], [129.0865, 35.2045], [129.0900, 35.2020]]
    },
    # 영도구
    {
        "id": "bs_yeongdo_yeongseon", "dong_name": "부산 영선동", "street_name": "영도 흰여울 절벽길",
        "vibe_desc": "남항 바다 절벽을 따라 걷는 파도 소리 길", "theme": "🌊 바다·해안",
        "province": "부산", "sgg": "영도구", "dong": "영선동4가", "width_m": 2.8, "car_control": 1.0,
        "car_control_label": "해안절벽 보행전용로", "slope_pct": 2.2, "density_dist_m": 5.3,
        "event_level": 0.85, "event_label": "흰여울 해안 예술제 & 골목 사진전",
        "events_list": ["흰여울 바다 노을 산책", "골목 갤러리 페스타"],
        "cafe_interval_m": 22, "transit_walk_min": 6.0, "transit_diversity": 0.85,
        "highlight_tag": "#흰여울문화마을 #오션뷰절벽길 #한국의산토리니", "is_landmark": True,
        "coords": [[129.0435, 35.0780], [129.0450, 35.0795], [129.0470, 35.0810]]
    },
    # 수영구
    {
        "id": "bs_suyeong_millak", "dong_name": "부산 민락동", "street_name": "민락 수변공원 & 광안대교 뷰로드",
        "vibe_desc": "광안대교의 환상적인 야경과 바다 바람을 즐기는 산책길", "theme": "🌉 야경·해변",
        "province": "부산", "sgg": "수영구", "dong": "민락동", "width_m": 5.5, "car_control": 1.0,
        "car_control_label": "수변공원 보행전용로", "slope_pct": 0.1, "density_dist_m": 5.0,
        "event_level": 0.95, "event_label": "밀락더마켓 아트 페스타 & 버스킹",
        "events_list": ["광안리 드론라이트쇼 관람", "수변 버스킹"],
        "cafe_interval_m": 15, "transit_walk_min": 4.5, "transit_diversity": 0.95,
        "highlight_tag": "#밀락더마켓 #광안대교야경 #민락수변공원", "is_landmark": False,
        "coords": [[129.1320, 35.1540], [129.1350, 35.1560], [129.1380, 35.1580]]
    },
    # 부산진구
    {
        "id": "bs_busanjin_jeonpo", "dong_name": "부산 전포동", "street_name": "전포 카페거리 & 사잇길",
        "vibe_desc": "철물점 골목이 뉴욕타임스 추천 글로벌 카페거리로 탈바꿈한 곳", "theme": "☕ 카페·골목",
        "province": "부산", "sgg": "부산진구", "dong": "전포동", "width_m": 3.8, "car_control": 0.85,
        "car_control_label": "보행자 안심거리", "slope_pct": 0.8, "density_dist_m": 4.8,
        "event_level": 0.95, "event_label": "전포 카페거리 축제 & 골목 플리마켓",
        "events_list": ["전포 골목 커피 페스티벌"], "cafe_interval_m": 10, "transit_walk_min": 3.0, "transit_diversity": 1.0,
        "highlight_tag": "#전포카페거리 #뉴욕타임스추천 #서면역세권", "is_landmark": True,
        "coords": [[129.0620, 35.1550], [129.0645, 35.1565], [129.0670, 35.1580]]
    },

    # ==================== 경기 / 수원 ====================
    {
        "id": "gg_suwon_haenggung", "dong_name": "수원 행궁동", "street_name": "수원화성 행리단 성곽길",
        "vibe_desc": "유네스코 화성 성곽을 따라 걷는 평화로운 보행로", "theme": "🏯 성곽·역사",
        "province": "수원/경기", "sgg": "팔달구", "dong": "행궁동", "width_m": 4.6, "car_control": 0.9,
        "car_control_label": "성곽 보행전용 & 안심도로", "slope_pct": 0.6, "density_dist_m": 5.1,
        "event_level": 0.95, "event_label": "수원화성 문화제 & 행궁 야간 플리마켓",
        "events_list": ["화성 성곽 달빛 산책", "행궁 청년 예술마켓"],
        "cafe_interval_m": 16, "transit_walk_min": 4.0, "transit_diversity": 0.9,
        "highlight_tag": "#수원화성 #행리단길 #성곽전망산책로", "is_landmark": True,
        "coords": [[127.0145, 37.2835], [127.0168, 37.2852], [127.0190, 37.2870]]
    },
    {
        "id": "gg_suwon_gwanggyo", "dong_name": "수원 이의동", "street_name": "광교호수공원 어반레비길",
        "vibe_desc": "국내 최대 도심 호수공원 수변 데크로드와 야경", "theme": "🌊 호수·야경",
        "province": "수원/경기", "sgg": "영통구", "dong": "이의동", "width_m": 6.0, "car_control": 1.0,
        "car_control_label": "호수 완전 보행전용로", "slope_pct": 0.2, "density_dist_m": 5.0,
        "event_level": 0.9, "event_label": "광교 어반레비 재즈 페스타",
        "events_list": ["광교 호수 야간 산책제"], "cafe_interval_m": 20, "transit_walk_min": 3.5, "transit_diversity": 0.95,
        "highlight_tag": "#광교호수공원 #어반레비 #수변데크로드", "is_landmark": True,
        "coords": [[127.0600, 37.2820], [127.0635, 37.2840], [127.0670, 37.2860]]
    },

    # ==================== 대전광역시 ====================
    {
        "id": "dj_dong_soje", "dong_name": "대전 소제동", "street_name": "철도관사촌 골목길",
        "vibe_desc": "100년 된 철도관사와 대나무 숲이 어우러진 정취", "theme": "🚂 근대·역사",
        "province": "대전", "sgg": "동구", "dong": "소제동", "width_m": 3.5, "car_control": 0.85,
        "car_control_label": "보행자 안심 골목", "slope_pct": 0.3, "density_dist_m": 5.1,
        "event_level": 0.9, "event_label": "소제 골목 아트위크 & 공방 마켓",
        "events_list": ["소제동 관사촌 투어", "대나무숲 야간 산책"],
        "cafe_interval_m": 18, "transit_walk_min": 4.5, "transit_diversity": 0.95,
        "highlight_tag": "#대전역뒤편 #철도관사촌 #대나무숲카페골목", "is_landmark": True,
        "coords": [[127.4370, 36.3320], [127.4390, 36.3335], [127.4410, 36.3350]]
    },

    # ==================== 광주광역시 ====================
    {
        "id": "gj_nam_yangnim", "dong_name": "광주 양림동", "street_name": "펭귄마을 역사문화골목",
        "vibe_desc": "근대 선교사 가옥과 아기자기한 예술 정원의 조화", "theme": "🐧 예술·역사",
        "province": "광주", "sgg": "남구", "dong": "양림동", "width_m": 3.6, "car_control": 0.9,
        "car_control_label": "골목 보행전용구간", "slope_pct": 0.7, "density_dist_m": 5.0,
        "event_level": 0.95, "event_label": "양림 골목 비엔날레 & 공예 마켓",
        "events_list": ["펭귄마을 업사이클링 마켓", "근대역사 가옥 투어"],
        "cafe_interval_m": 20, "transit_walk_min": 5.0, "transit_diversity": 0.9,
        "highlight_tag": "#펭귄마을 #이장우가옥 #광주근대역사산책", "is_landmark": True,
        "coords": [[126.9160, 35.1410], [126.9180, 35.1425], [126.9200, 35.1440]]
    },

    # ==================== 전북특별자치도 ====================
    {
        "id": "jb_jeonju_gyodong", "dong_name": "전주 교동", "street_name": "전주 한옥마을 태조로",
        "vibe_desc": "경기전과 전동성당을 잇는 국내 최대 한옥 보행로", "theme": "🏯 전통·한옥",
        "province": "전북", "sgg": "전주시", "dong": "교동", "width_m": 6.0, "car_control": 1.0,
        "car_control_label": "주말 차없는거리", "slope_pct": 0.2, "density_dist_m": 4.9,
        "event_level": 1.0, "event_label": "전주 한옥마을 경기전 야행",
        "events_list": ["전주 야경 달빛 걷기", "전통 디저트 마켓"],
        "cafe_interval_m": 14, "transit_walk_min": 5.5, "transit_diversity": 0.9,
        "highlight_tag": "#경기전 #전동성당 #국내최대한옥보행길", "is_landmark": True,
        "coords": [[127.1480, 35.8140], [127.1510, 35.8150], [127.1540, 35.8160]]
    },

    # ==================== 강원특별자치도 ====================
    {
        "id": "gw_gangneung_chodang", "dong_name": "강릉 초당동", "street_name": "초당 솔밭 솔향길",
        "vibe_desc": "바다 솔숲 향기를 맡으며 걷는 힐링 산책로", "theme": "🌲 솔숲·힐링",
        "province": "강원", "sgg": "강릉시", "dong": "초당동", "width_m": 4.5, "car_control": 0.9,
        "car_control_label": "솔숲 보행전용 데크길", "slope_pct": 0.2, "density_dist_m": 5.2,
        "event_level": 0.9, "event_label": "허균·허난설헌 솔숲 문화제",
        "events_list": ["솔밭 낭만 버스킹", "고택 다도 체험"],
        "cafe_interval_m": 22, "transit_walk_min": 5.5, "transit_diversity": 0.85,
        "highlight_tag": "#허균허난설헌기념공원 #솔향가득숲길 #초당고택산책", "is_landmark": True,
        "coords": [[128.9220, 37.7900], [128.9245, 37.7915], [128.9270, 37.7930]]
    },

    # ==================== 제주특별자치도 ====================
    {
        "id": "jj_jeju_samdo", "dong_name": "제주 삼도동", "street_name": "관덕정 원도심 돌담길",
        "vibe_desc": "제주의 옛 성안마을 돌담을 따라 걷는 산책길", "theme": "🍊 돌담·원도심",
        "province": "제주", "sgg": "제주시", "dong": "삼도2동", "width_m": 4.2, "car_control": 0.9,
        "car_control_label": "원도심 보행우선도로", "slope_pct": 0.2, "density_dist_m": 5.2,
        "event_level": 0.9, "event_label": "성안올레 걷기 & 관덕정 야행",
        "events_list": ["제주 원도심 야간 투어", "성안 플리마켓"],
        "cafe_interval_m": 25, "transit_walk_min": 3.5, "transit_diversity": 0.95,
        "highlight_tag": "#관덕정 #제주목관아 #원도심돌담길", "is_landmark": True,
        "coords": [[126.5215, 33.5130], [126.5238, 33.5142], [126.5260, 33.5155]]
    }
]

# 1. 100% 전수 채점 수행
for item in candidates:
    calculate_sub_scores(item)

# 점수 내림차순 정렬
candidates.sort(key=lambda x: x["score_100"], reverse=True)

# 2. 전국 상위 25% 컷오프 기준 점수 산출
n_total = len(candidates)
cutoff_idx = max(1, int(n_total * 0.25))
cutoff_score = candidates[cutoff_idx - 1]["score_100"]

print(f"전체 후보군: {n_total}개, 상위 25% 컷오프 점수: {cutoff_score}점")

# 3. 필터링 로직:
#   (1) 상위 25% 이상
#   (2) 구(sgg)별 최소 3개 보장 (Floor 3 Guarantee)
#   (3) is_landmark == True (수성못 등 대표 명소 무조건 포함)
selected_map = {}

# (1) 대표 명소 우선 포함
for item in candidates:
    if item.get("is_landmark", False):
        selected_map[item["id"]] = item

# (2) 구별 최소 3개 확보 (점수순)
sgg_groups = {}
for item in candidates:
    key = f"{item['province']}_{item['sgg']}"
    sgg_groups.setdefault(key, []).append(item)

for key, group in sgg_groups.items():
    top3 = group[:3]
    for item in top3:
        selected_map[item["id"]] = item

# (3) 상위 25% 고득점 추가
for item in candidates:
    if item["score_100"] >= cutoff_score:
        selected_map[item["id"]] = item

final_list = list(selected_map.values())
final_list.sort(key=lambda x: x["score_100"], reverse=True)

print(f"최종 선별된 전국 동네 수: {len(final_list)}개")

# 4. GeoJSON FeatureCollection 변환
features = []
for item in final_list:
    coords = item.pop("coords")
    feat = {
        "type": "Feature",
        "properties": item,
        "geometry": {
            "type": "LineString",
            "coordinates": coords
        }
    }
    features.append(feat)

geojson_data = {
    "type": "FeatureCollection",
    "features": features
}

output_path = os.path.join(os.path.dirname(__file__), "..", "data", "streets.geojson")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(geojson_data, f, ensure_ascii=False, indent=2)

print(f"성공적으로 {output_path} 파일이 생성되었습니다.")
