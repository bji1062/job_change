#!/usr/bin/env python3
"""
회사 복리후생 스크래핑 → SQL 파일 생성 도구

Setup (별도 venv):
  cd server/tools
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  playwright install chromium
  deactivate

Usage:
  server/tools/.venv/bin/python server/tools/scrape_benefits.py "삼성전자" --url "https://www.samsung-dxrecruit.com/benefit"
  server/tools/.venv/bin/python server/tools/scrape_benefits.py "네이버" --url "https://recruit.navercorp.com/..." --id naver
  server/tools/.venv/bin/python server/tools/scrape_benefits.py "현대자동차" --url "https://talent.hyundai.com/culture/benefit.hc" --type large --industry "자동차"
"""
import argparse
import asyncio
import re
import sys
from datetime import date
from pathlib import Path

# ━━ 회사명 → company_id 매핑 ━━
# 기존 수동 매핑 + KOSPI/KOSDAQ 상위 200개 회사 (seed 데이터 기반)
KNOWN_IDS = {
    # ── 기존 매핑 (seed.py 원본) ──
    "토스": "toss",
    "CJ그룹": "cj", "CJ": "cj",
    "쿠팡": "coupang",
    "배달의민족": "baemin", "우아한형제들": "baemin",
    "라인": "line", "LINE": "line",
    "당근": "daangn", "당근마켓": "daangn",
    "넥슨": "nexon",
    "엔씨소프트": "ncsoft",
    # ── KOSPI 1~50 (companies_kospi_1.py) ──
    "삼성전자": "samsung_elec", "Samsung": "samsung_elec", "삼성": "samsung_elec",
    "SK하이닉스": "sk_hynix", "하이닉스": "sk_hynix",
    "LG에너지솔루션": "lg_energy", "LGES": "lg_energy",
    "삼성바이오로직스": "samsung_bio", "삼성바이오": "samsung_bio",
    "현대자동차": "hyundai_motor", "현대차": "hyundai_motor", "현차": "hyundai_motor",
    "HD현대중공업": "hd_heavy", "현대중공업": "hd_heavy",
    "SK스퀘어": "sk_square",
    "한화에어로스페이스": "hanwha_aero", "한화에어로": "hanwha_aero",
    "두산에너빌리티": "doosan_enb", "두산에너": "doosan_enb",
    "KB금융": "kb_financial", "KB": "kb_financial", "국민은행": "kb_financial",
    "기아": "kia", "기아차": "kia", "KIA": "kia",
    "셀트리온": "celltrion", "Celltrion": "celltrion",
    "삼성물산": "samsung_cnt",
    "NAVER": "naver", "네이버": "naver", "naver": "naver",
    "신한지주": "shinhan", "신한은행": "shinhan", "신한금융": "shinhan",
    "한화오션": "hanwha_ocean", "대우조선": "hanwha_ocean",
    "현대모비스": "hyundai_mobis", "모비스": "hyundai_mobis",
    "삼성생명": "samsung_life",
    "한국전력": "kepco", "한전": "kepco", "KEPCO": "kepco",
    "HD한국조선해양": "hd_ksoe", "한국조선해양": "hd_ksoe", "KSOE": "hd_ksoe",
    "HD현대일렉트릭": "hd_electric", "현대일렉트릭": "hd_electric",
    "카카오": "kakao", "Kakao": "kakao",
    "하나금융지주": "hana_financial", "하나금융": "hana_financial", "하나은행": "hana_financial",
    "POSCO홀딩스": "posco_holdings", "포스코": "posco_holdings", "POSCO": "posco_holdings",
    "고려아연": "korea_zinc",
    "알테오젠": "alteogen", "Alteogen": "alteogen",
    "LG화학": "lg_chem",
    "삼성화재": "samsung_fire",
    "삼성SDI": "samsung_sdi",
    "삼성중공업": "samsung_heavy",
    "우리금융지주": "woori_financial", "우리금융": "woori_financial", "우리은행": "woori_financial",
    "현대로템": "hyundai_rotem",
    "메리츠금융지주": "meritz_financial", "메리츠금융": "meritz_financial", "메리츠": "meritz_financial",
    "HMM": "hmm", "현대상선": "hmm",
    "삼성전기": "samsung_electro",
    "SK": "sk_holdings", "에스케이": "sk_holdings",
    "SK이노베이션": "sk_innovation", "SK이노": "sk_innovation",
    "KT&G": "ktng", "케이티앤지": "ktng",
    "IBK기업은행": "ibk", "기업은행": "ibk", "IBK": "ibk",
    "포스코퓨처엠": "posco_future", "포스코케미칼": "posco_future",
    "효성중공업": "hyosung_heavy",
    "LG전자": "lg_elec", "엘지전자": "lg_elec",
    "HD현대": "hd_hyundai",
    "에코프로비엠": "ecoprobm",
    "하이브": "hybe", "HYBE": "hybe", "빅히트": "hybe",
    "LS ELECTRIC": "ls_electric", "LS일렉트릭": "ls_electric", "LS산전": "ls_electric",
    "현대글로비스": "hyundai_glovis", "글로비스": "hyundai_glovis",
    "삼성SDS": "samsung_sds",
    "KT": "kt", "케이티": "kt",
    "미래에셋증권": "mirae_asset", "미래에셋": "mirae_asset",
    # ── KOSPI 51~100 (companies_kospi_2.py) ──
    "두산": "doosan",
    "LG": "lg_corp", "엘지": "lg_corp",
    "에코프로": "ecopro",
    "한미반도체": "hanmi_semi",
    "크래프톤": "krafton", "KRAFTON": "krafton",
    "SK텔레콤": "skt", "SKT": "skt",
    "한국항공우주산업": "kai", "KAI": "kai",
    "에이비엘바이오": "abl_bio",
    "카카오뱅크": "kakao_bank",
    "한화시스템": "hanwha_systems",
    "SK바이오팜": "sk_biopharm",
    "S-Oil": "s_oil", "에쓰오일": "s_oil", "에스오일": "s_oil",
    "DB손해보험": "db_insurance", "DB손보": "db_insurance",
    "삼양식품": "samyang_food", "삼양라면": "samyang_food",
    "LIG넥스원": "lig_nex1",
    "레인보우로보틱스": "rainbow_robotics",
    "현대오토에버": "hyundai_autoever",
    "코오롱티슈진": "kolon_tissuegene",
    "유한양행": "yuhan",
    "이수페타시스": "isu_petasys",
    "포스코인터내셔널": "posco_intl",
    "HD현대마린솔루션": "hd_marine", "HD현대마린": "hd_marine",
    "에이피알": "apr", "APR": "apr", "메디큐브": "apr",
    "대한항공": "korean_air",
    "한진칼": "hanjin_kal",
    "현대건설": "hyundai_enc",
    "키움증권": "kiwoom",
    "NH투자증권": "nh_invest",
    "한국타이어앤테크놀로지": "hankook_tire", "한국타이어": "hankook_tire",
    "아모레퍼시픽": "amorepacific", "아모레": "amorepacific",
    "삼성증권": "samsung_securities",
    "HLB": "hlb",
    "카카오페이": "kakao_pay",
    "삼성카드": "samsung_card",
    "LG이노텍": "lg_innotek",
    "리가켐바이오": "ligachem",
    "LS": "ls_corp", "엘에스": "ls_corp",
    "LG유플러스": "lg_uplus", "LG U+": "lg_uplus",
    "코웨이": "coway",
    "한화": "hanwha_corp",
    "LG씨엔에스": "lg_cns", "LG CNS": "lg_cns",
    "펩트론": "peptron",
    "LG디스플레이": "lg_display", "LGD": "lg_display",
    "한미약품": "hanmi_pharm",
    "두산밥캣": "doosan_bobcat",
    "삼천당제약": "samchundang", "삼천당": "samchundang",
    "한국금융지주": "korea_financial", "한국투자증권": "korea_financial",
    "삼성에피스홀딩스": "samsung_epis", "삼성에피스": "samsung_epis",
    "현대제철": "hyundai_steel",
    "롯데케미칼": "lotte_chem",
    # ── KOSDAQ 1~50 (companies_kosdaq_1.py) ──
    "케어젠": "caregen",
    "리노공업": "leeno", "LEENO": "leeno",
    "디앤디파마텍": "dnd_pharma",
    "보로노이": "voronoi",
    "파마리서치": "pharma_research",
    "원익IPS": "wonik_ips",
    "클래시스": "classys",
    "메지온": "mezzion",
    "이오테크닉스": "eo_technics",
    "로보티즈": "robotis", "ROBOTIS": "robotis",
    "HPSP": "hpsp",
    "ISC": "isc",
    "오스코텍": "oscotec",
    "한솔케미칼": "hansol_chem",
    "올릭스": "olix",
    "엘앤씨바이오": "lnc_bio",
    "테크윙": "techwing",
    "휴젤": "hugel",
    "솔브레인": "soulbrain",
    "유진테크": "eugene_tech",
    "파크시스템스": "park_systems",
    "덕산네오룩스": "duksan_neolux",
    "에이디테크놀로지": "ad_tech",
    "티씨케이": "tck",
    "피에스케이": "psk",
    "주성엔지니어링": "jusung_eng",
    "셀트리온제약": "celltrion_pharm",
    "심텍": "simmtech",
    "HLB생명과학": "hlb_life",
    "동국제약": "dongkuk_pharm",
    "네패스": "nepes",
    "씨젠": "seegene",
    "성일하이텍": "sungeel",
    "SM엔터테인먼트": "sm_ent", "SM": "sm_ent",
    "인터로조": "interojo",
    "CJ ENM": "cj_enm_kd", "CJ이엔엠": "cj_enm_kd",
    "비에이치": "bh_co", "BH": "bh_co",
    "JYP엔터테인먼트": "jyp_ent", "JYP": "jyp_ent", "JYP엔터": "jyp_ent",
    "실리콘투": "silicon2",
    # ── KOSDAQ 51~100 (companies_kosdaq_2.py) ──
    "위메이드": "wemade",
    "카카오게임즈": "kakao_games",
    "HLB테라퓨틱스": "hlb_thera",
    "HLB이노베이션": "hlb_inno",
    "컴투스": "com2us",
    "펄어비스": "pearl_abyss",
    "솔브레인홀딩스": "soulbrain_hd",
    "나노엔텍": "nano_entek",
    "다우데이타": "daou_data",
    "HLB제약": "hlb_pharma",
    "엠씨넥스": "mcnex",
    "서울반도체": "seoul_semi",
    "코미팜": "komipharm",
    "더블유게임즈": "doubleugames",
    "에스티큐브": "st_cube",
    "네오위즈": "neowiz",
    "피에스케이홀딩스": "psk_holdings",
    "제이엘케이": "jlk",
    "나노신소재": "nano_material",
    "엠투아이": "m2i",
    "티에스이": "tse",
    "원익QnC": "wonik_qnc",
    "케이엠더블유": "kmw",
    "에코프로에이치엔": "ecopro_hn",
    "셀리드": "cellid",
    "와이바이오로직스": "y_biologics",
    "루닛": "lunit",
    "엔켐": "enchem",
    "제넥신": "genexine",
    "에임드바이오": "aimed_bio",
    "GC녹십자셀": "gc_cell",
    "엘오티베큠": "lot_vacuum",
    "동화기업": "dongwha",
    "아이패밀리에스씨": "ifamily",
    "켐트로스": "chemtros",
    "선익시스템": "sunic_system",
    "앱클론": "abclon",
    "지놈앤컴퍼니": "genome_company",
    "에스에프에이": "sfa",
    "아이센스": "i_sens",
    "텔레칩스": "telechips",
    "바이넥스": "binex",
    "켐트로닉스": "chemtronics",
    "매커스": "makersi",
    "리메드": "remed",
    "유비쿼스홀딩스": "ubiquoss", "유비쿼스": "ubiquoss",
    "원방테크": "wonbang_tech",
    "코오롱인더스트리 FnC": "kolon_fnc", "코오롱FnC": "kolon_fnc",
    "현대무벡스": "hyundai_muvex",
    "노바텍": "novatech",
}

