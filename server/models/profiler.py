from pydantic import BaseModel

class Job(BaseModel):
    job_cd: str
    job_nm: str
    icon_nm: str
    scenario_cd: str

class JobGroup(BaseModel):
    job_group_nm: str
    color_cd: str
    jobs: list[Job]

class Profile(BaseModel):
    profile_cd: str
    profile_nm: str
    profile_desc_ctnt: str
    map_priority_cd: str
    vec_val: dict
    profile_job_fits: dict

class ProfilerResultReq(BaseModel):
    job_cd: str | None = None
    scores_val: dict
    profile_cd: str
    similarity_val: float
    answers_val: list[dict]
