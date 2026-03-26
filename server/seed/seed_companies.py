"""
Seed script — KOSPI/KOSDAQ 시가총액 상위 200개 회사 데이터를 MySQL에 삽입.
Usage: cd server && python seed/seed_companies.py

기존 seed.py의 CJ, 토스 데이터와 중복되지 않도록 id가 다르게 설정됨.
benefits는 company_types의 benefit_presets를 사용 (개별 복지 데이터는 추후 추가).
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymysql
import config

from seed.companies_kospi_1 import KOSPI_1
from seed.companies_kospi_2 import KOSPI_2
from seed.companies_kosdaq_1 import KOSDAQ_1
from seed.companies_kosdaq_2 import KOSDAQ_2

ALL_COMPANIES = KOSPI_1 + KOSPI_2 + KOSDAQ_1 + KOSDAQ_2


def get_conn():
    return pymysql.connect(
        host=config.DB_HOST,
        port=int(config.DB_PORT),
        user=config.DB_USER,
        password=config.DB_PASS,
        database=config.DB_NAME,
        charset="utf8mb4",
        autocommit=False,
    )


def seed_companies(cur):
    """companies 테이블에 INSERT (중복 시 SKIP)"""
    sql = """
        INSERT IGNORE INTO companies (id, name, type_id, industry, logo, careers_benefit_url)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    rows = []
    for c in ALL_COMPANIES:
        rows.append((
            c["id"],
            c["name"],
            c["type"],
            c.get("industry"),
            c.get("logo"),
            c.get("careersUrl", ""),
        ))
    cur.executemany(sql, rows)
    print(f"  companies: {cur.rowcount} rows inserted")


def seed_aliases(cur):
    """company_aliases 테이블에 INSERT (중복 시 SKIP)"""
    sql = """
        INSERT IGNORE INTO company_aliases (company_id, alias)
        VALUES (%s, %s)
    """
    rows = []
    for c in ALL_COMPANIES:
        for alias in c.get("aliases", []):
            rows.append((c["id"], alias))
    cur.executemany(sql, rows)
    print(f"  aliases: {cur.rowcount} rows inserted")


def main():
    print(f"총 {len(ALL_COMPANIES)}개 회사 데이터 시딩 시작...")

    # 중복 id 체크
    ids = [c["id"] for c in ALL_COMPANIES]
    dupes = [x for x in set(ids) if ids.count(x) > 1]
    if dupes:
        print(f"  [WARN] 중복 id 발견: {dupes}")
        # 중복 제거 (첫 번째만 유지)
        seen = set()
        unique = []
        for c in ALL_COMPANIES:
            if c["id"] not in seen:
                seen.add(c["id"])
                unique.append(c)
        ALL_COMPANIES.clear()
        ALL_COMPANIES.extend(unique)
        print(f"  중복 제거 후 {len(ALL_COMPANIES)}개")

    conn = get_conn()
    try:
        cur = conn.cursor()
        seed_companies(cur)
        seed_aliases(cur)
        conn.commit()
        print("시딩 완료!")
    except Exception as e:
        conn.rollback()
        print(f"에러 발생, 롤백: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
