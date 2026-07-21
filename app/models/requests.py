from pydantic import BaseModel, Field
from typing import List, Optional

class PatientRenal(BaseModel):
    egfr: Optional[float] = None
    stage: Optional[str] = None

class PatientHepatic(BaseModel):
    impairment: Optional[str] = None

class PatientContext(BaseModel):
    age: Optional[int] = None
    sex: Optional[str] = None
    conditions: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    pregnancy_status: Optional[str] = "not_applicable"
    renal: Optional[PatientRenal] = None
    hepatic: Optional[PatientHepatic] = None

class QueryRequest(BaseModel):
    question: str
    patient_context: Optional[PatientContext] = None
    jurisdiction: Optional[str] = "US"
    audience: Optional[str] = "clinician"

class FeedbackRequest(BaseModel):
    query_id: str
    rating: str  # "helpful" or "unhelpful"
    citation_quality: Optional[str] = None  # "correct", "hallucination", "missing"
    comment: Optional[str] = None