# ━━ 복지 키워드 → (ben_key, category) 매핑 ━━
# 카테고리: financial, work_env, wellness, time, growth, family, life
BENEFIT_KEYWORDS = [
    # ━━ financial (보상·금전) ━━
    (r"복지\s*포인트|복리\s*포인트|선택.{0,2}복[리지]|카페테리아\s*포인트|업무\s*지원비|통신비", "welfare_point", "financial"),
    (r"경조사|경조금|명절", "event", "financial"),
    (r"성과급|인센티브|보너스", "bonus", "financial"),
    (r"자사주|RSU|스톡옵션|주식\s*매입|주식\s*보상", "stock", "financial"),
    (r"할인.*구매|임직원.*할인|사내.*매장|자사.*제품|서비스\s*이용권", "discount", "financial"),
    (r"주택.*대출|주택자금|사내\s*대출|전세.*대출|대출.*이자|대출.*지원", "housing_loan", "financial"),
    (r"기숙사|사택|숙소", "dormitory", "financial"),
    # ━━ work_env (근무환경) ━━
    (r"식대|식당|식사|중식|조식|석식|세\s*끼|카페|캔틴", "meal", "work_env"),
    (r"교통비|주차|통근|셔틀", "transport", "work_env"),
    (r"업무\s*기기|노트북|모니터|장비.*지원|가구|허먼밀러|스탠딩\s*데스크", "work_tools", "work_env"),
    # ━━ wellness (건강·의료) ━━
    (r"건강\s*검진|종합\s*검진|심리\s*검진", "health_check", "wellness"),
    (r"의료비|의료.*보험|실손|진단비|의료.*상담", "medical", "wellness"),
    (r"단체\s*보험|생명\s*보험|상해\s*보험", "insurance", "wellness"),
    (r"심리\s*상담|EAP|마음\s*건강|심리\s*센터", "mental", "wellness"),
    (r"피트니스|헬스장|체력단련|수영장|트레이너", "fitness", "wellness"),
    (r"부속의원|사내\s*병원|치과|한의원|약국|물리\s*치료|재활|근골격|이비인후|비뇨", "clinic", "wellness"),
    # ━━ time (시간·휴가) ━━
    (r"리프레시|안식.*휴가|장기.*휴가|워케이션|휴가비|휴가.*지원금", "refresh_leave", "time"),
    (r"유연.*근무|재택|원격|플렉스|자율\s*출퇴근|자율\s*근무|해외\s*근무", "flex_work", "time"),
    (r"연차|휴직|단축\s*근무", "leave_general", "time"),
    # ━━ growth (성장·커리어) ━━
    (r"어학|외국어|영어", "lang", "growth"),
    (r"사내\s*교육|직무\s*교육|교육\s*지원|외부\s*교육|컨퍼런스|학회|세미나|멘토링|온보딩", "edu_support", "growth"),
    (r"사내\s*공모|OCC|근속.*기념|시상|Awards?|추천.*리워드|스카우트", "career", "growth"),
    # ━━ family (가족) ━━
    (r"학자금|자녀.*교육", "child_edu", "family"),
    (r"출산|육아|임신|보육|어린이집|난임|가족\s*돌봄", "parenting", "family"),
    (r"결혼|웨딩|예식", "wedding", "family"),
    # ━━ life (라이프스타일) ━━
    (r"동호회|동아리|사내.*클럽|커뮤니티|활동비", "club", "life"),
    (r"도서|북카페|라이브러리", "library", "life"),
    (r"여행|휴양|리조트|콘도|워터파크|테마파크|숙박.*지원", "resort", "life"),
]

