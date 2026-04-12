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
    company_types = await database.fetch_all(
        """SELECT COMP_TP_CD AS comp_tp_cd, COMP_TP_NM AS comp_tp_nm,
                  GROWTH_RATE_VAL AS growth_rate_val, GROWTH_LABEL_NM AS growth_label_nm,
                  STABILITY_SCORE_NO AS stability_score_no
           FROM TCOMPANY_TYPE"""
    )

    # Benefit presets grouped by company type code
    preset_rows = await database.fetch_all(
        """SELECT ct.COMP_TP_CD AS comp_tp_cd,
                  bp.BENEFIT_CD AS benefit_cd, bp.BENEFIT_NM AS benefit_nm,
                  bp.BENEFIT_AMT AS benefit_amt, bp.BENEFIT_CTGR_CD AS benefit_ctgr_cd,
                  bp.BADGE_CD AS badge_cd, bp.DEFAULT_CHECKED_YN AS default_checked_yn
           FROM TBENEFIT_PRESET bp
           JOIN TCOMPANY_TYPE ct ON ct.COMP_TP_ID = bp.COMP_TP_ID
           ORDER BY bp.SORT_ORDER_NO"""
    )
    benefit_presets = {}
    for r in preset_rows:
        tp_cd = r.pop("comp_tp_cd")
        r["default_checked_yn"] = bool(r["default_checked_yn"])
        benefit_presets.setdefault(tp_cd, []).append(r)

    # Companies — single query (type code via JOIN)
    companies = await database.fetch_all(
        """SELECT c.COMP_ID AS comp_id, c.COMP_NM AS comp_nm,
                  ct.COMP_TP_CD AS comp_tp_cd,
                  c.INDUSTRY_NM AS industry_nm, c.LOGO_NM AS logo_nm,
                  c.WORK_STYLE_VAL AS work_style_val
           FROM TCOMPANY c JOIN TCOMPANY_TYPE ct ON ct.COMP_TP_ID = c.COMP_TP_ID"""
    )
    for c in companies:
        if isinstance(c.get("work_style_val"), str):
            c["work_style_val"] = json.loads(c["work_style_val"])

    # Aliases — batch
    all_aliases = await database.fetch_all(
        "SELECT COMP_ID AS comp_id, ALIAS_NM AS alias_nm FROM TCOMPANY_ALIAS"
    )
    alias_map = {}
    for a in all_aliases:
        alias_map.setdefault(a["comp_id"], []).append(a["alias_nm"])

    # Benefits — batch
    all_bens = await database.fetch_all(
        """SELECT COMP_ID AS comp_id, BENEFIT_CD AS benefit_cd, BENEFIT_NM AS benefit_nm,
                  BENEFIT_AMT AS benefit_amt, BENEFIT_CTGR_CD AS benefit_ctgr_cd,
                  BADGE_CD AS badge_cd, NOTE_CTNT AS note_ctnt,
                  QUAL_YN AS qual_yn, QUAL_DESC_CTNT AS qual_desc_ctnt
           FROM TCOMPANY_BENEFIT ORDER BY SORT_ORDER_NO"""
    )
    ben_map = {}
    for b in all_bens:
        comp_id = b.pop("comp_id")
        b["qual_yn"] = bool(b["qual_yn"])
        ben_map.setdefault(comp_id, []).append(b)

    for c in companies:
        c["aliases"] = alias_map.get(c["comp_id"], [])
        c["benefits"] = ben_map.get(c["comp_id"], [])

    # Profiles — single query
    profiles = await database.fetch_all(
        """SELECT PROFILE_ID AS profile_id, PROFILE_CD AS profile_cd, PROFILE_NM AS profile_nm,
                  PROFILE_DESC_CTNT AS profile_desc_ctnt, MAP_PRIORITY_CD AS map_priority_cd,
                  VEC_VAL AS vec_val
           FROM TPROFILE"""
    )
    for p in profiles:
        if isinstance(p.get("vec_val"), str):
            p["vec_val"] = json.loads(p["vec_val"])

    # Profile job fits — batch
    all_fits = await database.fetch_all(
        """SELECT PROFILE_ID AS profile_id, SCENARIO_CD AS scenario_cd,
                  FIT_CTNT AS fit_ctnt, CAUTION_CTNT AS caution_ctnt
           FROM TPROFILE_JOB_FIT"""
    )
    fit_map = {}
    for f in all_fits:
        fit_map.setdefault(f["profile_id"], {})[f["scenario_cd"]] = {
            "fit_ctnt": f["fit_ctnt"], "caution_ctnt": f["caution_ctnt"]
        }
    profiles_out = []
    for p in profiles:
        profiles_out.append({
            "profile_cd": p["profile_cd"],
            "profile_nm": p["profile_nm"],
            "profile_desc_ctnt": p["profile_desc_ctnt"],
            "map_priority_cd": p["map_priority_cd"],
            "vec_val": p["vec_val"],
            "profile_job_fits": fit_map.get(p["profile_id"], {}),
        })

    # Job groups + jobs — batch
    groups = await database.fetch_all(
        """SELECT JOB_GROUP_ID AS job_group_id, JOB_GROUP_NM AS job_group_nm,
                  COLOR_CD AS color_cd, SORT_ORDER_NO AS sort_order_no
           FROM TJOB_GROUP ORDER BY SORT_ORDER_NO"""
    )
    all_jobs = await database.fetch_all(
        """SELECT JOB_CD AS job_cd, JOB_GROUP_ID AS job_group_id, JOB_NM AS job_nm,
                  ICON_NM AS icon_nm, SCENARIO_CD AS scenario_cd
           FROM TJOB ORDER BY SORT_ORDER_NO"""
    )
    job_map = {}
    for j in all_jobs:
        gid = j.pop("job_group_id")
        job_map.setdefault(gid, []).append(j)
    job_groups = []
    for g in groups:
        job_groups.append({
            "job_group_nm": g["job_group_nm"],
            "color_cd": g["color_cd"],
            "jobs": job_map.get(g["job_group_id"], []),
        })

    # Profiler questions — single query
    questions = await database.fetch_all(
        """SELECT QUESTION_ID AS question_id, QUESTION_NO AS question_no,
                  QUESTION_LABEL_NM AS question_label_nm,
                  OPTION_A_TITLE_NM AS option_a_title_nm, OPTION_A_FX_VAL AS option_a_fx_val,
                  OPTION_B_TITLE_NM AS option_b_title_nm, OPTION_B_FX_VAL AS option_b_fx_val
           FROM TPROFILER_QUESTION ORDER BY QUESTION_NO"""
    )
    for q in questions:
        if isinstance(q.get("option_a_fx_val"), str):
            q["option_a_fx_val"] = json.loads(q["option_a_fx_val"])
        if isinstance(q.get("option_b_fx_val"), str):
            q["option_b_fx_val"] = json.loads(q["option_b_fx_val"])

    questions_out = [{
        "question_no": q["question_no"],
        "question_label_nm": q["question_label_nm"],
        "option_a": {"option_a_title_nm": q["option_a_title_nm"], "option_a_fx_val": q["option_a_fx_val"]},
        "option_b": {"option_b_title_nm": q["option_b_title_nm"], "option_b_fx_val": q["option_b_fx_val"]},
    } for q in questions]

    # Question scenario descriptions — single query
    q_desc_rows = await database.fetch_all(
        """SELECT SCENARIO_CD AS scenario_cd, DESC_A_CTNT AS desc_a_ctnt,
                  DESC_B_CTNT AS desc_b_ctnt, QUESTION_ID AS question_id
           FROM TQUESTION_SCENARIO ORDER BY QUESTION_ID"""
    )
    question_descs = {}
    for r in q_desc_rows:
        question_descs.setdefault(r["scenario_cd"], []).append({
            "desc_a_ctnt": r["desc_a_ctnt"],
            "desc_b_ctnt": r["desc_b_ctnt"],
        })

    data = {
        "company_types": company_types,
        "benefit_presets": benefit_presets,
        "companies": companies,
        "profiles": profiles_out,
        "job_groups": job_groups,
        "questions": questions_out,
        "question_descs": question_descs,
    }

    cache.set("reference_all", data)
    return JSONResponse(content=data, headers={"Cache-Control": "public, max-age=3600"})
