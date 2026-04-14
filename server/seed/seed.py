"""
Seed script — migrates hardcoded data from index.html into MySQL.
Usage: cd server && python seed/seed.py
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymysql
import config

# ━━ COMPANY TYPES ━━
COMPANY_TYPES = [
    ("large", "대기업", 0.04, "대기업 평균 4%", 90),
    ("mid", "중견기업", 0.027, "중견기업 평균 2.7%", 70),
    ("public", "공기업", 0.03, "공기업 평균 3%", 95),
    ("startup", "스타트업", 0.10, "스타트업 평균 10%", 30),
    ("foreign", "외국계", 0.05, "외국계 평균 5%", 60),
    ("freelance", "프리랜서", 0.02, "프리랜서 평균 2%", 20),
]

# ━━ BENEFIT PRESETS ━━
BEN_PRESETS = {
    "large": [
        {"key": "meal", "name": "식대 지원 (3식)", "val": 360, "cat": "perks", "badge": "est", "checked": True},
        {"key": "transport", "name": "교통비/주차비", "val": 120, "cat": "perks", "badge": "est", "checked": True},
        {"key": "welfare", "name": "복지포인트/선택복지", "val": 200, "cat": "perks", "badge": "est", "checked": True},
        {"key": "bonus", "name": "성과급/인센티브", "val": 300, "cat": "compensation", "badge": "est", "checked": False},
        {"key": "health", "name": "건강검진 (본인+가족)", "val": 100, "cat": "health", "badge": "est", "checked": True},
        {"key": "housing", "name": "사내대출 이자절감", "val": 200, "cat": "perks", "badge": "est", "checked": True},
        {"key": "child_edu", "name": "자녀 학자금", "val": 300, "cat": "family", "badge": "est", "checked": False},
        {"key": "event", "name": "경조사 지원", "val": 50, "cat": "family", "badge": "est", "checked": True},
    ],
    "mid": [
        {"key": "meal", "name": "식대 지원", "val": 300, "cat": "perks", "badge": "est", "checked": True},
        {"key": "transport", "name": "교통비", "val": 60, "cat": "perks", "badge": "est", "checked": True},
        {"key": "health", "name": "건강검진", "val": 50, "cat": "health", "badge": "est", "checked": True},
        {"key": "event", "name": "경조사 지원", "val": 30, "cat": "family", "badge": "est", "checked": True},
    ],
    "public": [
        {"key": "meal", "name": "식대 지원 (3식)", "val": 360, "cat": "perks", "badge": "est", "checked": True},
        {"key": "transport", "name": "교통비", "val": 120, "cat": "perks", "badge": "est", "checked": True},
        {"key": "welfare", "name": "복지포인트/선택복지", "val": 250, "cat": "perks", "badge": "est", "checked": True},
        {"key": "health", "name": "건강검진", "val": 80, "cat": "health", "badge": "est", "checked": True},
        {"key": "housing", "name": "사내대출 이자절감", "val": 250, "cat": "perks", "badge": "est", "checked": True},
        {"key": "child_edu", "name": "자녀 학자금", "val": 400, "cat": "family", "badge": "est", "checked": False},
        {"key": "edu", "name": "교육비/자기개발비", "val": 100, "cat": "growth", "badge": "est", "checked": True},
        {"key": "event", "name": "경조사 지원", "val": 50, "cat": "family", "badge": "est", "checked": True},
    ],
    "startup": [
        {"key": "meal", "name": "식대 지원 (3식)", "val": 360, "cat": "perks", "badge": "est", "checked": True},
        {"key": "stock", "name": "스톡옵션/RSU 기대값", "val": 500, "cat": "compensation", "badge": "est", "checked": False},
    ],
    "foreign": [
        {"key": "meal", "name": "식대 지원 (3식)", "val": 360, "cat": "perks", "badge": "est", "checked": True},
        {"key": "transport", "name": "교통비", "val": 100, "cat": "perks", "badge": "est", "checked": True},
        {"key": "welfare", "name": "복지포인트", "val": 150, "cat": "perks", "badge": "est", "checked": True},
        {"key": "bonus", "name": "성과급/인센티브", "val": 500, "cat": "compensation", "badge": "est", "checked": False},
        {"key": "health", "name": "건강검진", "val": 150, "cat": "health", "badge": "est", "checked": True},
        {"key": "edu", "name": "교육비 (도서, 세미나)", "val": 200, "cat": "growth", "badge": "est", "checked": True},
    ],
    "freelance": [],
}

# ━━ COMPANIES ━━
COMPANIES = [
    {
        "id": "cj", "name": "CJ그룹",
        "aliases": ["CJ", "cj", "씨제이", "CJ주식회사"],
        "type": "large", "industry": "식품/유통/엔터", "logo": "CJ",
        "careersUrl": "https://recruit.cj.net/recruit/culture/welfare",
        "benefits": [
            {"key": "meal", "name": "구내식당 (아침·점심·저녁 100%)", "val": 720, "cat": "perks", "badge": "auto", "note": "일 30,000원 × 240일 (한끼 10,000원 × 3끼)"},
            {"key": "cafe_point", "name": "카페테리아 포인트", "val": 200, "cat": "perks", "badge": "auto"},
            {"key": "commute_sup", "name": "출퇴근 셔틀 + 야근택시", "val": 120, "cat": "perks", "badge": "est"},
            {"key": "event", "name": "경조사 지원", "val": 50, "cat": "family", "badge": "est"},
            {"key": "health", "name": "건강검진 (본인+가족)", "val": 100, "cat": "health", "badge": "auto"},
            {"key": "medical", "name": "의료비 지원", "val": 100, "cat": "health", "badge": "est"},
            {"key": "fitness", "name": "피트니스 지원", "val": 60, "cat": "health", "badge": "est"},
            {"key": "housing", "name": "주택대부 이자절감", "val": 200, "cat": "perks", "badge": "est"},
            {"key": "resort", "name": "프리미엄 숙소 할인", "val": 50, "cat": "leisure", "badge": "est"},
            {"key": "lang", "name": "어학시험 응시료", "val": 15, "cat": "growth", "badge": "auto"},
            {"key": "child_edu", "name": "자녀 학자금", "val": 300, "cat": "family", "badge": "auto", "note": "초·중·고·대학"},
            {"key": "parenting", "name": "임신·출산·육아 지원", "val": 0, "cat": "family", "badge": "auto", "qual": True, "qualText": "키즈빌 운영, 배우자 출산휴가, 최대 2년 육아휴직"},
            {"key": "wedding", "name": "결혼 혜택", "val": 0, "cat": "family", "badge": "auto", "qual": True, "qualText": "웨딩카 제공, 사내 인재원 웨딩홀 대관"},
            {"key": "discount", "name": "계열사 40% 할인", "val": 100, "cat": "perks", "badge": "est", "note": "올리브영, CGV 등"},
            {"key": "tving", "name": "티빙 이용권", "val": 17, "cat": "leisure", "badge": "auto"},
            {"key": "travel", "name": "여행 지원", "val": 80, "cat": "leisure", "badge": "est"},
            {"key": "club", "name": "사내 동호회", "val": 30, "cat": "leisure", "badge": "est"},
            {"key": "creative_leave", "name": "창의휴가 (근속 시 2주 유급)", "val": 0, "cat": "time_off", "badge": "auto", "qual": True, "qualText": "3·5·7·10년 근속 시 2주간 유급 휴가"},
        ],
        "workStyle": {"remote": False, "flex": False, "unlimitedPTO": False, "refreshLeave": "3·5·7·10년 근속 시 2주 유급", "overtime": "일반적 대기업 수준"},
    },
    {
        "id": "toss", "name": "토스 (비바리퍼블리카)",
        "aliases": ["토스", "toss", "Toss", "비바리퍼블리카", "비바"],
        "type": "startup", "industry": "핀테크", "logo": "T",
        "careersUrl": "https://toss.im/career/culture",
        "benefits": [
            {"key": "meal", "name": "법인카드 식사 (점심+저녁 100%)", "val": 720, "cat": "perks", "badge": "auto", "note": "일 30,000원 × 240일 (한끼 10,000원 × 3끼)"},
            {"key": "fitness_comm", "name": "체력단련비+통신비 (매월)", "val": 120, "cat": "perks", "badge": "auto"},
            {"key": "insurance", "name": "직장 단체보험 (가족 포함)", "val": 150, "cat": "health", "badge": "auto"},
            {"key": "salon", "name": "사내 헤어살롱", "val": 30, "cat": "health", "badge": "est"},
            {"key": "cafe", "name": "사내 카페 무료", "val": 60, "cat": "work_env", "badge": "est"},
            {"key": "housing", "name": "주택자금 무이자 1억", "val": 350, "cat": "perks", "badge": "auto", "note": "시중 3.5% 기준 이자절감"},
            {"key": "edu", "name": "업무 교육비 100%", "val": 100, "cat": "growth", "badge": "auto", "note": "도서, 세미나 무제한"},
            {"key": "hardware", "name": "최고급 장비 제공", "val": 100, "cat": "work_env", "badge": "est"},
            {"key": "flex", "name": "유연 출퇴근+원격근무", "val": 0, "cat": "flexibility", "badge": "auto", "qual": True, "qualText": "유연한 출퇴근 시간, 원격 근무 가능"},
            {"key": "unlimited_pto", "name": "자율 휴가 (승인 불필요)", "val": 0, "cat": "time_off", "badge": "auto", "qual": True, "qualText": "별도 승인 없는 자율 휴가"},
            {"key": "refresh", "name": "리프레시 휴가 (3년마다 1개월)", "val": 0, "cat": "time_off", "badge": "auto", "qual": True, "qualText": "근속 3년마다 1개월 유급 휴가"},
        ],
        "workStyle": {"remote": True, "flex": True, "unlimitedPTO": True, "refreshLeave": "3년마다 1개월 유급", "overtime": "자율 (성과 중심)"},
    },
    {
        "id": "cj_cheiljedang", "name": "CJ제일제당",
        "aliases": ["CJ제일제당", "제일제당", "cj_cheiljedang"],
        "type": "large", "industry": "식품/바이오", "logo": "CJ",
        "careersUrl": "https://recruit.cj.net/",
        "benefits": [],
        "workStyle": {"remote": False, "flex": False, "unlimitedPTO": False, "overtime": "일반적 대기업 수준"},
    },
    {
        "id": "cj_enm", "name": "CJ ENM",
        "aliases": ["CJ ENM", "CJ이엔엠", "cj_enm", "tvN", "티빙"],
        "type": "large", "industry": "엔터/미디어", "logo": "CE",
        "careersUrl": "https://recruit.cj.net/",
        "benefits": [],
        "workStyle": {"remote": False, "flex": True, "unlimitedPTO": False, "overtime": "콘텐츠 제작 특성상 변동 큼"},
    },
    {
        "id": "cj_oliveyoung", "name": "CJ올리브영",
        "aliases": ["CJ올리브영", "올리브영", "cj_oliveyoung", "oliveyoung"],
        "type": "large", "industry": "유통/뷰티", "logo": "OY",
        "careersUrl": "https://recruit.cj.net/",
        "benefits": [],
        "workStyle": {"remote": False, "flex": False, "unlimitedPTO": False, "overtime": "일반적 대기업 수준"},
    },
]

# ━━ PROFILES ━━
PROFILES = [
    {"id": "explorer", "type": "탐험가형", "vec": {"compensation": -.3, "security": -.6, "growth": .9, "autonomy": .8, "impact": 0, "flexibility": .4},
     "desc": "돈과 안정성을 기꺼이 포기하더라도 배움과 자유를 택합니다.", "mapPri": "growth",
     "jobFit": {"tech": {"fit": "스타트업 초기 멤버, 프리랜서 개발자", "caution": "안정성을 경시하면 생애 주기 변화에서 급격한 스트레스를 받을 수 있습니다."}, "planning": {"fit": "신규 서비스 0→1 기획, 스타트업 첫 PM", "caution": "탐험을 위한 이직이 잦으면 런칭→성장까지의 결과물을 증명하기 어렵습니다."}, "marketing": {"fit": "그로스 마케팅 초기 셋업, 스타트업 마케팅 1호", "caution": "너무 자주 이동하면 캠페인 성과를 끝까지 증명하기 어렵습니다."}, "sales": {"fit": "신규 시장 개척 영업, 스타트업 첫 세일즈", "caution": "고객 관계는 시간이 걸립니다. 너무 빨리 떠나면 네트워크가 쌓이지 않습니다."}, "design": {"fit": "브랜딩 에이전시, 프리랜서 디자이너", "caution": "포트폴리오 다양성은 좋지만, 깊이 있는 프로젝트 하나가 더 강력합니다."}, "corporate": {"fit": "스타트업 경영지원 1호, 신규 법인 셋업", "caution": "경영지원은 신뢰와 안정이 핵심입니다. 잦은 이동은 신뢰를 쌓기 어렵게 만듭니다."}}},
    {"id": "architect", "type": "건축가형", "vec": {"compensation": 0, "security": -.1, "growth": .8, "autonomy": .2, "impact": .8, "flexibility": 0},
     "desc": "전문적 깊이와 조직적 영향력을 동시에 추구합니다.", "mapPri": "growth",
     "jobFit": {"tech": {"fit": "기술 리드, CTO, 플랫폼 아키텍트", "caution": "기술과 경영 두 축을 동시에 추구하면 중간에 빠질 위험이 있습니다."}, "planning": {"fit": "CPO, 프로덕트 전략가, 서비스 아키텍트", "caution": "기획 깊이와 조직 영향력 사이에서 시기별로 비중을 조절해야 합니다."}, "marketing": {"fit": "CMO, 브랜드 전략가, 마케팅 디렉터", "caution": "전략과 실행을 동시에 잡으려면 위임 능력이 핵심입니다."}, "sales": {"fit": "영업 디렉터, 전략 파트너십, 사업개발 리더", "caution": "영업 현장과 전략 사이에서 균형을 잃으면 둘 다 약해집니다."}, "design": {"fit": "CDO, 디자인 시스템 리드, UX 디렉터", "caution": "디자인 실무에서 멀어지면 팀의 신뢰를 잃을 수 있습니다."}, "corporate": {"fit": "CFO, CHRO, 경영전략 임원", "caution": "실무 감각을 잃으면 현장과 괴리된 의사결정을 하게 됩니다."}}},
    {"id": "fortress", "type": "요새형", "vec": {"compensation": .7, "security": .9, "growth": -.3, "autonomy": -.3, "impact": 0, "flexibility": -.5},
     "desc": "예측 가능한 보상과 안정성을 최우선으로 합니다.", "mapPri": "stability",
     "jobFit": {"tech": {"fit": "대기업 전문가 트랙, 공공기관 IT, 금융권 개발", "caution": "안정성에 과도하게 최적화하면 기술 트렌드 변화에 적응력이 약해집니다."}, "planning": {"fit": "대기업 서비스기획, 공공 SI 기획, 금융권 PM", "caution": "안정적 환경에서 혁신적 기획 역량이 정체될 수 있습니다."}, "marketing": {"fit": "대기업 브랜드 마케팅, 공기업 홍보", "caution": "안정적이지만 퍼포먼스 마케팅 역량이 약해질 수 있습니다."}, "sales": {"fit": "대기업 기존 고객 관리, 공공 입찰 영업", "caution": "신규 개척 역량이 약해지면 시장 변화에 취약해집니다."}, "design": {"fit": "대기업 인하우스, 공공기관 디자인", "caution": "외부 트렌드와 단절되면 디자인 감각이 정체됩니다."}, "corporate": {"fit": "대기업 재무/인사, 공기업 경영지원", "caution": "한 회사에 오래 있으면 외부 시장가치를 모르게 됩니다."}}},
    {"id": "conqueror", "type": "정복자형", "vec": {"compensation": .9, "security": -.2, "growth": .1, "autonomy": 0, "impact": .8, "flexibility": -.2},
     "desc": "높은 보상과 강한 영향력을 함께 추구합니다.", "mapPri": "salary",
     "jobFit": {"tech": {"fit": "빅테크 시니어, 핀테크 리드, 높은 RSU 제공 기업", "caution": "보상에 집중하면 기술적 깊이가 약해질 수 있습니다."}, "planning": {"fit": "빅테크 PM, 전략 컨설팅, VC/PE 투자심사역", "caution": "보상과 타이틀에 집착하면 실질적 기획 역량이 정체됩니다."}, "marketing": {"fit": "퍼포먼스 에이전시 임원, 빅테크 마케팅 리드", "caution": "매출 기여만 추구하면 브랜드 역량이 약해집니다."}, "sales": {"fit": "엔터프라이즈 세일즈, 투자 세일즈, 고연봉 영업직", "caution": "단기 실적 추구가 장기 고객 관계를 해칠 수 있습니다."}, "design": {"fit": "빅테크 디자인 리드, 에이전시 CD", "caution": "보상 중심 이동은 포트폴리오의 일관성을 해칩니다."}, "corporate": {"fit": "경영 컨설팅, 투자은행, CFO 트랙", "caution": "보상과 직급에만 집중하면 실무 역량이 약해집니다."}}},
    {"id": "nomad", "type": "유목민형", "vec": {"compensation": -.4, "security": -.5, "growth": .2, "autonomy": .8, "impact": -.3, "flexibility": .9},
     "desc": "어떤 것에도 묶이지 않는 것을 최고의 가치로 봅니다.", "mapPri": "wlb",
     "jobFit": {"tech": {"fit": "디지털 노마드 개발자, 프리랜서, 오픈소스 컨트리뷰터", "caution": "유연성 자체가 목적이 되면 깊이도 영향력도 쌓이지 않습니다."}, "planning": {"fit": "프리랜서 PM/기획 컨설턴트, 멀티 프로젝트", "caution": "프로덕트의 성장을 끝까지 보지 못하면 기획 역량이 제한됩니다."}, "marketing": {"fit": "프리랜서 마케터, 포트폴리오 커리어", "caution": "브랜드 마케팅은 시간이 걸립니다. 짧은 프로젝트만으론 한계가 있습니다."}, "sales": {"fit": "독립 에이전트, 프리랜서 세일즈 컨설턴트", "caution": "영업은 관계 비즈니스입니다. 유목 생활이 네트워크 구축을 방해할 수 있습니다."}, "design": {"fit": "프리랜서 디자이너, 디지털 노마드", "caution": "클라이언트 의존도가 높으면 진정한 자유가 아닙니다."}, "corporate": {"fit": "프리랜서 회계사, 독립 HR 컨설턴트", "caution": "경영지원은 조직 맥락을 깊이 아는 것이 핵심인데, 짧은 관여로는 어렵습니다."}}},
    {"id": "gardener", "type": "정원사형", "vec": {"compensation": .1, "security": .7, "growth": .7, "autonomy": -.1, "impact": 0, "flexibility": -.2},
     "desc": "안전한 환경 안에서 꾸준히 성장하는 것을 선호합니다.", "mapPri": "benefits",
     "jobFit": {"tech": {"fit": "대기업 R&D, 사내 기술 리더, 내부 이동 활용", "caution": "외부 시장 가치를 점검하지 않으면 사내에서만 통하는 전문가가 됩니다."}, "planning": {"fit": "대기업 기획실, 안정적 서비스의 지속적 개선", "caution": "새로운 시장/서비스 경험 없이는 기획 역량에 한계가 옵니다."}, "marketing": {"fit": "대기업 브랜드팀, 안정적 마케팅 조직", "caution": "같은 브랜드만 오래 하면 새 도전에 대한 감각이 둔해집니다."}, "sales": {"fit": "대기업 핵심 고객 관리, 장기 파트너십 영업", "caution": "신규 개척 없이 관리만 하면 영업 근육이 약해집니다."}, "design": {"fit": "대기업 디자인센터, 디자인 시스템 장기 운영", "caution": "같은 가이드라인 안에서만 작업하면 창의성이 정체됩니다."}, "corporate": {"fit": "대기업 재무/인사 전문가, 장기 근속", "caution": "한 회사에 최적화되면 이직 시 적응이 어렵습니다."}}},
    {"id": "sovereign", "type": "주권자형", "vec": {"compensation": .2, "security": -.3, "growth": .1, "autonomy": .9, "impact": .5, "flexibility": .3},
     "desc": "자기 방식대로 일하면서 의미 있는 결정을 내리고 싶어합니다.", "mapPri": "wlb",
     "jobFit": {"tech": {"fit": "창업, 소규모 팀 리더, 독립 컨설턴트", "caution": "모든 것을 직접 통제하려는 성향이 위임 실패와 번아웃으로 이어질 수 있습니다."}, "planning": {"fit": "1인 PM, 사내 벤처, 독립 프로덕트 컨설팅", "caution": "혼자 결정하는 습관이 팀 협업을 어렵게 만들 수 있습니다."}, "marketing": {"fit": "1인 마케팅 에이전시, 사내 벤처 마케팅 리드", "caution": "혼자서 다 하려다 전문성 깊이가 얕아질 수 있습니다."}, "sales": {"fit": "독립 세일즈 에이전트, 소규모 팀 영업 리더", "caution": "영업은 조직 지원이 중요합니다. 혼자 다 하면 스케일이 안 됩니다."}, "design": {"fit": "1인 디자인 스튜디오, 사내 벤처 디자인 리드", "caution": "클라이언트 관리와 디자인을 동시에 하면 둘 다 약해질 수 있습니다."}, "corporate": {"fit": "소규모 법인 CFO, 스타트업 COO", "caution": "경영지원을 혼자 맡으면 전문 분야의 깊이가 얕아집니다."}}},
    {"id": "strategist", "type": "전략가형", "vec": {"compensation": .5, "security": .2, "growth": .3, "autonomy": 0, "impact": .6, "flexibility": .5},
     "desc": "어떤 한 축에 올인하지 않고 최적의 포지션을 계산합니다.", "mapPri": "growth",
     "jobFit": {"tech": {"fit": "PM, 전략 기획, 매니지먼트 트랙", "caution": "균형 추구가 어느 것도 강하지 않은 상태로 이어질 수 있습니다."}, "planning": {"fit": "전략 기획, 사업개발, PM → 경영 트랙", "caution": "다방면에 관심이 분산되면 전문성이 약해집니다."}, "marketing": {"fit": "마케팅 전략가, 브랜드+퍼포먼스 양쪽 경험", "caution": "다 잘하려다 아무것도 깊지 않을 수 있습니다."}, "sales": {"fit": "전략 영업, 사업개발, 파트너십 매니저", "caution": "너무 전략적으로만 접근하면 현장 감각을 잃습니다."}, "design": {"fit": "UX 전략가, 디자인+기획 겸직", "caution": "디자인과 전략 사이에서 정체성이 모호해질 수 있습니다."}, "corporate": {"fit": "전략기획실, 경영진 보좌, MBA 트랙", "caution": "전략만 하고 실행을 안 하면 신뢰를 잃습니다."}}},
]

# ━━ JOB GROUPS ━━
JOB_GROUPS = [
    {"groupLabel": "기술", "color": "#4b8df8", "jobs": [
        {"id": "dev", "label": "개발", "icon": "💻", "scenario": "tech"},
        {"id": "devops", "label": "DevOps/인프라", "icon": "🛠️", "scenario": "tech"},
        {"id": "security", "label": "보안", "icon": "🔐", "scenario": "tech"},
        {"id": "data", "label": "데이터 분석", "icon": "📊", "scenario": "tech"},
        {"id": "ai", "label": "AI / ML", "icon": "🤖", "scenario": "tech"},
    ]},
    {"groupLabel": "디자인", "color": "#e85d9a", "jobs": [
        {"id": "uxui", "label": "UX/UI 디자인", "icon": "🎨", "scenario": "design"},
        {"id": "graphic", "label": "그래픽/영상", "icon": "🎬", "scenario": "design"},
    ]},
    {"groupLabel": "비즈니스", "color": "#f0a030", "jobs": [
        {"id": "pm", "label": "서비스기획/PM", "icon": "📋", "scenario": "planning"},
        {"id": "po", "label": "프로덕트 오너", "icon": "📦", "scenario": "planning"},
        {"id": "marketing", "label": "마케팅", "icon": "📢", "scenario": "marketing"},
        {"id": "content", "label": "콘텐츠/에디터", "icon": "✍️", "scenario": "marketing"},
        {"id": "sales", "label": "영업/세일즈", "icon": "🤝", "scenario": "sales"},
        {"id": "cs", "label": "고객성공(CS/CX)", "icon": "📞", "scenario": "sales"},
    ]},
    {"groupLabel": "경영", "color": "#34c77b", "jobs": [
        {"id": "finance", "label": "재무/회계", "icon": "💰", "scenario": "corporate"},
        {"id": "hr", "label": "인사(HR)", "icon": "👤", "scenario": "corporate"},
        {"id": "legal", "label": "총무/법무", "icon": "📑", "scenario": "corporate"},
    ]},
    {"groupLabel": "산업/연구", "color": "#8b6cf6", "jobs": [
        {"id": "manufacturing", "label": "생산/제조/품질", "icon": "🏭", "scenario": "corporate"},
        {"id": "logistics", "label": "물류/SCM", "icon": "🚛", "scenario": "corporate"},
        {"id": "md", "label": "MD/바잉", "icon": "🏪", "scenario": "sales"},
        {"id": "rnd", "label": "연구/R&D", "icon": "🔬", "scenario": "tech"},
    ]},
]

# ━━ PROFILER QUESTIONS ━━
Q_BASE = [
    {"id": 1, "label": "보상 vs 성장", "a": {"title": "연봉 40% 인상", "fx": {"compensation": .9, "security": .2, "growth": -.5, "autonomy": 0, "impact": -.1, "flexibility": -.1}}, "b": {"title": "연봉 동결", "fx": {"compensation": -.4, "security": -.2, "growth": .9, "autonomy": .3, "impact": .1, "flexibility": .2}}},
    {"id": 2, "label": "안정성 vs 자율성", "a": {"title": "대기업 정규직", "fx": {"compensation": .3, "security": .9, "growth": -.1, "autonomy": -.7, "impact": .1, "flexibility": -.3}}, "b": {"title": "계약직 1년 갱신", "fx": {"compensation": -.1, "security": -.7, "growth": .1, "autonomy": .9, "impact": -.1, "flexibility": .4}}},
    {"id": 3, "label": "영향력 vs 보상", "a": {"title": "연봉 30% 인상", "fx": {"compensation": .8, "security": .2, "growth": .1, "autonomy": -.1, "impact": -.6, "flexibility": 0}}, "b": {"title": "연봉 10% 삭감", "fx": {"compensation": -.5, "security": -.1, "growth": .3, "autonomy": .2, "impact": .9, "flexibility": 0}}},
    {"id": 4, "label": "유연성 vs 안정성", "a": {"title": "업계 1위 대기업", "fx": {"compensation": .3, "security": .9, "growth": -.2, "autonomy": -.2, "impact": .2, "flexibility": -.8}}, "b": {"title": "중견 회사", "fx": {"compensation": -.1, "security": -.5, "growth": .3, "autonomy": .1, "impact": -.1, "flexibility": .9}}},
    {"id": 5, "label": "성장 vs 자율성", "a": {"title": "업계 최고 전문가에게 직접 배움", "fx": {"compensation": 0, "security": .1, "growth": .9, "autonomy": -.7, "impact": 0, "flexibility": -.1}}, "b": {"title": "혼자 맡아서 자유롭게 진행", "fx": {"compensation": 0, "security": -.2, "growth": .2, "autonomy": .9, "impact": .2, "flexibility": .3}}},
    {"id": 6, "label": "보상 vs 유연성", "a": {"title": "연봉 50% 인상", "fx": {"compensation": 1, "security": .3, "growth": -.1, "autonomy": -.5, "impact": .1, "flexibility": -.9}}, "b": {"title": "연봉 동결", "fx": {"compensation": -.3, "security": -.1, "growth": .1, "autonomy": .4, "impact": 0, "flexibility": .9}}},
    {"id": 7, "label": "영향력 vs 성장", "a": {"title": "리더 포지션", "fx": {"compensation": .3, "security": .1, "growth": -.4, "autonomy": .1, "impact": .9, "flexibility": -.2}}, "b": {"title": "실무 전문가", "fx": {"compensation": -.1, "security": .1, "growth": .9, "autonomy": .2, "impact": -.4, "flexibility": .2}}},
    {"id": 8, "label": "안정성 vs 보상", "a": {"title": "공공기관급 안정성", "fx": {"compensation": -.5, "security": 1, "growth": -.3, "autonomy": -.2, "impact": -.1, "flexibility": -.3}}, "b": {"title": "초기 스타트업", "fx": {"compensation": .8, "security": -.9, "growth": .5, "autonomy": .2, "impact": .3, "flexibility": -.1}}},
    {"id": 9, "label": "자율성 vs 영향력", "a": {"title": "완전 자율 근무", "fx": {"compensation": 0, "security": 0, "growth": .1, "autonomy": .9, "impact": -.6, "flexibility": .3}}, "b": {"title": "출근 필수, 회의 빡빡", "fx": {"compensation": .1, "security": .2, "growth": .2, "autonomy": -.7, "impact": .9, "flexibility": -.2}}},
    {"id": 10, "label": "성장 vs 안정성", "a": {"title": "검증된 환경, 안정 운영", "fx": {"compensation": .2, "security": .9, "growth": -.6, "autonomy": -.1, "impact": 0, "flexibility": -.3}}, "b": {"title": "초기 스타트업", "fx": {"compensation": -.2, "security": -.8, "growth": .9, "autonomy": .3, "impact": .2, "flexibility": .1}}},
    {"id": 11, "label": "유연성 vs 영향력", "a": {"title": "업계 인정받는 포지션", "fx": {"compensation": .2, "security": .3, "growth": .1, "autonomy": -.1, "impact": .9, "flexibility": -.7}}, "b": {"title": "무명이지만 범용적 역할", "fx": {"compensation": -.1, "security": -.1, "growth": .3, "autonomy": .2, "impact": -.5, "flexibility": .9}}},
    {"id": 12, "label": "보상 vs 자율성", "a": {"title": "연봉 35% 인상", "fx": {"compensation": .85, "security": .2, "growth": 0, "autonomy": -.8, "impact": .1, "flexibility": -.3}}, "b": {"title": "현재 연봉 유지", "fx": {"compensation": -.2, "security": 0, "growth": .1, "autonomy": .9, "impact": -.1, "flexibility": .4}}},
]

# ━━ QUESTION SCENARIO DESCRIPTIONS ━━
Q_DESC = {
    "tech": [
        {"a": "기존과 동일한 기술 스택 유지", "b": "한 번도 다뤄보지 않은 기술 스택을 처음부터 구축"},
        {"a": "명확한 R&R, 매년 3~5% 인상. 출퇴근 고정, 재택 불가", "b": "완전 원격, 업무 시간 자율, 프로젝트 선택권"},
        {"a": "실무 개발자. 의사결정 참여 없음", "b": "5인 팀 리드. 기술 선택, 채용, 아키텍처 직접 결정"},
        {"a": "10년 안정적. 독자 플랫폼이라 이직 시 기술 전환 어려움", "b": "3년 후 존속 불확실. 시장 범용 기술로 어디든 이직 가능"},
        {"a": "그 사람의 방식을 따라야 하고, 자기 코드 스타일 불가", "b": "사내에 배울 시니어 없음. 독학으로 해결"},
        {"a": "3년 의무 근속. 중도 퇴사 시 위약금", "b": "아무 구속 없음. 6개월마다 커리어 방향 재조정 가능"},
        {"a": "CTO 타이틀. 경영진 회의, 컨퍼런스 발표. 70%가 매니지먼트", "b": "시니어 엔지니어. 최신 기술을 매일 다루고 깊이가 쌓임"},
        {"a": "구조조정 가능성 제로. 연봉은 업계 평균의 80%", "b": "2년 내 인수 또는 폐업 반반. 성공 시 스톡옵션으로 연봉 5배"},
        {"a": "재택, 자기 일정, 프로젝트 선택. 조직 의사결정에 영향력 없음", "b": "일정 자율 없음. 대신 팀 리드로서 조직 방향에 직접 영향"},
        {"a": "새로 배울 건 적지만 실수할 일도 없음. 5년 후 같은 자리 보장", "b": "3개월마다 기술 스택 변경. 성장은 폭발적이지만 회사가 망하면 처음부터"},
        {"a": "컨퍼런스 초청, 네임밸류 높음. 다른 방향 전환은 어려움", "b": "시장 인지도 없음. 경험이 3~4개 다른 직군으로 전환 가능"},
        {"a": "주 5일 출근, 야근 빈번, 휴가 사용 자유롭지 않음", "b": "주 4일 근무, 완전 원격, 업무 시간 자율 선택"},
    ],
    "planning": [
        {"a": "기존과 동일한 서비스 운영 업무", "b": "한 번도 해보지 않은 신규 서비스를 0→1로 기획"},
        {"a": "명확한 R&R, 매년 3~5% 인상. 출퇴근 고정, 재택 불가", "b": "완전 원격, 업무 시간 자율, 프로젝트 선택권"},
        {"a": "기획 실무만 담당. 전략 회의 참여 없음", "b": "프로덕트 리드. 로드맵, 우선순위, KPI 직접 결정"},
        {"a": "10년 안정적. 자체 프로세스라 이직 시 경험 전환 어려움", "b": "3년 후 존속 불확실. 범용적 기획 방법론으로 어디든 이직 가능"},
        {"a": "업계 최고 PO에게 직접 배움. 그 사람의 프레임워크만 사용", "b": "사내에 배울 사람 없음. 나만의 기획 프레임을 직접 구축"},
        {"a": "3년 의무 근속. 중도 퇴사 시 위약금", "b": "아무 구속 없음. 6개월마다 커리어 방향 재조정 가능"},
        {"a": "CPO 타이틀. 경영진 보고, 외부 발표. 70%가 매니지먼트", "b": "실무 기획자. 매일 사용자 리서치하고 PRD 직접 작성"},
        {"a": "구조조정 가능성 제로. 연봉은 업계 평균의 80%", "b": "2년 내 인수 또는 폐업 반반. 성공 시 스톡옵션으로 연봉 5배"},
        {"a": "재택, 자기 일정, 프로젝트 선택. 조직 의사결정에 영향력 없음", "b": "일정 자율 없음. 대신 팀 리드로서 프로덕트 방향에 직접 영향"},
        {"a": "안정적인 서비스 유지보수. 5년 후 같은 자리 보장", "b": "3개월마다 피봇. 성장은 폭발적이지만 회사가 망하면 처음부터"},
        {"a": "업계에서 인정받는 PM. 다른 분야 전환은 어려움", "b": "시장 인지도 없음. 경험이 마케팅·영업·전략 등으로 전환 가능"},
        {"a": "주 5일 출근, 야근 빈번, 휴가 사용 자유롭지 않음", "b": "주 4일 근무, 완전 원격, 업무 시간 자율 선택"},
    ],
    "marketing": [
        {"a": "기존과 동일한 캠페인 반복 운영", "b": "한 번도 해보지 않은 신규 채널/시장을 처음부터 개척"},
        {"a": "명확한 R&R, 매년 3~5% 인상. 출퇴근 고정, 재택 불가", "b": "완전 원격, 업무 시간 자율, 프로젝트 선택권"},
        {"a": "실행 담당자. 전략 회의 참여 없음", "b": "마케팅 팀 리드. 예산 배분, 채널 선택, KPI 직접 결정"},
        {"a": "10년 안정적. 자체 플랫폼 마케팅이라 범용 경험 부족", "b": "3년 후 존속 불확실. 다양한 채널 경험으로 어디든 이직 가능"},
        {"a": "업계 최고 CMO에게 직접 배움. 그 사람의 방식만 따라야 함", "b": "사내에 배울 사람 없음. 나만의 마케팅 전략을 직접 구축"},
        {"a": "3년 의무 근속. 중도 퇴사 시 위약금", "b": "아무 구속 없음. 6개월마다 커리어 방향 재조정 가능"},
        {"a": "CMO 타이틀. 경영진 보고, 외부 강연. 70%가 매니지먼트", "b": "퍼포먼스 마케터. 매일 데이터 보고 캠페인 최적화. 깊이가 쌓임"},
        {"a": "구조조정 가능성 제로. 연봉은 업계 평균의 80%", "b": "2년 내 인수 또는 폐업 반반. 성공 시 스톡옵션으로 연봉 5배"},
        {"a": "재택, 자기 일정, 프로젝트 선택. 조직 의사결정에 영향력 없음", "b": "일정 자율 없음. 대신 팀 리드로서 브랜드 방향에 직접 영향"},
        {"a": "안정적인 브랜드 유지. 5년 후 같은 자리 보장", "b": "매달 새 캠페인. 성장은 폭발적이지만 회사가 망하면 포트폴리오만 남음"},
        {"a": "업계에서 인정받는 마케터. 다른 분야 전환은 어려움", "b": "시장 인지도 없음. 경험이 기획·영업·콘텐츠로 전환 가능"},
        {"a": "주 5일 출근, 야근 빈번, 휴가 사용 자유롭지 않음", "b": "주 4일 근무, 완전 원격, 업무 시간 자율 선택"},
    ],
    "sales": [
        {"a": "기존 고객 관리 위주의 안정적 영업", "b": "신규 시장 개척. 고객 베이스를 처음부터 구축"},
        {"a": "명확한 R&R, 매년 3~5% 인상. 출퇴근 고정, 재택 불가", "b": "완전 자율, 성과만 내면 시간과 장소 자유"},
        {"a": "담당 고객만 관리. 영업 전략 참여 없음", "b": "영업팀 리드. 타겟 시장, 가격 정책, 파이프라인 직접 결정"},
        {"a": "10년 안정적. 특정 산업 영업이라 다른 업종 전환 어려움", "b": "3년 후 존속 불확실. 다양한 산업 경험으로 어디든 이직 가능"},
        {"a": "업계 최고 영업 리더에게 직접 배움. 그 사람의 방식만 따름", "b": "사내에 배울 사람 없음. 나만의 영업 프로세스를 직접 구축"},
        {"a": "3년 의무 근속. 중도 퇴사 시 위약금", "b": "아무 구속 없음. 6개월마다 커리어 방향 재조정 가능"},
        {"a": "영업본부장. 경영진 보고, 핵심 고객 미팅. 70%가 매니지먼트", "b": "탑세일즈. 매일 현장에서 딜 클로징. 실력이 직접 쌓임"},
        {"a": "구조조정 가능성 제로. 연봉은 업계 평균의 80%", "b": "2년 내 인수 또는 폐업 반반. 성공 시 인센티브로 연봉 5배"},
        {"a": "재택, 자기 일정, 고객 선택. 조직 의사결정에 영향력 없음", "b": "일정 자율 없음. 대신 팀 리드로서 영업 전략에 직접 영향"},
        {"a": "기존 거래처 유지. 5년 후 같은 자리 보장", "b": "매달 새 고객 발굴. 성장은 폭발적이지만 파이프라인이 끊기면 처음부터"},
        {"a": "업계에서 인정받는 영업 전문가. 다른 직군 전환은 어려움", "b": "시장 인지도 없음. 경험이 마케팅·사업개발·컨설팅으로 전환 가능"},
        {"a": "주 5일 출근, 야근 빈번, 휴가 사용 자유롭지 않음", "b": "주 4일 근무, 완전 원격, 업무 시간 자율 선택"},
    ],
    "design": [
        {"a": "기존과 동일한 디자인 시스템 유지 운영", "b": "한 번도 해보지 않은 브랜딩을 처음부터 구축"},
        {"a": "명확한 R&R, 매년 3~5% 인상. 출퇴근 고정, 재택 불가", "b": "완전 원격, 업무 시간 자율, 프로젝트 선택권"},
        {"a": "시안 제작만 담당. 방향성 결정 없음", "b": "디자인 리드. 브랜딩, UX 방향, 디자인 시스템 직접 결정"},
        {"a": "10년 안정적. 자체 디자인 가이드라 이직 시 포트폴리오 약함", "b": "3년 후 존속 불확실. 다양한 프로젝트로 포트폴리오 풍부"},
        {"a": "업계 최고 디자이너에게 직접 배움. 그 사람의 스타일만 따름", "b": "사내에 배울 사람 없음. 나만의 디자인 철학을 직접 구축"},
        {"a": "3년 의무 근속. 중도 퇴사 시 위약금", "b": "아무 구속 없음. 6개월마다 커리어 방향 재조정 가능"},
        {"a": "CDO 타이틀. 경영진 보고, 외부 강연. 70%가 매니지먼트", "b": "시니어 디자이너. 매일 직접 디자인하고 깊이가 쌓임"},
        {"a": "구조조정 가능성 제로. 연봉은 업계 평균의 80%", "b": "2년 내 인수 또는 폐업 반반. 성공 시 스톡옵션으로 연봉 5배"},
        {"a": "재택, 자기 일정, 프로젝트 선택. 조직 의사결정에 영향력 없음", "b": "일정 자율 없음. 대신 리드로서 제품 디자인 방향에 직접 영향"},
        {"a": "안정적인 유지보수 디자인. 5년 후 같은 자리 보장", "b": "매달 새 프로젝트. 성장은 폭발적이지만 회사가 망하면 포트폴리오만 남음"},
        {"a": "업계에서 인정받는 디자이너. 다른 분야 전환은 어려움", "b": "시장 인지도 없음. 경험이 기획·마케팅·프론트엔드로 전환 가능"},
        {"a": "주 5일 출근, 야근 빈번, 휴가 사용 자유롭지 않음", "b": "주 4일 근무, 완전 원격, 업무 시간 자율 선택"},
    ],
    "corporate": [
        {"a": "기존과 동일한 프로세스 운영", "b": "전사 시스템을 새로 설계. ERP 도입부터 직접 주도"},
        {"a": "명확한 R&R, 매년 3~5% 인상. 출퇴근 고정, 재택 불가", "b": "완전 원격, 업무 시간 자율, 프로젝트 선택권"},
        {"a": "실무 담당자. 경영 의사결정 참여 없음", "b": "팀 리드. 예산, 인력, 프로세스 직접 결정"},
        {"a": "10년 안정적. 특정 산업 경험이라 다른 업종 전환 어려움", "b": "3년 후 존속 불확실. 범용적 경험으로 어디든 이직 가능"},
        {"a": "업계 최고 임원에게 직접 배움. 그 사람의 방식만 따름", "b": "사내에 배울 사람 없음. 나만의 프로세스를 직접 구축"},
        {"a": "3년 의무 근속. 중도 퇴사 시 위약금", "b": "아무 구속 없음. 6개월마다 커리어 방향 재조정 가능"},
        {"a": "임원 타이틀. 이사회 보고, 전사 의사결정. 70%가 매니지먼트", "b": "실무 전문가. 매일 직접 분석하고 보고서 작성. 전문성이 쌓임"},
        {"a": "구조조정 가능성 제로. 연봉은 업계 평균의 80%", "b": "2년 내 인수 또는 폐업 반반. 성공 시 스톡옵션으로 연봉 5배"},
        {"a": "재택, 자기 일정, 프로젝트 선택. 조직 의사결정에 영향력 없음", "b": "일정 자율 없음. 대신 팀 리드로서 조직 운영에 직접 영향"},
        {"a": "안정적인 운영 업무. 5년 후 같은 자리 보장", "b": "매달 새 과제. 성장은 폭발적이지만 회사가 망하면 처음부터"},
        {"a": "업계에서 인정받는 전문가. 다른 분야 전환은 어려움", "b": "시장 인지도 없음. 경험이 컨설팅·기획·운영 등으로 전환 가능"},
        {"a": "주 5일 출근, 야근 빈번, 휴가 사용 자유롭지 않음", "b": "주 4일 근무, 완전 원격, 업무 시간 자율 선택"},
    ],
}


def seed():
    conn = pymysql.connect(
        host=config.DB_HOST, port=config.DB_PORT,
        user=config.DB_USER, password=config.DB_PASS,
        db=config.DB_NAME, charset="utf8mb4",
        autocommit=True,
        auth_plugin_map={'mysql_native_password': None},
    )
    cur = conn.cursor()

    # 1. Company types — INSERT then build code→ID map
    for t in COMPANY_TYPES:
        cur.execute(
            "INSERT IGNORE INTO TCOMPANY_TYPE (COMP_TP_CD, COMP_TP_NM, GROWTH_RATE_VAL, GROWTH_LABEL_NM, STABILITY_SCORE_NO) VALUES (%s,%s,%s,%s,%s)",
            t,
        )
    cur.execute("SELECT COMP_TP_ID, COMP_TP_CD FROM TCOMPANY_TYPE")
    TP_MAP = {row[1]: row[0] for row in cur.fetchall()}
    print(f"  TCOMPANY_TYPE: {len(COMPANY_TYPES)}")

    # 2. Benefit presets
    count = 0
    for type_cd, items in BEN_PRESETS.items():
        comp_tp_id = TP_MAP.get(type_cd)
        if not comp_tp_id:
            continue
        for i, b in enumerate(items):
            cur.execute(
                "INSERT INTO TBENEFIT_PRESET (COMP_TP_ID, BENEFIT_CD, BENEFIT_NM, BENEFIT_AMT, BENEFIT_CTGR_CD, BADGE_CD, DEFAULT_CHECKED_YN, SORT_ORDER_NO) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (comp_tp_id, b["key"], b["name"], b["val"], b["cat"], b["badge"], b["checked"], i),
            )
            count += 1
    print(f"  TBENEFIT_PRESET: {count}")

    # 3. Companies — INSERT with COMP_ENG_NM (former string id) + grab lastrowid for FK
    for c in COMPANIES:
        cur.execute(
            "INSERT IGNORE INTO TCOMPANY (COMP_ENG_NM, COMP_NM, COMP_TP_ID, INDUSTRY_NM, LOGO_NM, WORK_STYLE_VAL, CAREERS_BENEFIT_URL) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (
                c["id"],
                c["name"],
                TP_MAP.get(c["type"]),
                c.get("industry"),
                c.get("logo"),
                json.dumps(c.get("workStyle"), ensure_ascii=False) if c.get("workStyle") else None,
                c.get("careersUrl"),
            ),
        )
        # Resolve COMP_ID (handle INSERT IGNORE case where row already exists)
        cur.execute("SELECT COMP_ID FROM TCOMPANY WHERE COMP_ENG_NM=%s", (c["id"],))
        row = cur.fetchone()
        if not row:
            continue
        comp_id = row[0]
        for alias in c.get("aliases", []):
            cur.execute(
                "INSERT IGNORE INTO TCOMPANY_ALIAS (COMP_ID, ALIAS_NM) VALUES (%s,%s)",
                (comp_id, alias),
            )
        for i, b in enumerate(c.get("benefits", [])):
            cur.execute(
                "INSERT IGNORE INTO TCOMPANY_BENEFIT (COMP_ID, BENEFIT_CD, BENEFIT_NM, BENEFIT_AMT, BENEFIT_CTGR_CD, BADGE_CD, NOTE_CTNT, QUAL_YN, QUAL_DESC_CTNT, SORT_ORDER_NO) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    comp_id,
                    b["key"],
                    b["name"],
                    b["val"],
                    b["cat"],
                    b["badge"],
                    b.get("note"),
                    b.get("qual", False),
                    b.get("qualText"),
                    i,
                ),
            )
    print(f"  TCOMPANY: {len(COMPANIES)}")

    # 4. Profiles
    for p in PROFILES:
        cur.execute(
            "INSERT IGNORE INTO TPROFILE (PROFILE_CD, PROFILE_NM, PROFILE_DESC_CTNT, MAP_PRIORITY_CD, VEC_VAL) VALUES (%s,%s,%s,%s,%s)",
            (p["id"], p["type"], p["desc"], p["mapPri"], json.dumps(p["vec"])),
        )
    cur.execute("SELECT PROFILE_ID, PROFILE_CD FROM TPROFILE")
    PROFILE_MAP = {row[1]: row[0] for row in cur.fetchall()}
    for p in PROFILES:
        profile_id = PROFILE_MAP.get(p["id"])
        if not profile_id:
            continue
        for scenario, fit in p["jobFit"].items():
            cur.execute(
                "INSERT IGNORE INTO TPROFILE_JOB_FIT (PROFILE_ID, SCENARIO_CD, FIT_CTNT, CAUTION_CTNT) VALUES (%s,%s,%s,%s)",
                (profile_id, scenario, fit["fit"], fit["caution"]),
            )
    print(f"  TPROFILE: {len(PROFILES)}")

    # 5. Job groups & jobs
    job_count = 0
    for i, g in enumerate(JOB_GROUPS):
        cur.execute(
            "INSERT INTO TJOB_GROUP (JOB_GROUP_NM, COLOR_CD, SORT_ORDER_NO) VALUES (%s,%s,%s)",
            (g["groupLabel"], g["color"], i),
        )
        gid = cur.lastrowid
        for j, job in enumerate(g["jobs"]):
            cur.execute(
                "INSERT IGNORE INTO TJOB (JOB_CD, JOB_GROUP_ID, JOB_NM, ICON_NM, SCENARIO_CD, SORT_ORDER_NO) VALUES (%s,%s,%s,%s,%s,%s)",
                (job["id"], gid, job["label"], job["icon"], job["scenario"], j),
            )
            job_count += 1
    print(f"  TJOB_GROUP: {len(JOB_GROUPS)}, TJOB: {job_count}")

    # 6. Profiler questions — QUESTION_NO preserves original 1..N
    for q in Q_BASE:
        cur.execute(
            "INSERT IGNORE INTO TPROFILER_QUESTION (QUESTION_NO, QUESTION_LABEL_NM, OPTION_A_TITLE_NM, OPTION_A_FX_VAL, OPTION_B_TITLE_NM, OPTION_B_FX_VAL) VALUES (%s,%s,%s,%s,%s,%s)",
            (q["id"], q["label"], q["a"]["title"], json.dumps(q["a"]["fx"]), q["b"]["title"], json.dumps(q["b"]["fx"])),
        )
    cur.execute("SELECT QUESTION_ID, QUESTION_NO FROM TPROFILER_QUESTION")
    Q_MAP = {row[1]: row[0] for row in cur.fetchall()}
    print(f"  TPROFILER_QUESTION: {len(Q_BASE)}")

    # 7. Question scenario descriptions
    desc_count = 0
    for scenario, descs in Q_DESC.items():
        for i, d in enumerate(descs):
            q_no = Q_BASE[i]["id"]
            q_id = Q_MAP.get(q_no)
            if not q_id:
                continue
            cur.execute(
                "INSERT IGNORE INTO TQUESTION_SCENARIO (QUESTION_ID, SCENARIO_CD, DESC_A_CTNT, DESC_B_CTNT) VALUES (%s,%s,%s,%s)",
                (q_id, scenario, d["a"], d["b"]),
            )
            desc_count += 1
    print(f"  TQUESTION_SCENARIO: {desc_count}")

    # 8. Popular cases (landing page)
    POPULAR_CASES = [
        ('company','쿠팡','large','대기업','네이버','large','대기업',
         json.dumps(['<strong>연봉</strong>은 쿠팡이 높지만 포괄임금 + 야근 많음으로 시간당 가치는 역전될 수 있음','<strong>워라밸</strong>은 네이버가 우세 · 재택·유연근무 실사용률 높음','<strong>3년 성장</strong>은 비슷한 수준 — 직무에 따라 갈림'],ensure_ascii=False),
         12341,847),
        ('company','카카오','large','대기업','삼성전자','large','대기업',
         json.dumps(['<strong>IT 플랫폼</strong> vs 제조 대기업 — 문화 차이 큼','<strong>자율 문화</strong> vs 체계적 구조 · 성향에 따라 선택','<strong>복지</strong> 패키지는 삼성이 종합적으로 우세'],ensure_ascii=False),
         9823,623),
        ('company','토스','startup','핀테크','카카오뱅크','large','인터넷은행',
         json.dumps(['<strong>성장성</strong>은 토스가 빠르지만 리스크도 큼','<strong>안정성</strong>은 카카오뱅크(은행 라이선스)가 우세','<strong>보상 구조</strong> 스톡옵션 vs 안정 연봉 차이'],ensure_ascii=False),
         5432,298),
        ('company','라인','large','글로벌 IT','카카오','large','대기업',
         json.dumps(['<strong>글로벌</strong> 경험은 라인이 압도적 · 일본 시장 기반','<strong>국내 영향력</strong>은 카카오가 우세 · 플랫폼 생태계','<strong>처우</strong>는 비슷한 수준 — 직급별로 차이'],ensure_ascii=False),
         4821,245),
        ('company','삼성전자','large','대기업','SK하이닉스','large','대기업',
         json.dumps(['<strong>반도체</strong> 양대 산맥 — 직무 전문성은 비슷','<strong>연봉</strong>은 SK하이닉스가 근소 우위 · 성과급 변동 큼','<strong>워라밸</strong>은 사업부에 따라 크게 달라짐'],ensure_ascii=False),
         4512,231),
        ('company','배달의민족','large','플랫폼','당근','startup','플랫폼',
         json.dumps(['<strong>조직 문화</strong> 모두 수평적 · 배민이 더 체계적','<strong>성장 가능성</strong>은 당근이 높지만 수익화 과제','<strong>복지</strong>는 배민(우아한형제들)이 종합 우세'],ensure_ascii=False),
         3987,198),
        ('company','현대자동차','large','대기업','LG에너지솔루션','large','대기업',
         json.dumps(['<strong>미래 모빌리티</strong> vs 배터리 — 둘 다 성장 산업','<strong>연봉</strong>은 LG엔솔이 근소 우위 · 신설법인 프리미엄','<strong>안정성</strong>은 현대차가 우세 · 매출 규모 차이'],ensure_ascii=False),
         3654,187),
        ('company','네이버','large','대기업','구글코리아','foreign','외국계',
         json.dumps(['<strong>연봉</strong>은 구글이 압도적 · RSU 포함 시 2배 이상 차이','<strong>커리어 성장</strong>은 네이버가 국내 리더십 기회 많음','<strong>워라밸</strong>은 구글이 우세 · 유연근무 정착'],ensure_ascii=False),
         3421,176),
        ('company','카카오','large','대기업','토스','startup','핀테크',
         json.dumps(['<strong>안정성</strong>은 카카오가 우세 · 플랫폼 수익 안정적','<strong>성장 속도</strong>는 토스가 빠름 · 금융 슈퍼앱 도전','<strong>스톡옵션</strong> 토스가 매력적이나 리스크도 큼'],ensure_ascii=False),
         3198,165),
        ('company','쿠팡','large','대기업','마켓컬리','startup','이커머스',
         json.dumps(['<strong>규모</strong>는 쿠팡이 압도적 · 나스닥 상장사','<strong>성장성</strong>은 컬리가 프리미엄 시장 차별화','<strong>업무 강도</strong>는 쿠팡이 높음 · 포괄임금 주의'],ensure_ascii=False),
         2876,142),
    ]
    pop_count = 0
    for pc in POPULAR_CASES:
        cur.execute(
            """INSERT IGNORE INTO TPOPULAR_CASE
               (CASE_TYPE_CD, TITLE_A_NM, TYPE_A_CD, SUB_A_NM, TITLE_B_NM, TYPE_B_CD, SUB_B_NM,
                POINTS_VAL, VIEW_NO, COMPARISON_NO)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            pc,
        )
        pop_count += 1
    print(f"  TPOPULAR_CASE: {pop_count}")

    cur.close()
    conn.close()
    print("\nSeed complete!")

if __name__ == "__main__":
    seed()
