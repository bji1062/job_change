#!/usr/bin/env python3
"""
회사 목록 파일 기반 → 복지리(bokziri.com) UUID 매핑 → 스크래핑 명령어 생성

Usage:
  # 전체 실행 (company_list.txt + 복지리 UUID 수집 + 명령어 생성)
  python3 server/tools/collect_bokziri_ids_v2.py

  # 이미 수집된 JSON에서 명령어만 재생성
  python3 server/tools/collect_bokziri_ids_v2.py --skip-collect

  # 중단 후 이어서 수집 (기존 JSON에 없는 회사만)
  python3 server/tools/collect_bokziri_ids_v2.py --resume
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path
from urllib.parse import quote

# ━━ 경로 ━━
TOOLS_DIR = Path(__file__).resolve().parent
COMPANY_LIST_FILE = TOOLS_DIR / "company_list.txt"
OUTPUT_JSON = TOOLS_DIR / "bokziri_ids_v2.json"
OUTPUT_SCRAPE_SH = TOOLS_DIR / "scrape_commands_bokziri_v2.sh"


def load_companies() -> list[dict]:
    """company_list.txt에서 회사 목록 로드 (중복/빈줄 제거)"""
    if not COMPANY_LIST_FILE.exists():
        print(f"[ERROR] {COMPANY_LIST_FILE} 파일이 없습니다.")
        sys.exit(1)

    seen = set()
    companies = []
    for line in COMPANY_LIST_FILE.read_text(encoding="utf-8").splitlines():
        name = line.strip()
        if name and name not in seen:
            seen.add(name)
            companies.append({"name": name})

    print(f"[INFO] 회사 목록 로드: {len(companies)}개")
    return companies


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


async def search_bokziri(context, company_name: str, retry: int = 2) -> dict | None:
    """복지리에서 회사 검색 -> 첫 번째 결과의 UUID 반환"""
    encoded = quote(company_name)
    url = f"https://www.bokziri.com/#searchKeyword={encoded}&categoryFilter="

    for attempt in range(retry + 1):
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=20000)
            await page.wait_for_timeout(3000)

            links = await page.evaluate("""
                () => {
                    const results = [];
                    const anchors = document.querySelectorAll('a[href*="/company/"]');
                    for (const a of anchors) {
                        const href = a.getAttribute('href');
                        const match = href.match(/\\/company\\/([a-zA-Z0-9]+)/);
                        if (match) {
                            const text = a.innerText.trim().split('\\n')[0].trim();
                            results.push({uuid: match[1], name: text});
                        }
                    }
                    return results;
                }
            """)

            if links:
                return {"uuid": links[0]["uuid"], "bokziri_name": links[0]["name"]}

            if attempt < retry:
                await page.wait_for_timeout(2000)
            else:
                return None
        except Exception as e:
            if attempt >= retry:
                print(f"  [ERROR] '{company_name}' 실패: {e}")
                return None
        finally:
            await page.close()

    return None


async def collect_all(companies: list[dict], existing: dict | None = None) -> dict:
    """모든 회사의 복지리 UUID 수집"""
    pw, browser, context = await create_browser()
    found = existing.get("found", {}) if existing else {}
    not_found = existing.get("not_found", []) if existing else []
    not_found_names = {item["name"] for item in not_found}
    skipped = 0

    try:
        for i, comp in enumerate(companies):
            name = comp["name"]

            if name in found:
                skipped += 1
                continue

            print(f"[{i+1}/{len(companies)}] '{name}' 검색 중...")
            result = await search_bokziri(context, name)

            if result:
                found[name] = {
                    "uuid": result["uuid"],
                    "bokziri_name": result["bokziri_name"],
                    "url": f"https://www.bokziri.com/company/{result['uuid']}",
                }
                print(f"  -> UUID: {result['uuid']} ({result['bokziri_name']})")
            else:
                if name not in not_found_names:
                    not_found.append({"name": name})
                    not_found_names.add(name)
                print(f"  -> 미발견")

            # 50개마다 중간 저장
            if (i + 1) % 50 == 0:
                _save_json({"found": found, "not_found": not_found})
                print(f"  [SAVE] 중간 저장 ({len(found)}개 발견)")

            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print(f"\n[INFO] 중단됨. 현재까지 저장합니다...")
    finally:
        _save_json({"found": found, "not_found": not_found})
        await browser.close()
        await pw.stop()

    if skipped:
        print(f"[INFO] 기존 수집 데이터 스킵: {skipped}개")

    return {"found": found, "not_found": not_found}


def _save_json(data: dict):
    OUTPUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_scrape_commands(data: dict) -> str:
    """수집된 UUID로 scrape_benefits.py 명령어 생성"""
    from datetime import date

    found = data["found"]
    not_found = data.get("not_found", [])

    lines = [
        "#!/bin/bash",
        "# 복지리(bokziri.com) 기반 복지 스크래핑 명령어",
        f"# 총 {len(found)}개 회사",
        f"# 미발견: {len(not_found)}개",
        f"# 생성일: {date.today().isoformat()}",
        "",
    ]

    for name, info in found.items():
        lines.append(
            f'server/tools/.venv/bin/python server/tools/scrape_benefits.py "{name}" '
            f'--url "{info["url"]}" --raw-only'
        )

    if not_found:
        lines.append("")
        lines.append("# ━━ 미발견 회사 (복지리에 미등록) ━━")
        for comp in not_found:
            lines.append(f'# [NOT FOUND] {comp["name"]}')

    return "\n".join(lines) + "\n"


async def main():
    parser = argparse.ArgumentParser(description="회사 목록 → 복지리 UUID 수집 → 스크래핑 명령어 생성")
    parser.add_argument("--skip-collect", action="store_true", help="기존 JSON에서 명령어만 재생성")
    parser.add_argument("--resume", action="store_true", help="기존 JSON에 없는 회사만 추가 수집")
    args = parser.parse_args()

    if args.skip_collect:
        if not OUTPUT_JSON.exists():
            print(f"[ERROR] {OUTPUT_JSON} 파일이 없습니다.")
            sys.exit(1)
        data = json.loads(OUTPUT_JSON.read_text(encoding="utf-8"))
        print(f"[INFO] 기존 JSON 로드: {len(data['found'])}개 회사")
    else:
        companies = load_companies()

        existing = None
        if args.resume and OUTPUT_JSON.exists():
            existing = json.loads(OUTPUT_JSON.read_text(encoding="utf-8"))
            print(f"[INFO] 기존 데이터 로드: {len(existing['found'])}개 (이어서 수집)")

        print(f"\n[INFO] 복지리 UUID 수집 시작 ({len(companies)}개 회사)")
        print("=" * 60)
        data = await collect_all(companies, existing)

        print()
        print("=" * 60)
        print(f"[INFO] 수집 완료: {len(data['found'])}개 발견, {len(data['not_found'])}개 미발견")
        print(f"[INFO] JSON 저장: {OUTPUT_JSON}")

    sh_content = generate_scrape_commands(data)
    OUTPUT_SCRAPE_SH.write_text(sh_content, encoding="utf-8")
    OUTPUT_SCRAPE_SH.chmod(0o755)
    print(f"[INFO] 스크래핑 명령어 저장: {OUTPUT_SCRAPE_SH}")

    if data.get("not_found"):
        print(f"\n[WARN] 미발견 {len(data['not_found'])}개 (복지리 미등록)")


if __name__ == "__main__":
    asyncio.run(main())
