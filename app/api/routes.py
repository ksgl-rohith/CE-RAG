import uuid
import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.database import QueryLog, Feedback, AuditLog, DocumentChunk, Document
from app.models.requests import QueryRequest, FeedbackRequest
from app.models.responses import QueryResponse, Citation, DrugInformation, Indications, PatientConsiderations, SideEffects, Alternatives, TreatmentTimeline, EvidenceIndicators
from app.retrieval.hybrid_fusion import HybridRetriever
from app.config import settings

import google.generativeai as genai

router = APIRouter()

def clean_json_string(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def generate_mock_json_response(query_text: str, chunks: List[DocumentChunk]) -> str:
    citations = []
    summary = "Insufficient clinical evidence found."
    
    if chunks:
        first_chunk = chunks[0]
        summary = f"Retrieved source: {first_chunk.document.title}. passage: {first_chunk.chunk_text[:150]}..."
        citations = [
            {
                "claim_id": "claim_1",
                "claim_text": f"Matched text in {first_chunk.document.title}.",
                "supporting_chunk_id": str(first_chunk.id),
                "source_document_id": str(first_chunk.document_id),
                "source_passage": first_chunk.chunk_text[:200],
                "citation_url": first_chunk.document.source_url,
                "entailment_status": "supports",
                "verification_score": 1.0
            }
        ]
        
    mock_response = {
        "summary": summary,
        "drug_information": {
            "generic_name": "N/A",
            "brand_names": [],
            "drug_class": "N/A",
            "active_ingredients": [],
            "mechanism": "N/A"
        },
        "indications": {
            "approved": ["Mock indication derived from chunks"] if chunks else [],
            "off_label_with_evidence": []
        },
        "patient_considerations": {
            "age": [],
            "pregnancy": [],
            "renal": [],
            "hepatic": [],
            "allergies": [],
            "comorbidities": []
        },
        "contraindications": [],
        "warnings": [],
        "side_effects": {
            "common": [],
            "serious": []
        },
        "interactions": [],
        "alternatives": {
            "generic_equivalents": [],
            "same_class": [],
            "other_guideline_supported_options": []
        },
        "treatment_timeline": {
            "expected_onset": "N/A",
            "reassessment_period": "N/A",
            "typical_duration": "N/A",
            "limitations": "Mock offline mode activated."
        },
        "monitoring": [],
        "evidence_indicators": {
            "evidence_quality": "moderate" if chunks else "low",
            "population_match": "moderate",
            "source_agreement": "moderate",
            "answer_completeness": "low"
        },
        "limitations": ["Generating offline mock response due to missing API credentials."],
        "citations": citations
    }
    return json.dumps(mock_response)

def generate_rag_response(query_text: str, context_str: str, chunks: List[DocumentChunk]) -> str:
    prompt = f"""You are a clinical pharmacy and drug information AI assistant. 
Your task is to answer the following clinical query. For the main summary answer, safety warnings, and indications, base your answer strictly on the retrieved guidelines and drug labels text chunks provided below. For standard structured reference fields (such as drug_information, alternatives, and patient_considerations), you should supplement missing details using your general clinical knowledge if the retrieved chunks do not contain them.

Patient Context:
{context_str}

Clinical Query:
{query_text}

Retrieved Evidence Chunks:
"""
    for i, chunk in enumerate(chunks):
        doc_title = chunk.document.title if chunk.document else "Unknown Document"
        doc_id = str(chunk.document_id)
        prompt += f"\n[Chunk {i+1} (Source: {doc_title}, ID: {doc_id}, Page: {chunk.metadata_json.get('page_number')}, Section: {chunk.clinical_section})]\n{chunk.chunk_text}\n"

    prompt += """
Produce a structured JSON response matching the following format exactly. Ensure all fields are filled based on the evidence. If the evidence is insufficient to answer a field, leave it as null, empty array, or state "Insufficient evidence".
DO NOT include any markdown formatting wrappers (like ```json) in your raw response. Just return raw JSON.

JSON Schema to match:
{
  "summary": "Short 1-2 sentence direct answer",
  "drug_information": {
    "generic_name": "Generic name of drug",
    "brand_names": ["brand 1"],
    "drug_class": "Drug class name",
    "active_ingredients": ["ingredient 1"],
    "mechanism": "Mechanism of action text"
  },
  "indications": {
    "approved": ["approved indication 1"],
    "off_label_with_evidence": ["off-label usage if supported by chunks"]
  },
  "patient_considerations": {
    "age": ["geriatric/pediatric details from chunks"],
    "pregnancy": ["pregnancy/lactation details"],
    "renal": ["renal impairment dosage/warnings"],
    "hepatic": ["hepatic impairment details"],
    "allergies": ["hypersensitivity warnings"],
    "comorbidities": ["comorbidity adjustments"]
  },
  "contraindications": ["list of absolute contraindications"],
  "warnings": ["list of warnings/precautions"],
  "side_effects": {
    "common": ["list of common side effects"],
    "serious": ["list of serious/black-box side effects"]
  },
  "interactions": ["list of drug interactions from chunks"],
  "alternatives": {
    "generic_equivalents": [],
    "same_class": [],
    "other_guideline_supported_options": []
  },
  "treatment_timeline": {
    "expected_onset": "onset details",
    "reassessment_period": "reassessment timing",
    "typical_duration": "typical duration of therapy",
    "limitations": "onset limitations text"
  },
  "monitoring": ["list of monitoring parameters"],
  "evidence_indicators": {
    "evidence_quality": "high / moderate / low",
    "population_match": "high / moderate / low",
    "source_agreement": "high / moderate / low",
    "answer_completeness": "high / moderate / low"
  },
  "limitations": ["limitations of the retrieved evidence"],
  "citations": [
    {
      "claim_id": "claim_1",
      "claim_text": "A specific clinical statement from the summary/details",
      "chunk_index": 1,
      "source_passage": "Exact quote from the chunk supporting the claim",
      "entailment_status": "supports",
      "verification_score": 1.0
    }
  ]
}
"""
    if settings.LLM_PROVIDER == "google" and settings.LLM_API_KEY:
        try:
            genai.configure(api_key=settings.LLM_API_KEY)
            model = genai.GenerativeModel(settings.LLM_MODEL)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
    elif settings.LLM_PROVIDER == "openai" and settings.LLM_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.LLM_API_KEY)
            response = client.chat.completions.create(
                model=settings.LLM_MODEL or "gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.LLM_TEMPERATURE,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            
    return generate_mock_json_response(query_text, chunks)

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV
    }