# ━━ 출력 경로 ━━
BENEFIT_DIR = Path(__file__).resolve().parent.parent / "seed" / "benefit"


def resolve_company_id(name: str, cli_id: str | None) -> str:
    if cli_id:
        return cli_id
    if name in KNOWN_IDS:
        return KNOWN_IDS[name]
    print(f"[ERROR] '{name}'의 company_id를 알 수 없습니다.")
    print(f"        KNOWN_IDS에 등록하거나 --id 옵션으로 지정해주세요.")
    sys.exit(1)


async def create_browser():
    from playwright.async_api import async_playwright
    from urllib.parse import urlparse
    import os

    pw = await async_playwright().start()
    # 기존 설치된 Chromium 바이너리 탐색
    chromium_path = None
    for p in Path("/root/.cache/ms-playwright").glob("chromium-*/chrome-linux/chrome"):
        chromium_path = str(p)
        break

    # 프록시 설정 (환경 변수에서 자동 감지)
    proxy_config = None
    proxy_url = os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY")
    if proxy_url:
        parsed = urlparse(proxy_url)
        proxy_config = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
        if parsed.username:
            proxy_config["username"] = parsed.username
        if parsed.password:
            proxy_config["password"] = parsed.password
        print(f"[INFO] 프록시 사용: {parsed.hostname}:{parsed.port}")

    launch_args = {
        "headless": True,
        "executable_path": chromium_path,
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ],
    }
    if proxy_config:
        launch_args["proxy"] = proxy_config

    browser = await pw.chromium.launch(**launch_args)
    context = await browser.new_context(
        ignore_https_errors=True,
        viewport={"width": 1920, "height": 1080},
        locale="ko-KR",
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
    )
    await context.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
    )
    return pw, browser, context


