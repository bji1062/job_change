import json
from fastapi import APIRouter, Depends, Query
import database
from middleware.auth_middleware import get_current_user
from models.profiler import ProfilerResultReq

router = APIRouter()

@router.get("/jobs")
async def get_jobs():
    groups = await database.fetch_all(
        """SELECT JOB_GROUP_ID AS job_group_id, JOB_GROUP_NM AS job_group_nm,
                  COLOR_CD AS color_cd, SORT_ORDER_NO AS sort_order_no
           FROM TJOB_GROUP ORDER BY SORT_ORDER_NO"""
    )
    result = []
    for g in groups:
        jobs = await database.fetch_all(
            """SELECT JOB_CD AS job_cd, JOB_NM AS job_nm, ICON_NM AS icon_nm, SCENARIO_CD AS scenario_cd
               FROM TJOB WHERE JOB_GROUP_ID=%s ORDER BY SORT_ORDER_NO""",
            (g["job_group_id"],),
        )
        result.append({"job_group_nm": g["job_group_nm"], "color_cd": g["color_cd"], "jobs": jobs})
    return result

@router.get("/questions")
async def get_questions(scenario_cd: str = Query("tech")):
    questions = await database.fetch_all(
        """SELECT QUESTION_ID AS question_id, QUESTION_NO AS question_no,
                  QUESTION_LABEL_NM AS question_label_nm,
                  OPTION_A_TITLE_NM AS option_a_title_nm, OPTION_A_FX_VAL AS option_a_fx_val,
                  OPTION_B_TITLE_NM AS option_b_title_nm, OPTION_B_FX_VAL AS option_b_fx_val
           FROM TPROFILER_QUESTION ORDER BY QUESTION_NO"""
    )
    descs = await database.fetch_all(
        """SELECT QUESTION_ID AS question_id, DESC_A_CTNT AS desc_a_ctnt, DESC_B_CTNT AS desc_b_ctnt
           FROM TQUESTION_SCENARIO WHERE SCENARIO_CD=%s ORDER BY QUESTION_ID""",
        (scenario_cd,),
    )
    desc_map = {d["question_id"]: d for d in descs}
    result = []
    for q in questions:
        a_fx = json.loads(q["option_a_fx_val"]) if isinstance(q["option_a_fx_val"], str) else q["option_a_fx_val"]
        b_fx = json.loads(q["option_b_fx_val"]) if isinstance(q["option_b_fx_val"], str) else q["option_b_fx_val"]
        d = desc_map.get(q["question_id"], {})
        result.append({
            "question_no": q["question_no"],
            "question_label_nm": q["question_label_nm"],
            "option_a": {
                "option_a_title_nm": q["option_a_title_nm"],
                "option_a_fx_val": a_fx,
                "desc_a_ctnt": d.get("desc_a_ctnt", ""),
            },
            "option_b": {
                "option_b_title_nm": q["option_b_title_nm"],
                "option_b_fx_val": b_fx,
                "desc_b_ctnt": d.get("desc_b_ctnt", ""),
            },
        })
    return result

@router.get("/profiles")
async def get_profiles():
    profiles = await database.fetch_all(
        """SELECT PROFILE_ID AS profile_id, PROFILE_CD AS profile_cd, PROFILE_NM AS profile_nm,
                  PROFILE_DESC_CTNT AS profile_desc_ctnt, MAP_PRIORITY_CD AS map_priority_cd,
                  VEC_VAL AS vec_val
           FROM TPROFILE"""
    )
    result = []
    for p in profiles:
        vec = json.loads(p["vec_val"]) if isinstance(p["vec_val"], str) else p["vec_val"]
        fits = await database.fetch_all(
            """SELECT SCENARIO_CD AS scenario_cd, FIT_CTNT AS fit_ctnt, CAUTION_CTNT AS caution_ctnt
               FROM TPROFILE_JOB_FIT WHERE PROFILE_ID=%s""",
            (p["profile_id"],),
        )
        profile_job_fits = {f["scenario_cd"]: {"fit_ctnt": f["fit_ctnt"], "caution_ctnt": f["caution_ctnt"]} for f in fits}
        result.append({
            "profile_cd": p["profile_cd"],
            "profile_nm": p["profile_nm"],
            "profile_desc_ctnt": p["profile_desc_ctnt"],
            "map_priority_cd": p["map_priority_cd"],
            "vec_val": vec,
            "profile_job_fits": profile_job_fits,
        })
    return result

@router.post("/results")
async def save_result(req: ProfilerResultReq, mbr_id: int = Depends(get_current_user)):
    import json as j
    # Resolve JOB_CD / PROFILE_CD 코드값을 INT FK로 변환
    job_fk = None
    if req.job_cd:
        jr = await database.fetch_one("SELECT JOB_ID AS job_id FROM TJOB WHERE JOB_CD=%s", (req.job_cd,))
        job_fk = jr["job_id"] if jr else None
    pr = await database.fetch_one("SELECT PROFILE_ID AS profile_id FROM TPROFILE WHERE PROFILE_CD=%s", (req.profile_cd,))
    profile_fk = pr["profile_id"] if pr else None
    result_id = await database.execute(
        """INSERT INTO TPROFILER_RESULT (MBR_ID, JOB_ID, SCORES_VAL, PROFILE_ID, SIMILARITY_VAL, ANSWERS_VAL)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (mbr_id, job_fk, j.dumps(req.scores_val), profile_fk, req.similarity_val, j.dumps(req.answers_val)),
    )
    return {"result_id": result_id}
