import json
from fastapi import APIRouter, Depends, Query
import database
from middleware.auth_middleware import get_current_user
from models.profiler import ProfilerResultReq

router = APIRouter()

@router.get("/jobs")
async def get_jobs():
    groups = await database.fetch_all(
        "SELECT JOB_GROUP_ID AS id, JOB_GROUP_NM AS group_label, COLOR_CD AS color, SORT_ORDER_NO AS sort_order "
        "FROM TJOB_GROUP ORDER BY SORT_ORDER_NO"
    )
    result = []
    for g in groups:
        jobs = await database.fetch_all(
            "SELECT JOB_CD AS id, JOB_NM AS label, ICON_NM AS icon, SCENARIO_CD AS scenario "
            "FROM TJOB WHERE JOB_GROUP_ID=%s ORDER BY SORT_ORDER_NO",
            (g["id"],),
        )
        result.append({"groupLabel": g["group_label"], "color": g["color"], "jobs": jobs})
    return result

@router.get("/questions")
async def get_questions(scenario: str = Query("tech")):
    questions = await database.fetch_all(
        """SELECT QUESTION_ID AS pk_id, QUESTION_NO AS id, QUESTION_LABEL_NM AS label,
                  OPTION_A_TITLE_NM AS option_a_title, OPTION_A_FX_VAL AS option_a_fx,
                  OPTION_B_TITLE_NM AS option_b_title, OPTION_B_FX_VAL AS option_b_fx
           FROM TPROFILER_QUESTION ORDER BY QUESTION_NO"""
    )
    descs = await database.fetch_all(
        "SELECT QUESTION_ID AS question_id, DESC_A_CTNT AS desc_a, DESC_B_CTNT AS desc_b "
        "FROM TQUESTION_SCENARIO WHERE SCENARIO_CD=%s ORDER BY QUESTION_ID",
        (scenario,),
    )
    desc_map = {d["question_id"]: d for d in descs}
    result = []
    for q in questions:
        a_fx = json.loads(q["option_a_fx"]) if isinstance(q["option_a_fx"], str) else q["option_a_fx"]
        b_fx = json.loads(q["option_b_fx"]) if isinstance(q["option_b_fx"], str) else q["option_b_fx"]
        d = desc_map.get(q["pk_id"], {})
        result.append({
            "id": q["id"], "label": q["label"],
            "a": {"title": q["option_a_title"], "fx": a_fx, "desc": d.get("desc_a", "")},
            "b": {"title": q["option_b_title"], "fx": b_fx, "desc": d.get("desc_b", "")},
        })
    return result

@router.get("/profiles")
async def get_profiles():
    profiles = await database.fetch_all(
        """SELECT PROFILE_ID AS pk_id, PROFILE_CD AS id, PROFILE_NM AS type_name,
                  PROFILE_DESC_CTNT AS description, MAP_PRIORITY_CD AS map_priority, VEC_VAL AS vec
           FROM TPROFILE"""
    )
    result = []
    for p in profiles:
        vec = json.loads(p["vec"]) if isinstance(p["vec"], str) else p["vec"]
        fits = await database.fetch_all(
            "SELECT SCENARIO_CD AS scenario, FIT_CTNT AS fit, CAUTION_CTNT AS caution "
            "FROM TPROFILE_JOB_FIT WHERE PROFILE_ID=%s",
            (p["pk_id"],),
        )
        job_fit = {f["scenario"]: {"fit": f["fit"], "caution": f["caution"]} for f in fits}
        result.append({
            "id": p["id"], "type": p["type_name"], "desc": p["description"],
            "mapPri": p["map_priority"], "vec": vec, "jobFit": job_fit,
        })
    return result

@router.post("/results")
async def save_result(req: ProfilerResultReq, user_id: int = Depends(get_current_user)):
    import json as j
    # Resolve JOB_CD / PROFILE_CD 코드값을 INT FK로 변환
    job_fk = None
    if req.job_id:
        jr = await database.fetch_one("SELECT JOB_ID AS id FROM TJOB WHERE JOB_CD=%s", (req.job_id,))
        job_fk = jr["id"] if jr else None
    pr = await database.fetch_one("SELECT PROFILE_ID AS id FROM TPROFILE WHERE PROFILE_CD=%s", (req.profile_id,))
    profile_fk = pr["id"] if pr else None
    rid = await database.execute(
        """INSERT INTO TPROFILER_RESULT (MBR_ID, JOB_ID, SCORES_VAL, PROFILE_ID, SIMILARITY_VAL, ANSWERS_VAL)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (user_id, job_fk, j.dumps(req.scores), profile_fk, req.similarity, j.dumps(req.answers)),
    )
    return {"id": rid}
