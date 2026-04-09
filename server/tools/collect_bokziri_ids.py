#!/usr/bin/env python3
"""
복지리(bokziri.com)에서 회사별 UUID를 자동 수집하고,
수집된 UUID로 scrape_benefits.py 명령어를 생성하는 스크립트.

Usage:
  # 전체 실행 (UUID 수집 + 명령어 생성)
  server/tools/.venv/bin/python server/tools/collect_bokziri_ids.py

  # 이미 수집된 JSON에서 명령어만 재생성
  server/tools/.venv/bin/python server/tools/collect_bokziri_ids.py --skip-collect
"""
import argparse
import asyncio
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

# ━━ 회사 목록 (KOSPI + KOSDAQ 200개) ━━
# scrape_commands 파일에서 사용하는 회사명 기준
COMPANIES = [
    # ── KOSPI 1~50 ──
    "삼성전자", "SK하이닉스", "LG에너지솔루션", "삼성바이오로직스",
    "현대자동차", "HD현대중공업", "SK스퀘어", "한화에어로스페이스",
    "두산에너빌리티", "KB금융", "기아", "셀트리온",
    "삼성물산", "NAVER", "신한지주", "한화오션",
    "현대모비스", "삼성생명", "한국전력", "HD한국조선해양",
    "HD현대일렉트릭", "카카오", "하나금융지주", "POSCO홀딩스",
    "고려아연", "알테오젠", "LG화학", "삼성화재",
    "삼성SDI", "삼성중공업", "우리금융지주", "현대로템",
    "메리츠금융지주", "HMM", "삼성전기", "SK",
    "SK이노베이션", "KT&G", "IBK기업은행", "포스코퓨처엠",
    "효성중공업", "LG전자", "HD현대", "에코프로비엠",
    "하이브", "LS ELECTRIC", "현대글로비스", "삼성SDS",
    "KT", "미래에셋증권",
    # ── KOSPI 51~100 ──
    "두산", "LG", "에코프로", "한미반도체",
    "크래프톤", "SK텔레콤", "한국항공우주산업", "에이비엘바이오",
    "카카오뱅크", "한화시스템", "SK바이오팜", "S-Oil",
    "DB손해보험", "삼양식품", "LIG넥스원", "레인보우로보틱스",
    "현대오토에버", "코오롱티슈진", "유한양행", "이수페타시스",
    "포스코인터내셔널", "HD현대마린솔루션", "에이피알", "대한항공",
    "한진칼", "현대건설", "키움증권", "NH투자증권",
    "한국타이어앤테크놀로지", "아모레퍼시픽", "삼성증권", "HLB",
    "카카오페이", "삼성카드", "LG이노텍", "리가켐바이오",
    "LS", "LG유플러스", "코웨이", "한화",
    "LG씨엔에스", "펩트론", "LG디스플레이", "한미약품",
    "두산밥캣", "삼천당제약", "한국금융지주", "삼성에피스홀딩스",
    "현대제철", "롯데케미칼",
    # ── KOSDAQ 1~50 ──
    "케어젠", "리노공업", "디앤디파마텍", "보로노이",
    "파마리서치", "원익IPS", "클래시스", "메지온",
    "이오테크닉스", "로보티즈", "HPSP", "ISC",
    "오스코텍", "한솔케미칼", "올릭스", "엘앤씨바이오",
    "테크윙", "휴젤", "솔브레인", "유진테크",
    "파크시스템스", "덕산네오룩스", "에이디테크놀로지", "티씨케이",
    "피에스케이", "주성엔지니어링", "셀트리온제약", "심텍",
    "HLB생명과학", "동국제약", "네패스", "씨젠",
    "성일하이텍", "SM엔터테인먼트", "인터로조", "CJ ENM",
    "비에이치", "JYP엔터테인먼트", "실리콘투",
    # ── KOSDAQ 51~100 ──
    "위메이드", "카카오게임즈", "HLB테라퓨틱스", "HLB이노베이션",
    "컴투스", "펄어비스", "솔브레인홀딩스", "나노엔텍",
    "다우데이타", "HLB제약", "엠씨넥스", "서울반도체",
    "코미팜", "더블유게임즈", "에스티큐브", "네오위즈",
    "피에스케이홀딩스", "제이엘케이", "나노신소재", "엠투아이",
    "티에스이", "원익QnC", "케이엠더블유", "에코프로에이치엔",
    "셀리드", "와이바이오로직스", "루닛", "엔켐",
    "제넥신", "에임드바이오", "GC녹십자셀", "엘오티베큠",
    "동화기업", "아이패밀리에스씨", "켐트로스", "선익시스템",
    "앱클론", "지놈앤컴퍼니", "에스에프에이", "아이센스",
    "텔레칩스", "바이넥스", "켐트로닉스", "매커스",
    "리메드", "유비쿼스홀딩스", "원방테크", "코오롱인더스트리 FnC",
    "현대무벡스", "노바텍",
]

# ━━ 출력 경로 ━━
TOOLS_DIR = Path(__file__).resolve().parent
OUTPUT_JSON = TOOLS_DIR / "bokziri_ids.json"
OUTPUT_SCRAPE_SH = TOOLS_DIR / "scrape_commands_bokziri.sh"


