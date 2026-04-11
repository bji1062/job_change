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


def _load_type_map(cur):
    """TCOMPANY_TYPE 코드 → INT PK 매핑 로드"""
    cur.execute("SELECT COMP_TP_ID, COMP_TP_CD FROM TCOMPANY_TYPE")
    return {row[1]: row[0] for row in cur.fetchall()}


def seed_companies(cur):
    """TCOMPANY 테이블에 INSERT (중복 시 SKIP). COMP_ENG_NM에 기존 영문 id 저장."""
    tp_map = _load_type_map(cur)
    sql = """
        INSERT IGNORE INTO TCOMPANY (COMP_ENG_NM, COMP_NM, COMP_TP_ID, INDUSTRY_NM, LOGO_NM, CAREERS_BENEFIT_URL)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    rows = []
    for c in ALL_COMPANIES:
        rows.append((
            c["id"],
            c["name"],
            tp_map.get(c["type"]),
            c.get("industry"),
            c.get("logo"),
            c.get("careersUrl", ""),
        ))
    cur.executemany(sql, rows)
    print(f"  TCOMPANY: {cur.rowcount} rows inserted")


def seed_aliases(cur):
    """TCOMPANY_ALIAS 테이블에 INSERT (중복 시 SKIP). COMP_ENG_NM → COMP_ID 매핑 후 INT FK 사용."""
    cur.execute("SELECT COMP_ID, COMP_ENG_NM FROM TCOMPANY")
    eng_to_id = {row[1]: row[0] for row in cur.fetchall()}
    sql = """
        INSERT IGNORE INTO TCOMPANY_ALIAS (COMP_ID, ALIAS_NM)
        VALUES (%s, %s)
    """
    rows = []
    for c in ALL_COMPANIES:
        comp_id = eng_to_id.get(c["id"])
        if not comp_id:
            continue
        for alias in c.get("aliases", []):
            rows.append((comp_id, alias))
    if rows:
        cur.executemany(sql, rows)
    print(f"  TCOMPANY_ALIAS: {cur.rowcount} rows inserted")


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
