from pydantic import BaseModel

class Job(BaseModel):
    id: str
    label: str
    icon: str
    scenario: str

class JobGroup(BaseModel):
    groupLabel: str
    color: str
    jobs: list[Job]

class Profile(BaseModel):
    id: str
    type: str
    desc: str
    mapPri: str
    vec: dict
    jobFit: dict

class ProfilerResultReq(BaseModel):
    job_id: str | None = None
    scores: dict
    profile_id: str
    similarity: float
    answers: list[dict]