async def create_browser():
    from playwright.async_api import async_playwright
    import os

    pw = await async_playwright().start()
    chromium_path = None
    for p in Path("/root/.cache/ms-playwright").glob("chromium-*/chrome-linux/chrome"):
        chromium_path = str(p)
        break

    proxy_config = None
    proxy_url = os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY")
    if proxy_url:
        from urllib.parse import urlparse
        parsed = urlparse(proxy_url)
        proxy_config = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
        if parsed.username:
            proxy_config["username"] = parsed.username
        if parsed.password:
            proxy_config["password"] = parsed.password

    launch_args = {
        "headless": True,
        "executable_path": chromium_path,
        "args": ["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"],
    }
    if proxy_config:
        launch_args["proxy"] = proxy_config

    browser = await pw.chromium.launch(**launch_args)
    context = await browser.new_context(
        ignore_https_errors=True,
        viewport={"width": 1920, "height": 1080},
        locale="ko-KR",
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    )
    await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
    return pw, browser, context


async def search_company(context, company_name: str, retry: int = 2) -> dict | None:
    """복지리에서 회사 검색 → 첫 번째 결과의 UUID와 표시 이름 반환"""
    encoded = quote(company_name)
    url = f"https://www.bokziri.com/#searchKeyword={encoded}&categoryFilter="

    for attempt in range(retry + 1):
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=20000)
            await page.wait_for_timeout(3000)  # SPA 렌더링 대기

            # 회사 링크 추출: /company/{uuid} 패턴
            links = await page.evaluate("""
                () => {
                    const results = [];
                    const anchors = document.querySelectorAll('a[href*="/company/"]');
                    for (const a of anchors) {
                        const href = a.getAttribute('href');
                        const match = href.match(/\\/company\\/([a-zA-Z0-9]+)/);
                        if (match) {
                            const text = a.innerText.trim().split('\\n')[0].trim();
                            results.push({uuid: match[1], name: text, href: href});
                        }
                    }
                    return results;
                }
            """)

            if links:
                # 첫 번째 결과 반환
                return {"uuid": links[0]["uuid"], "bokziri_name": links[0]["name"], "url": f"https://www.bokziri.com/company/{links[0]['uuid']}"}

            if attempt < retry:
                print(f"  [RETRY] '{company_name}' 결과 없음, 재시도 {attempt + 1}/{retry}")
                await page.wait_for_timeout(2000)
            else:
                return None
        except Exception as e:
            if attempt < retry:
                print(f"  [RETRY] '{company_name}' 에러: {e}, 재시도 {attempt + 1}/{retry}")
            else:
                print(f"  [ERROR] '{company_name}' 실패: {e}")
                return None
        finally:
            await page.close()

    return None


async def collect_all(companies: list[str]) -> dict:
    """모든 회사의 복지리 UUID 수집"""
    pw, browser, context = await create_browser()
    results = {}
    not_found = []

    try:
        for i, name in enumerate(companies):
            print(f"[{i+1}/{len(companies)}] '{name}' 검색 중...")
            result = await search_company(context, name)

            if result:
                results[name] = result
                print(f"  → UUID: {result['uuid']} ({result['bokziri_name']})")
            else:
                not_found.append(name)
                print(f"  → 미발견")

            # 요청 간격 (서버 부하 방지)
            if i < len(companies) - 1:
                await asyncio.sleep(1)
    finally:
        await browser.close()
        await pw.stop()

    return {"found": results, "not_found": not_found}


def generate_scrape_commands(data: dict) -> str:
    """수집된 UUID로 scrape_benefits.py 명령어 생성"""
    lines = [
        "#!/bin/bash",
        "# 복지리(bokziri.com) 기반 복지 스크래핑 명령어",
        f"# 총 {len(data['found'])}개 회사 (미발견: {len(data['not_found'])}개)",
        f"# 생성일: {__import__('datetime').date.today().isoformat()}",
        "",
    ]

    for name, info in data["found"].items():
        lines.append(
            f'server/tools/.venv/bin/python server/tools/scrape_benefits.py "{name}" '
            f'--url "{info["url"]}" --raw-only'
        )

    if data["not_found"]:
        lines.append("")
        lines.append("# ━━ 미발견 회사 (수동 확인 필요) ━━")
        for name in data["not_found"]:
            lines.append(f'# [NOT FOUND] "{name}"')

    return "\n".join(lines) + "\n"


async def main():
    parser = argparse.ArgumentParser(description="복지리 UUID 수집 + 스크래핑 명령어 생성")
    parser.add_argument("--skip-collect", action="store_true", help="기존 JSON에서 명령어만 재생성")
    args = parser.parse_args()

    if args.skip_collect:
        if not OUTPUT_JSON.exists():
            print(f"[ERROR] {OUTPUT_JSON} 파일이 없습니다. --skip-collect 없이 먼저 실행하세요.")
            sys.exit(1)
        data = json.loads(OUTPUT_JSON.read_text(encoding="utf-8"))
        print(f"[INFO] 기존 JSON 로드: {len(data['found'])}개 회사")
    else:
        print(f"[INFO] 복지리 UUID 수집 시작 ({len(COMPANIES)}개 회사)")
        print("=" * 60)
        data = await collect_all(COMPANIES)

        # JSON 저장
        OUTPUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print()
        print("=" * 60)
        print(f"[INFO] UUID 수집 완료: {len(data['found'])}개 발견, {len(data['not_found'])}개 미발견")
        print(f"[INFO] JSON 저장: {OUTPUT_JSON}")

    # 스크래핑 명령어 생성
    sh_content = generate_scrape_commands(data)
    OUTPUT_SCRAPE_SH.write_text(sh_content, encoding="utf-8")
    OUTPUT_SCRAPE_SH.chmod(0o755)
    print(f"[INFO] 스크래핑 명령어 저장: {OUTPUT_SCRAPE_SH}")

    if data["not_found"]:
        print(f"\n[WARN] 미발견 회사 {len(data['not_found'])}개:")
        for name in data["not_found"]:
            print(f"  - {name}")


if __name__ == "__main__":
    asyncio.run(main())
