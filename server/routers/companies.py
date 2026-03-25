import json
from fastapi import APIRouter, Query
import database
from models.company import BenefitUpsert

router = APIRouter()

@router.get("/search")
async def search(q: str = Query(..., min_length=1)):
    q_like = f"%{q}%"
    rows = await database.fetch_all(
        """SELECT DISTINCT c.id, c.name, c.type_id AS type, c.industry, c.logo
           FROM companies c
           LEFT JOIN company_aliases ca ON ca.company_id = c.id
           WHERE c.name LIKE %s OR ca.alias LIKE %s
           LIMIT 20""",
        (q_like, q_like),
    )
    return rows

@router.get("/{company_id}")
async def detail(company_id: str):
    comp = await database.fetch_one(
        "SELECT id, name, type_id AS type, industry, logo, work_style FROM companies WHERE id=%s",
        (company_id,),
    )
    if not comp:
        return {"error": "not found"}

    aliases = await database.fetch_all(
        "SELECT alias FROM company_aliases WHERE company_id=%s", (company_id,)
    )
    benefits = await database.fetch_all(
        """SELECT ben_key AS `key`, name, val, category AS cat, badge,
                  note, is_qualitative AS qual, qual_text AS qualText
           FROM company_benefits WHERE company_id=%s ORDER BY sort_order""",
        (company_id,),
    )

    ws = comp.get("work_style")
    if isinstance(ws, str):
        ws = json.loads(ws)

    return {
        **comp,
        "work_style": ws,
        "aliases": [a["alias"] for a in aliases],
        "benefits": benefits,
    }

@router.put("/{company_id}/benefits")
async def upsert_benefits(company_id: str, items: list[BenefitUpsert]):
    comp = await database.fetch_one(
        "SELECT id FROM companies WHERE id=%s", (company_id,)
    )
    if not comp:
        return {"error": "company not found"}

    # 기존 복지 전체 삭제 후 재삽입 (중복 방지)
    await database.execute(
        "DELETE FROM company_benefits WHERE company_id=%s",
        (company_id,),
    )

    for i, b in enumerate(items):
        await database.execute(
            """INSERT INTO company_benefits
               (company_id, ben_key, name, val, category, badge, note, is_qualitative, qual_text, sort_order)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON DUPLICATE KEY UPDATE
               name=VALUES(name), val=VALUES(val), category=VALUES(category),
               badge=VALUES(badge), note=VALUES(note), is_qualitative=VALUES(is_qualitative),
               qual_text=VALUES(qual_text), sort_order=VALUES(sort_order)""",
            (company_id, b.key, b.name, b.val, b.cat, b.badge,
             b.note, b.qual, b.qualText, b.sortOrder or i),
        )

    benefits = await database.fetch_all(
        """SELECT ben_key AS `key`, name, val, category AS cat, badge,
                  note, is_qualitative AS qual, qual_text AS qualText
           FROM company_benefits WHERE company_id=%s ORDER BY sort_order""",
        (company_id,),
    )
    return {"count": len(benefits), "benefits": benefits}