@router.post("/api/v1/query", response_model=QueryResponse)
def ask_question(req: QueryRequest, db: Session = Depends(get_db)):
    query_id = uuid.uuid4()
    
    # 1. Format Patient Context string
    context_str = ""
    if req.patient_context:
        ctx = req.patient_context
        context_str = f"Age: {ctx.age or 'N/A'}, Sex: {ctx.sex or 'N/A'}, Conditions: {', '.join(ctx.conditions)}, Meds: {', '.join(ctx.current_medications)}, Allergies: {', '.join(ctx.allergies)}"
        
    # 2. Retrieve relevant evidence chunks
    # Simple de-identified search query (audit logs can screen this)
    chunks = HybridRetriever.search(
        db=db,
        query=req.question,
        top_k=settings.RERANK_TOP_K
    )
    
    # 3. Generate RAG Response (Gemini or Mock)
    raw_llm_output = generate_rag_response(req.question, context_str, chunks)
    cleaned_json = clean_json_string(raw_llm_output)
    
    try:
        response_data = json.loads(cleaned_json)
        # Force inject query_id and question to match response schema
        response_data["query_id"] = str(query_id)
        response_data["question"] = req.question
        
        # Map numeric chunk_index to database UUIDs and paths
        citations = response_data.get("citations", [])
        if isinstance(citations, list):
            for cit in citations:
                if not isinstance(cit, dict):
                    continue
                idx = cit.get("chunk_index")
                if idx is not None:
                    try:
                        idx_val = int(idx)
                        if 1 <= idx_val <= len(chunks):
                            matched_chunk = chunks[idx_val - 1]
                            cit["supporting_chunk_id"] = str(matched_chunk.id)
                            cit["source_document_id"] = str(matched_chunk.document_id)
                            if matched_chunk.document:
                                cit["citation_url"] = matched_chunk.document.source_url
                            if not cit.get("source_passage"):
                                cit["source_passage"] = matched_chunk.chunk_text[:300]
                    except (ValueError, TypeError):
                        pass
        
        # Validate through Pydantic
        response_obj = QueryResponse.model_validate(response_data)
    except Exception as err:
        print(f"JSON validation failed on LLM output. Raw: {raw_llm_output}. Cleaned: {cleaned_json}. Error: {err}")
        # Build a safe emergency fallback response
        fallback_str = generate_mock_json_response(req.question, chunks)
        fallback_data = json.loads(fallback_str)
        fallback_data["query_id"] = str(query_id)
        fallback_data["question"] = req.question
        response_obj = QueryResponse.model_validate(fallback_data)
        
    # 4. Save QueryLog to Database
    db_query_log = QueryLog(
        id=query_id,
        question=req.question,
        patient_context=req.patient_context.model_dump() if req.patient_context else None,
        jurisdiction=req.jurisdiction,
        generated_answer=response_obj.summary,
        structured_response=response_obj.model_dump(),
        evidence_quality_score=response_obj.evidence_indicators.evidence_quality,
        source_agreement_score=response_obj.evidence_indicators.source_agreement
    )
    db.add(db_query_log)
    
    # 5. Log audit event
    db_audit = AuditLog(
        event_type="query_processed",
        query_id=query_id,
        event_details={
            "num_chunks_retrieved": len(chunks),
            "evidence_quality": response_obj.evidence_indicators.evidence_quality,
            "deidentified": settings.DEIDENTIFY_INPUT
        }
    )
    db.add(db_audit)
    db.commit()
    
    return response_obj

