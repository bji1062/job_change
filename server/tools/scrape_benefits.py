#!/usr/bin/env python3
"""
회사 복리후생 스크래핑 → SQL 파일 생성 도구

Usage:
  python server/tools/scrape_benefits.py "삼성전자" --url "https://www.samsung-dxrecruit.com/benefit"
  python server/tools/scrape_benefits.py "네이버" --url "https://recruit.navercorp.com/..." --id naver
  python server/tools/scrape_benefits.py "현대자동차" --url "https://talent.hyundai.com/culture/benefit.hc" --type large --industry "자동차"
"""
import argparse
import asyncio
import re
import sys
from datetime import date
from pathlib import Path

# ━━ 회사명 → company_id 매핑 ━━
KNOWN_IDS = {
    "삼성전자": "samsung", "삼성": "samsung",
    "LG전자": "lg", "LG": "lg",
    "현대자동차": "hyundai", "현대차": "hyundai",
    "네이버": "naver", "NAVER": "naver",
    "카카오": "kakao",
    "SK하이닉스": "skhynix", "SK": "sk",
    "토스": "toss",
    "CJ그룹": "cj", "CJ": "cj",
    "쿠팡": "coupang",
    "배달의민족": "baemin", "우아한형제들": "baemin",
    "라인": "line", "LINE": "line",
    "당근": "daangn", "당근마켓": "daangn",
    "크래프톤": "krafton", "KRAFTON": "krafton",
    "넥슨": "nexon",
    "엔씨소프트": "ncsoft",
}

# ━━ 복지 키워드 → (ben_key, category) 매핑 ━━
BENEFIT_KEYWORDS = [
    # money
    (r"식대|구내식당|중식|조식|석식", "meal", "money"),
    (r"복지포인트|선택복지|카페테리아\s*포인트", "welfare_point", "money"),
    (r"교통비|주차", "transport", "money"),
    (r"경조사|경조금", "event", "money"),
    (r"성과급|인센티브|보너스", "bonus", "money"),
    (r"자사주|RSU|스톡옵션|주식", "stock", "money"),
    (r"통신비", "telecom", "money"),
    # health
    (r"건강검진|종합검진", "health_check", "health"),
    (r"의료비", "medical", "health"),
    (r"단체보험|생명보험|상해보험", "insurance", "health"),
    (r"심리상담|EAP|마음건강", "mental", "health"),
    (r"피트니스|헬스장|체력단련|운동", "fitness", "health"),
    (r"치과|한의원|부속의원|사내\s*병원", "clinic", "health"),
    # housing
    (r"주택.*대출|주택자금|사내대출|전세.*대출", "housing_loan", "housing"),
    (r"기숙사|사택|숙소", "dormitory", "housing"),
    # family
    (r"학자금|자녀.*교육", "child_edu", "family"),
    (r"출산|육아|임신|보육|어린이집", "parenting", "family"),
    (r"결혼|웨딩", "wedding", "family"),
    # life
    (r"통근.*버스|셔틀", "commute", "life"),
    (r"동호회|동아리|사내.*클럽", "club", "life"),
    (r"도서|북카페|라이브러리", "library", "life"),
    (r"여행|휴양|리조트|호텔|콘도", "resort", "life"),
    (r"할인.*구매|임직원.*할인|사내.*매장", "discount", "life"),
    # leave
    (r"리프레시.*휴가|안식.*휴가|장기.*휴가", "refresh_leave", "leave"),
    (r"유연.*근무|재택.*근무|원격.*근무|플렉스", "flex_work", "leave"),
    (r"연차|휴가|휴직", "leave_general", "leave"),
    # edu
    (r"어학|외국어|영어", "lang", "edu"),
    (r"자기.*개발|교육.*지원|직무.*교육|온라인.*강의", "edu_support", "edu"),
]

# ━━ 출력 경로 ━━
BENEFIT_DIR = Path(__file__).resolve().parent.parent / "seed" / "benefit"


def resolve_company_id(name: str, cli_id: str | None) -> str:
    if cli_id:
        return cli_id
    if name in KNOWN_IDS:
        return KNOWN_IDS[name]
    print(f"[ERROR] '{name}'의 company_id를 알 수 없습니다.")
    print(f"        --id 옵션으로 지정해주세요. 예: --id mycompany")
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


def parse_benefits(raw_text: str, company_id: str) -> list[dict]:
    """키워드 매칭으로 복리후생 항목 추출 (best-effort)"""
    found = []
    seen_keys = set()
    lines = raw_text.split("\n")

    for line in lines:
        line = line.strip()
        if not line or len(line) < 2:
            continue
        for pattern, ben_key, category in BENEFIT_KEYWORDS:
            if ben_key in seen_keys:
                continue
            if re.search(pattern, line):
                # 해당 라인을 복지명으로 사용 (최대 100자)
                name = line[:100].strip()
                found.append({
                    "company_id": company_id,
                    "ben_key": ben_key,
                    "name": name,
                    "val": 0,
                    "category": category,
                    "badge": "est",
                    "note": None,
                    "is_qualitative": True,
                    "qual_text": line[:500] if len(line) > 100 else None,
                    "sort_order": len(found) + 1,
                })
                seen_keys.add(ben_key)
                break

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
        lines.append("  ('placeholder', 'placeholder', 'placeholder', 0, 'money', 'est', NULL, FALSE, NULL, 0);")

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
