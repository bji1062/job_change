import json
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import database
from services import cache

router = APIRouter()

@router.get("/all")
async def get_all():
    cached = cache.get("reference_all")
    if cached:
        return JSONResponse(content=cached, headers={"Cache-Control": "public, max-age=3600"})

    # Company types
    types = await database.fetch_all("SELECT * FROM company_types")

    # Benefit presets grouped by type_id
    preset_rows = await database.fetch_all(
        "SELECT type_id, ben_key AS `key`, name, val, category AS cat, badge, checked_default AS checked FROM benefit_presets ORDER BY sort_order"
    )
    ben_presets = {}
    for r in preset_rows:
        tid = r.pop("type_id")
        r["checked"] = bool(r["checked"])
        ben_presets.setdefault(tid, []).append(r)

    # Companies — single query
    companies = await database.fetch_all(
        "SELECT id, name, type_id AS type, industry, logo, work_style FROM companies"
    )
    for c in companies:
        if isinstance(c.get("work_style"), str):
            c["work_style"] = json.loads(c["work_style"])

    # Aliases — batch (1 query instead of N)
    all_aliases = await database.fetch_all("SELECT company_id, alias FROM company_aliases")
    alias_map = {}
    for a in all_aliases:
        alias_map.setdefault(a["company_id"], []).append(a["alias"])

    # Benefits — batch (1 query instead of N)
    all_bens = await database.fetch_all(
        """SELECT company_id, ben_key AS `key`, name, val, category AS cat, badge,
                  note, is_qualitative AS qual, qual_text AS qualText
           FROM company_benefits ORDER BY sort_order"""
    )
    ben_map = {}
    for b in all_bens:
        cid = b.pop("company_id")
        ben_map.setdefault(cid, []).append(b)

    for c in companies:
        c["aliases"] = alias_map.get(c["id"], [])
        c["benefits"] = ben_map.get(c["id"], [])

    # Profiles — single query
    profiles = await database.fetch_all("SELECT * FROM profiles")
    for p in profiles:
        if isinstance(p.get("vec"), str):
            p["vec"] = json.loads(p["vec"])

    # Profile job fits — batch (1 query instead of 8)
    all_fits = await database.fetch_all("SELECT profile_id, scenario, fit, caution FROM profile_job_fits")
    fit_map = {}
    for f in all_fits:
        fit_map.setdefault(f["profile_id"], {})[f["scenario"]] = {"fit": f["fit"], "caution": f["caution"]}
    for p in profiles:
        p["jobFit"] = fit_map.get(p["id"], {})

    # Job groups + jobs — batch (1 query instead of 5)
    groups = await database.fetch_all("SELECT * FROM job_groups ORDER BY sort_order")
    all_jobs = await database.fetch_all("SELECT id, group_id, label, icon, scenario FROM jobs ORDER BY sort_order")
    job_map = {}
    for j in all_jobs:
        gid = j.pop("group_id")
        job_map.setdefault(gid, []).append(j)
    for g in groups:
        g["jobs"] = job_map.get(g["id"], [])

    # Profiler questions — single query
    questions = await database.fetch_all("SELECT * FROM profiler_questions ORDER BY id")
    for q in questions:
        if isinstance(q.get("option_a_fx"), str):
            q["option_a_fx"] = json.loads(q["option_a_fx"])
        if isinstance(q.get("option_b_fx"), str):
            q["option_b_fx"] = json.loads(q["option_b_fx"])

    # Question scenario descriptions — single query
    q_desc_rows = await database.fetch_all("SELECT * FROM question_scenarios ORDER BY question_id")
    q_desc = {}
    for r in q_desc_rows:
        q_desc.setdefault(r["scenario"], []).append({"a": r["desc_a"], "b": r["desc_b"]})

    data = {
        "companyTypes": types,
        "benPresets": ben_presets,
        "companies": companies,
        "profiles": [
            {"id": p["id"], "type": p["type_name"], "desc": p["description"],
             "mapPri": p["map_priority"], "vec": p["vec"], "jobFit": p["jobFit"]}
            for p in profiles
        ],
        "jobGroups": [
            {"groupLabel": g["group_label"], "color": g["color"], "jobs": g["jobs"]}
            for g in groups
        ],
        "questions": [
            {"id": q["id"], "label": q["label"],
             "a": {"title": q["option_a_title"], "fx": q["option_a_fx"]},
             "b": {"title": q["option_b_title"], "fx": q["option_b_fx"]}}
            for q in questions
        ],
        "questionDescs": q_desc,
    }

    cache.set("reference_all", data)
    return JSONResponse(content=data, headers={"Cache-Control": "public, max-age=3600"})