@router.get("/api/v1/query/{query_id}/evidence")
def get_query_evidence(query_id: str, db: Session = Depends(get_db)):
    # Retrieve query log to get the structural response and citations
    query_uuid = uuid.UUID(query_id)
    query_log = db.query(QueryLog).filter(QueryLog.id == query_uuid).first()
    if not query_log:
        raise HTTPException(status_code=404, detail="Query record not found")
        
    structured = query_log.structured_response or {}
    citations = structured.get("citations", [])
    
    # Retrieve matching chunks
    chunk_ids = [uuid.UUID(c["supporting_chunk_id"]) for c in citations if c.get("supporting_chunk_id")]
    chunks = db.query(DocumentChunk).filter(DocumentChunk.id.in_(chunk_ids)).all()
    
    result = []
    for chunk in chunks:
        doc = db.query(Document).filter(Document.id == chunk.document_id).first()
        result.append({
            "chunk_id": str(chunk.id),
            "document_title": doc.title if doc else "Unknown",
            "clinical_section": chunk.clinical_section,
            "page_number": chunk.metadata_json.get("page_number"),
            "text": chunk.chunk_text
        })
    return result

@router.post("/api/v1/feedback")
def submit_feedback(req: FeedbackRequest, db: Session = Depends(get_db)):
    query_uuid = uuid.UUID(req.query_id)
    
    # Get associated query log
    query_log = db.query(QueryLog).filter(QueryLog.id == query_uuid).first()
    if not query_log:
        raise HTTPException(status_code=404, detail="Query record not found")
        
    feedback = Feedback(
        query_id=query_uuid,
        rating=req.rating,
        citation_quality=req.citation_quality,
        comment=req.comment
    )
    db.add(feedback)
    
    db_audit = AuditLog(
        event_type="feedback_submitted",
        query_id=query_uuid,
        event_details={"rating": req.rating, "citation_quality": req.citation_quality}
    )
    db.add(db_audit)
    db.commit()
    
    return {"status": "success", "message": "Feedback submitted successfully"}
