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
    types = await database.fetch_all(
        """SELECT COMP_TP_CD AS id, COMP_TP_NM AS label,
                  GROWTH_RATE_VAL AS growth_rate, GROWTH_LABEL_NM AS growth_label,
                  STABILITY_SCORE_NO AS stability_score
           FROM TCOMPANY_TYPE"""
    )

    # Benefit presets grouped by company type code
    preset_rows = await database.fetch_all(
        """SELECT ct.COMP_TP_CD AS type_id, bp.BENEFIT_CD AS `key`, bp.BENEFIT_NM AS name,
                  bp.BENEFIT_AMT AS val, bp.BENEFIT_CTGR_CD AS cat, bp.BADGE_CD AS badge,
                  bp.DEFAULT_CHECKED_YN AS checked
           FROM TBENEFIT_PRESET bp
           JOIN TCOMPANY_TYPE ct ON ct.COMP_TP_ID = bp.COMP_TP_ID
           ORDER BY bp.SORT_ORDER_NO"""
    )
    ben_presets = {}
    for r in preset_rows:
        tid = r.pop("type_id")
        r["checked"] = bool(r["checked"])
        ben_presets.setdefault(tid, []).append(r)

    # Companies — single query (type code via JOIN)
    companies = await database.fetch_all(
        """SELECT c.COMP_ID AS id, c.COMP_NM AS name, ct.COMP_TP_CD AS type,
                  c.INDUSTRY_NM AS industry, c.LOGO_NM AS logo, c.WORK_STYLE_VAL AS work_style
           FROM TCOMPANY c JOIN TCOMPANY_TYPE ct ON ct.COMP_TP_ID = c.COMP_TP_ID"""
    )
    for c in companies:
        if isinstance(c.get("work_style"), str):
            c["work_style"] = json.loads(c["work_style"])

    # Aliases — batch
    all_aliases = await database.fetch_all(
        "SELECT COMP_ID AS company_id, ALIAS_NM AS alias FROM TCOMPANY_ALIAS"
    )
    alias_map = {}
    for a in all_aliases:
        alias_map.setdefault(a["company_id"], []).append(a["alias"])

    # Benefits — batch
    all_bens = await database.fetch_all(
        """SELECT COMP_ID AS company_id, BENEFIT_CD AS `key`, BENEFIT_NM AS name,
                  BENEFIT_AMT AS val, BENEFIT_CTGR_CD AS cat, BADGE_CD AS badge,
                  NOTE_CTNT AS note, QUAL_YN AS qual, QUAL_DESC_CTNT AS qualText
           FROM TCOMPANY_BENEFIT ORDER BY SORT_ORDER_NO"""
    )
    ben_map = {}
    for b in all_bens:
        cid = b.pop("company_id")
        b["qual"] = bool(b["qual"])
        ben_map.setdefault(cid, []).append(b)

    for c in companies:
        c["aliases"] = alias_map.get(c["id"], [])
        c["benefits"] = ben_map.get(c["id"], [])

    # Profiles — single query
    profiles = await database.fetch_all(
        """SELECT PROFILE_ID AS pk_id, PROFILE_CD AS id, PROFILE_NM AS type_name,
                  PROFILE_DESC_CTNT AS description, MAP_PRIORITY_CD AS map_priority, VEC_VAL AS vec
           FROM TPROFILE"""
    )
    for p in profiles:
        if isinstance(p.get("vec"), str):
            p["vec"] = json.loads(p["vec"])

    # Profile job fits — batch (PROFILE_ID INT 키)
    all_fits = await database.fetch_all(
        """SELECT PROFILE_ID AS profile_id, SCENARIO_CD AS scenario,
                  FIT_CTNT AS fit, CAUTION_CTNT AS caution
           FROM TPROFILE_JOB_FIT"""
    )
    fit_map = {}
    for f in all_fits:
        fit_map.setdefault(f["profile_id"], {})[f["scenario"]] = {"fit": f["fit"], "caution": f["caution"]}
    for p in profiles:
        p["jobFit"] = fit_map.get(p["pk_id"], {})

    # Job groups + jobs — batch
    groups = await database.fetch_all(
        """SELECT JOB_GROUP_ID AS id, JOB_GROUP_NM AS group_label, COLOR_CD AS color, SORT_ORDER_NO AS sort_order
           FROM TJOB_GROUP ORDER BY SORT_ORDER_NO"""
    )
    all_jobs = await database.fetch_all(
        """SELECT JOB_CD AS id, JOB_GROUP_ID AS group_id, JOB_NM AS label, ICON_NM AS icon, SCENARIO_CD AS scenario
           FROM TJOB ORDER BY SORT_ORDER_NO"""
    )
    job_map = {}
    for j in all_jobs:
        gid = j.pop("group_id")
        job_map.setdefault(gid, []).append(j)
    for g in groups:
        g["jobs"] = job_map.get(g["id"], [])

    # Profiler questions — single query
    questions = await database.fetch_all(
        """SELECT QUESTION_ID AS pk_id, QUESTION_NO AS id, QUESTION_LABEL_NM AS label,
                  OPTION_A_TITLE_NM AS option_a_title, OPTION_A_FX_VAL AS option_a_fx,
                  OPTION_B_TITLE_NM AS option_b_title, OPTION_B_FX_VAL AS option_b_fx
           FROM TPROFILER_QUESTION ORDER BY QUESTION_NO"""
    )
    for q in questions:
        if isinstance(q.get("option_a_fx"), str):
            q["option_a_fx"] = json.loads(q["option_a_fx"])
        if isinstance(q.get("option_b_fx"), str):
            q["option_b_fx"] = json.loads(q["option_b_fx"])

    # Question scenario descriptions — single query
    q_desc_rows = await database.fetch_all(
        """SELECT SCENARIO_CD AS scenario, DESC_A_CTNT AS desc_a, DESC_B_CTNT AS desc_b, QUESTION_ID AS question_id
           FROM TQUESTION_SCENARIO ORDER BY QUESTION_ID"""
    )
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
