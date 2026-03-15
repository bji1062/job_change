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

    # Companies (brief)
    companies = await database.fetch_all(
        "SELECT id, name, type_id AS type, industry, logo, work_style FROM companies"
    )
    for c in companies:
        if isinstance(c.get("work_style"), str):
            c["work_style"] = json.loads(c["work_style"])
        # load aliases
        aliases = await database.fetch_all(
            "SELECT alias FROM company_aliases WHERE company_id=%s", (c["id"],)
        )
        c["aliases"] = [a["alias"] for a in aliases]
        # load benefits
        bens = await database.fetch_all(
            """SELECT ben_key AS `key`, name, val, category AS cat, badge,
                      note, is_qualitative AS qual, qual_text AS qualText
               FROM company_benefits WHERE company_id=%s ORDER BY sort_order""",
            (c["id"],),
        )
        c["benefits"] = bens

    # Profiles
    profiles = await database.fetch_all("SELECT * FROM profiles")
    for p in profiles:
        if isinstance(p.get("vec"), str):
            p["vec"] = json.loads(p["vec"])
        # load job fits
        fits = await database.fetch_all(
            "SELECT scenario, fit, caution FROM profile_job_fits WHERE profile_id=%s", (p["id"],)
        )
        p["jobFit"] = {f["scenario"]: {"fit": f["fit"], "caution": f["caution"]} for f in fits}

    # Job groups
    groups = await database.fetch_all("SELECT * FROM job_groups ORDER BY sort_order")
    for g in groups:
        jobs = await database.fetch_all(
            "SELECT id, label, icon, scenario FROM jobs WHERE group_id=%s ORDER BY sort_order", (g["id"],)
        )
        g["jobs"] = jobs

    # Profiler questions
    questions = await database.fetch_all("SELECT * FROM profiler_questions ORDER BY id")
    for q in questions:
        if isinstance(q.get("option_a_fx"), str):
            q["option_a_fx"] = json.loads(q["option_a_fx"])
        if isinstance(q.get("option_b_fx"), str):
            q["option_b_fx"] = json.loads(q["option_b_fx"])

    # Question scenario descriptions
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