async def scrape_page(context, url: str, timeout: int = 30000, screenshot_path: str | None = None):
    page = await context.new_page()
    try:
        print(f"[INFO] 페이지 접속 중: {url}")
        resp = await page.goto(url, wait_until="networkidle", timeout=timeout)
        status = resp.status if resp else "unknown"
        print(f"[INFO] HTTP 상태: {status}")

        # 추가 대기 (JS 렌더링)
        await page.wait_for_timeout(2000)

        # 점진적 스크롤 (lazy-load 대응)
        for i in range(5):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await page.wait_for_timeout(500)

        # 최상단으로 복귀
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(500)

        title = await page.title()
        text = await page.evaluate("document.body.innerText")

        if screenshot_path:
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"[INFO] 스크린샷 저장: {screenshot_path}")

        return {"title": title, "text": text, "status": status}
    finally:
        await page.close()


_NAV_RE = re.compile(
    r"^(회사소개|사업부소개|직무소개|직무인터뷰|DX스토리|"
    r"Copyright|©|\+82|e\.recruit|개인정보|이용약관|채용문의)"
)


def segment_blocks(raw_text: str) -> list[dict]:
    """텍스트를 {title, lines[]} 블록으로 구조화"""
    blocks = []
    current = None

    for line in raw_text.split("\n"):
        line = line.strip()
        if not line or len(line) < 2 or _NAV_RE.match(line):
            continue

        is_title = len(line) <= 30 and not line.endswith(('.', '다', '요'))

        if is_title:
            current = {"title": line, "lines": []}
            blocks.append(current)
        elif current:
            current["lines"].append(line)
        else:
            current = {"title": line, "lines": []}
            blocks.append(current)

    return blocks


