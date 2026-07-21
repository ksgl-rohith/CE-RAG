from pydantic import BaseModel, Field
from typing import List, Optional

class DrugInformation(BaseModel):
    generic_name: Optional[str] = None
    brand_names: List[str] = Field(default_factory=list)
    drug_class: Optional[str] = None
    active_ingredients: List[str] = Field(default_factory=list)
    mechanism: Optional[str] = None

class Indications(BaseModel):
    approved: List[str] = Field(default_factory=list)
    off_label_with_evidence: List[str] = Field(default_factory=list)

class PatientConsiderations(BaseModel):
    age: List[str] = Field(default_factory=list)
    pregnancy: List[str] = Field(default_factory=list)
    renal: List[str] = Field(default_factory=list)
    hepatic: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    comorbidities: List[str] = Field(default_factory=list)

class SideEffects(BaseModel):
    common: List[str] = Field(default_factory=list)
    serious: List[str] = Field(default_factory=list)

class Alternatives(BaseModel):
    generic_equivalents: List[str] = Field(default_factory=list)
    same_class: List[str] = Field(default_factory=list)
    other_guideline_supported_options: List[str] = Field(default_factory=list)

class TreatmentTimeline(BaseModel):
    expected_onset: Optional[str] = None
    reassessment_period: Optional[str] = None
    typical_duration: Optional[str] = None
    limitations: Optional[str] = None

class EvidenceIndicators(BaseModel):
    evidence_quality: str = "low"
    population_match: str = "low"
    source_agreement: str = "low"
    answer_completeness: str = "low"

class Citation(BaseModel):
    claim_id: str
    claim_text: str
    supporting_chunk_id: Optional[str] = None
    source_document_id: Optional[str] = None
    source_passage: Optional[str] = None
    chunk_index: Optional[int] = None
    citation_url: Optional[str] = None
    entailment_status: Optional[str] = None
    verification_score: Optional[float] = None

class QueryResponse(BaseModel):
    query_id: str
    question: str
    summary: str = "No summary provided."
    drug_information: DrugInformation = DrugInformation()
    indications: Indications = Indications()
    patient_considerations: PatientConsiderations = PatientConsiderations()
    contraindications: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    side_effects: SideEffects = SideEffects()
    interactions: List[str] = Field(default_factory=list)
    alternatives: Alternatives = Alternatives()
    treatment_timeline: TreatmentTimeline = TreatmentTimeline()
    monitoring: List[str] = Field(default_factory=list)
    evidence_indicators: EvidenceIndicators = EvidenceIndicators()
    limitations: List[str] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
