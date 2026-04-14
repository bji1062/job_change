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
import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from datetime import date
from pathlib import Path



# ━━ 복지 키워드 → (ben_key, category) 매핑 ━━
# 카테고리: compensation, perks, work_env, health, time, growth, family, life, culture
BENEFIT_KEYWORDS = [
    # ━━ compensation (보상) ━━
    (r"성과급|인센티브|보너스", "bonus", "compensation"),
    (r"자사주|RSU|스톡옵션|주식\s*매입|주식\s*보상", "stock", "compensation"),
    # ━━ perks (금전·지원) ━━
    (r"복지\s*포인트|복리\s*포인트|선택.{0,2}복[리지]|카페테리아\s*포인트|업무\s*지원비|통신비", "welfare_point", "perks"),
    (r"할인.*구매|임직원.*할인|사내.*매장|자사.*제품|서비스\s*이용권", "discount", "perks"),
    (r"주택.*대출|주택자금|사내\s*대출|전세.*대출|대출.*이자|대출.*지원", "housing_loan", "perks"),
    (r"기숙사|사택|숙소", "dormitory", "perks"),
    # ━━ family (경조·가족) ━━
    (r"경조사|경조금|명절", "event", "family"),
    # ━━ work_env (근무환경) ━━
    (r"식대|식당|식사|중식|조식|석식|세\s*끼|카페|캔틴", "meal", "work_env"),
    (r"교통비|주차|통근|셔틀", "transport", "work_env"),
    (r"업무\s*기기|노트북|모니터|장비.*지원|가구|허먼밀러|스탠딩\s*데스크", "work_tools", "work_env"),
    # ━━ health (건강·의료) ━━
    (r"건강\s*검진|종합\s*검진|심리\s*검진", "health_check", "health"),
    (r"의료비|의료.*보험|실손|진단비|의료.*상담", "medical", "health"),
    (r"단체\s*보험|생명\s*보험|상해\s*보험", "insurance", "health"),
    (r"심리\s*상담|EAP|마음\s*건강|심리\s*센터", "mental", "health"),
    (r"피트니스|헬스장|체력단련|수영장|트레이너", "fitness", "health"),
    (r"부속의원|사내\s*병원|치과|한의원|약국|물리\s*치료|재활|근골격|이비인후|비뇨", "clinic", "health"),
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
    """회사명 → COMP_ENG_NM 조회. DB 의 TCOMPANY.COMP_NM + TCOMPANY_ALIAS.ALIAS_NM 에서 검색."""
    if cli_id:
        return cli_id
    import pymysql
    conn = pymysql.connect(
        host=config.DB_HOST, port=config.DB_PORT,
        user=config.DB_USER, password=config.DB_PASS,
        db=config.DB_NAME, charset="utf8mb4",
    )
    try:
        cur = conn.cursor()
        cur.execute("SELECT COMP_ENG_NM FROM TCOMPANY WHERE COMP_NM=%s", (name,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(
            "SELECT c.COMP_ENG_NM FROM TCOMPANY c "
            "JOIN TCOMPANY_ALIAS a ON a.COMP_ID = c.COMP_ID "
            "WHERE a.ALIAS_NM=%s LIMIT 1",
            (name,),
        )
        row = cur.fetchone()
        if row:
            return row[0]
    finally:
        conn.close()
    print(f"[ERROR] '{name}' 이 DB(TCOMPANY/TCOMPANY_ALIAS)에 없습니다.")
    print(f"        --id 옵션으로 직접 지정하거나 DB에 회사를 먼저 등록하세요.")
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
        f"-- 1) 회사 등록 (없는 경우) — COMP_TP_ID는 코드 조회",
        f"INSERT IGNORE INTO TCOMPANY (COMP_ENG_NM, COMP_NM, COMP_TP_ID, INDUSTRY_NM, LOGO_NM, CAREERS_BENEFIT_URL)",
        f"VALUES ('{company_id}', '{company_name}', (SELECT COMP_TP_ID FROM TCOMPANY_TYPE WHERE COMP_TP_CD='{company_type}'), {escape_sql(industry)}, '{logo}', '{url}');",
        "",
        f"-- 2) 기존 추정 데이터 삭제 (official 보존)",
        f"DELETE FROM TCOMPANY_BENEFIT WHERE COMP_ID = (SELECT COMP_ID FROM TCOMPANY WHERE COMP_ENG_NM='{company_id}') AND BADGE_CD = 'est';",
        "",
        f"-- 3) 복리후생 INSERT",
        "INSERT INTO TCOMPANY_BENEFIT",
        "  (COMP_ID, BENEFIT_CD, BENEFIT_NM, BENEFIT_AMT, BENEFIT_CTGR_CD, BADGE_CD, NOTE_CTNT, QUAL_YN, QUAL_DESC_CTNT, SORT_ORDER_NO)",
        "VALUES",
    ]

    comp_id_subq = f"(SELECT COMP_ID FROM TCOMPANY WHERE COMP_ENG_NM='{company_id}')"
    value_lines = []
    for b in benefits:
        val_line = (
            f"  ({comp_id_subq}, '{b['ben_key']}', {escape_sql(b['name'])}, "
            f"{b['val']}, '{b['category']}', '{b['badge']}', {escape_sql(b['note'])}, "
            f"{'TRUE' if b['is_qualitative'] else 'FALSE'}, {escape_sql(b['qual_text'])}, "
            f"{b['sort_order']})"
        )
        value_lines.append(val_line)

    if value_lines:
        lines.append(",\n".join(value_lines) + ";")
    else:
        lines.append("  -- [NOTE] 자동 파싱된 항목 없음 — raw 텍스트를 참고하여 수동 작성 필요")
        lines.append(f"  ({comp_id_subq}, 'placeholder', 'placeholder', 0, 'perks', 'est', NULL, FALSE, NULL, 0);")

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