def split_compound_line(line: str) -> list[str]:
    """'부속의원, 치과, 한의원, 약국' → ['부속의원', '치과', '한의원', '약국']"""
    parts = re.split(r'[,·⋅、]', line)
    return [p.strip() for p in parts if len(p.strip()) >= 2]


def parse_benefits(raw_text: str, company_id: str) -> list[dict]:
    """블록 기반 키워드 매칭으로 복리후생 항목 추출"""
    blocks = segment_blocks(raw_text)
    found = []
    seen_keys: set[str] = set()

    for block in blocks:
        full_text = block["title"] + " " + " ".join(block["lines"])

        # 1) 블록 전체에 대해 키워드 매칭
        matched_in_block: list[tuple[str, str, str]] = []
        for pattern, ben_key, category in BENEFIT_KEYWORDS:
            if ben_key in seen_keys:
                continue
            if re.search(pattern, full_text, re.IGNORECASE):
                matched_in_block.append((ben_key, category, pattern))

        # 2) 복합 라인 분해 → 추가 매칭
        for line in block["lines"]:
            sub_items = split_compound_line(line)
            if len(sub_items) >= 3:
                for sub in sub_items:
                    for pattern, ben_key, category in BENEFIT_KEYWORDS:
                        if ben_key in seen_keys:
                            continue
                        if re.search(pattern, sub, re.IGNORECASE):
                            if not any(m[0] == ben_key for m in matched_in_block):
                                matched_in_block.append((ben_key, category, pattern))

        # 3) 매칭 결과 등록
        for ben_key, category, _ in matched_in_block:
            if ben_key in seen_keys:
                continue
            name = block["title"][:100]
            found.append({
                "company_id": company_id,
                "ben_key": ben_key,
                "name": name,
                "val": 0,
                "category": category,
                "badge": "est",
                "note": None,
                "is_qualitative": True,
                "qual_text": " ".join(block["lines"])[:500] if block["lines"] else None,
                "sort_order": len(found) + 1,
            })
            seen_keys.add(ben_key)

    return found


