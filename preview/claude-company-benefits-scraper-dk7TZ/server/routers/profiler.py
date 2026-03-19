import json
from fastapi import APIRouter, Depends, Query
import database
from middleware.auth_middleware import get_current_user
from models.profiler import ProfilerResultReq

router = APIRouter()

@router.get("/jobs")
async def get_jobs():
    groups = await database.fetch_all("SELECT * FROM job_groups ORDER BY sort_order")
    result = []
    for g in groups:
        jobs = await database.fetch_all(
            "SELECT id, label, icon, scenario FROM jobs WHERE group_id=%s ORDER BY sort_order",
            (g["id"],),
        )
        result.append({"groupLabel": g["group_label"], "color": g["color"], "jobs": jobs})
    return result

@router.get("/questions")
async def get_questions(scenario: str = Query("tech")):
    questions = await database.fetch_all("SELECT * FROM profiler_questions ORDER BY id")
    descs = await database.fetch_all(
        "SELECT question_id, desc_a, desc_b FROM question_scenarios WHERE scenario=%s ORDER BY question_id",
        (scenario,),
    )
    desc_map = {d["question_id"]: d for d in descs}
    result = []
    for q in questions:
        a_fx = json.loads(q["option_a_fx"]) if isinstance(q["option_a_fx"], str) else q["option_a_fx"]
        b_fx = json.loads(q["option_b_fx"]) if isinstance(q["option_b_fx"], str) else q["option_b_fx"]
        d = desc_map.get(q["id"], {})
        result.append({
            "id": q["id"], "label": q["label"],
            "a": {"title": q["option_a_title"], "fx": a_fx, "desc": d.get("desc_a", "")},
            "b": {"title": q["option_b_title"], "fx": b_fx, "desc": d.get("desc_b", "")},
        })
    return result

@router.get("/profiles")
async def get_profiles():
    profiles = await database.fetch_all("SELECT * FROM profiles")
    result = []
    for p in profiles:
        vec = json.loads(p["vec"]) if isinstance(p["vec"], str) else p["vec"]
        fits = await database.fetch_all(
            "SELECT scenario, fit, caution FROM profile_job_fits WHERE profile_id=%s", (p["id"],)
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
    rid = await database.execute(
        """INSERT INTO profiler_results (user_id, job_id, scores, profile_id, similarity, answers)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (user_id, req.job_id, j.dumps(req.scores), req.profile_id, req.similarity, j.dumps(req.answers)),
    )
    return {"id": rid}
