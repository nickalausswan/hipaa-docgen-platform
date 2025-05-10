from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

class PatientData(BaseModel):
    name: str
    age: int
    weight_kg: float
    creatinine: float
    admitting_diagnosis: str
    diagnosis_codes: List[str]
    prior_notes: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "API is working!"}

@app.post("/generate-note/")
async def generate_note(data: PatientData):
    note = f"{data.name} (age {data.age}) is admitted for {data.admitting_diagnosis}."
    return {"note": note}

@app.post("/dvt-risk/")
async def dvt_risk(data: PatientData):
    crcl = ((140 - data.age) * data.weight_kg) / (72 * data.creatinine)
    recommendation = "Use Heparin" if crcl < 30 else "Use Lovenox"
    return {
        "creatinine_clearance": round(crcl, 1),
        "recommendation": recommendation
    }

@app.post("/consult-message/")
async def consult_message(data: PatientData):
    message = (
        f"Hello, may I please consult you on {data.name} who is being admitted for "
        f"{data.admitting_diagnosis} for assistance with..."
    )
    return {"message": message}