def escape_sql(s: str | None) -> str:
    if s is None:
        return "NULL"
    escaped = s.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def generate_sql(
    company_name: str,
    company_id: str,
    company_type: str,
    industry: str | None,
    benefits: list[dict],
    url: str,
) -> str:
    today = date.today().isoformat()
    logo = company_name[0]

    lines = [
        f"-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"-- {company_name} 복리후생 데이터",
        f"-- 출처: Playwright 스크래핑 ({today})",
        f"-- URL: {url}",
        f"-- badge: 'est' (추정치 — 공식 확인 시 'official'로 변경)",
        f"-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"-- 1) 회사 등록 (없는 경우)",
        f"INSERT IGNORE INTO companies (id, name, type_id, industry, logo, careers_benefit_url)",
        f"VALUES ('{company_id}', '{company_name}', '{company_type}', {escape_sql(industry)}, '{logo}', '{url}');",
        "",
        f"-- 2) 기존 추정 데이터 삭제 (official 보존)",
        f"DELETE FROM company_benefits WHERE company_id = '{company_id}' AND badge = 'est';",
        "",
        f"-- 3) 복리후생 INSERT",
        "INSERT INTO company_benefits",
        "  (company_id, ben_key, name, val, category, badge, note, is_qualitative, qual_text, sort_order)",
        "VALUES",
    ]

    value_lines = []
    for b in benefits:
        val_line = (
            f"  ('{b['company_id']}', '{b['ben_key']}', {escape_sql(b['name'])}, "
            f"{b['val']}, '{b['category']}', '{b['badge']}', {escape_sql(b['note'])}, "
            f"{'TRUE' if b['is_qualitative'] else 'FALSE'}, {escape_sql(b['qual_text'])}, "
            f"{b['sort_order']})"
        )
        value_lines.append(val_line)

    if value_lines:
        lines.append(",\n".join(value_lines) + ";")
    else:
        lines.append("  -- [NOTE] 자동 파싱된 항목 없음 — raw 텍스트를 참고하여 수동 작성 필요")
        lines.append("  ('placeholder', 'placeholder', 'placeholder', 0, 'financial', 'est', NULL, FALSE, NULL, 0);")

    return "\n".join(lines) + "\n"


async def main():
    parser = argparse.ArgumentParser(
        description="회사 복리후생 스크래핑 → SQL 파일 생성"
    )
    parser.add_argument("company", help="회사명 (한국어)")
    parser.add_argument("--url", required=True, help="채용/복지 페이지 URL")
    parser.add_argument("--id", dest="company_id", help="company_id slug (예: samsung)")
    parser.add_argument("--type", dest="company_type", default="large",
                        help="기업유형: large, startup, mid, foreign, public, freelance (기본: large)")
    parser.add_argument("--industry", help="업종 (예: 전자/반도체)")
    parser.add_argument("--screenshot", action="store_true", help="스크린샷 저장")
    parser.add_argument("--timeout", type=int, default=30000, help="페이지 로드 타임아웃 ms (기본: 30000)")
    parser.add_argument("--raw-only", action="store_true", help="Raw 텍스트만 출력, SQL 생성 안 함")
    args = parser.parse_args()

    company_id = resolve_company_id(args.company, args.company_id)
    BENEFIT_DIR.mkdir(parents=True, exist_ok=True)

    # ── 스크래핑 ──
    pw, browser, context = await create_browser()
    try:
        screenshot_path = str(BENEFIT_DIR / f"{args.company}.png") if args.screenshot else None
        result = await scrape_page(context, args.url, args.timeout, screenshot_path)
    except Exception as e:
        print(f"[ERROR] 스크래핑 실패: {e}")
        await browser.close()
        await pw.stop()
        sys.exit(1)
    finally:
        await browser.close()
        await pw.stop()

    raw_text = result["text"]

    # ── Raw 텍스트 저장 ──
    txt_path = BENEFIT_DIR / f"{args.company}.txt"
    txt_path.write_text(raw_text, encoding="utf-8")
    print(f"[INFO] Raw 텍스트 저장: {txt_path}")
    print(f"[INFO] 텍스트 길이: {len(raw_text)}자, {len(raw_text.splitlines())}줄")
    print()
    print("=" * 60)
    print("  RAW TEXT (처음 3000자)")
    print("=" * 60)
    print(raw_text[:3000])
    if len(raw_text) > 3000:
        print(f"\n... ({len(raw_text) - 3000}자 생략)")
    print("=" * 60)

    if args.raw_only:
        print("[INFO] --raw-only 모드: SQL 생성 생략")
        return

    # ── 키워드 파싱 ──
    benefits = parse_benefits(raw_text, company_id)
    print(f"\n[INFO] 자동 파싱된 복지 항목: {len(benefits)}개")
    for b in benefits:
        print(f"  - [{b['category']}] {b['ben_key']}: {b['name'][:50]}")

    # ── SQL 생성 ──
    sql = generate_sql(
        args.company, company_id, args.company_type,
        args.industry, benefits, args.url,
    )
    sql_path = BENEFIT_DIR / f"{args.company}.sql"
    sql_path.write_text(sql, encoding="utf-8")
    print(f"\n[INFO] SQL 파일 저장: {sql_path}")
    print(f"[WARN] 자동 파싱은 best-effort입니다. 반드시 수동 검수 후 사용하세요.")
    print(f"[HINT] Raw 텍스트: {txt_path}")


if __name__ == "__main__":
    asyncio.run(main())
