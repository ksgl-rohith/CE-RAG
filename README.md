# Clinical Evidence RAG

> An accuracy-first, evidence-grounded medical drug information assistant built with adaptive and iterative Retrieval-Augmented Generation (RAG).

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688)](https://fastapi.tiangolo.com/)
[![Gradio](https://img.shields.io/badge/Gradio-Interface-orange)](https://www.gradio.app/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791)](https://www.postgresql.org/)
[![pgvector](https://img.shields.io/badge/pgvector-Vector_Search-4B32C3)](https://github.com/pgvector/pgvector)
[![Status](https://img.shields.io/badge/Status-Research_Prototype-yellow)](#project-status)

## Overview

Medical drug information is distributed across regulatory labels, clinical guidelines, randomized controlled trials, systematic reviews, meta-analyses, pharmacokinetic and pharmacodynamic publications, and drug reference databases. Finding and reconciling this information can be slow and difficult, especially when a question involves age, pregnancy, kidney or liver function, comorbidities, interactions, side effects, therapeutic alternatives, or treatment duration.

This project proposes an **Adaptive and Iterative Medical RAG system** that retrieves evidence from trusted sources, evaluates whether that evidence is sufficient, corrects weak retrieval, and produces structured answers with traceable citations.

The system is designed as an **evidence-based clinical drug information and decision-support assistant**. It does not independently diagnose, prescribe, or replace a qualified physician or pharmacist.

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Goals](#goals)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [RAG Pipeline Workflow](#rag-pipeline-workflow)
- [How Adaptive and Iterative RAG Works](#how-adaptive-and-iterative-rag-works)
- [Use Cases](#use-cases)
- [Trusted Evidence Sources](#trusted-evidence-sources)
- [Evidence Prioritization](#evidence-prioritization)
- [Technology Stack](#technology-stack)
- [Recommended Repository Structure](#recommended-repository-structure)
- [Data Model](#data-model)
- [Retrieval and Ranking Strategy](#retrieval-and-ranking-strategy)
- [Response Contract](#response-contract)
- [API Design](#api-design)
- [Local Development](#local-development)
- [Configuration](#configuration)
- [Evaluation](#evaluation)
- [Medical Safety and Privacy](#medical-safety-and-privacy)
- [Limitations](#limitations)
- [Roadmap](#roadmap)
- [Project Status](#project-status)
- [References](#references)
- [License](#license)

---

## Problem Statement

For a single disease, multiple drugs may be available with different active ingredients, mechanisms, dosage forms, contraindications, age restrictions, adverse effects, interactions, treatment durations, monitoring requirements, and levels of supporting evidence.

Lack of consolidated, reliable, and patient-relevant information can lead to:

- Poor understanding of a drug's composition and approved use.
- Confusion between exact generic substitutes and therapeutic alternatives.
- Missed contraindications and drug interactions.
- Inappropriate interpretation of side effects.
- Insufficient attention to age, pregnancy, renal, hepatic, or comorbidity-specific considerations.
- Overreliance on incomplete or low-quality information.
- Difficulty identifying what diseases a medicine is approved or supported to treat.
- Uncertainty about expected onset, reassessment period, and typical treatment duration.

The proposed system addresses this problem by retrieving and synthesizing evidence from high-quality medical sources while exposing the basis, limitations, and confidence of every answer.

---

## Goals

### Primary goals

1. Prioritize **clinical accuracy and evidence quality** over response speed.
2. Generate answers using only retrieved and approved medical evidence.
3. Provide claim-level citations and source traceability.
4. Adapt retrieval strategy to the query's intent, complexity, and safety risk.
5. Repeat retrieval when evidence is weak, incomplete, conflicting, or mismatched.
6. Abstain when the available evidence is insufficient.
7. Clearly distinguish:
   - Approved indications
   - Off-label evidence
   - Exact generic substitutes
   - Therapeutic alternatives
   - General information
   - Patient-specific clinical decisions

### Non-goals

- Autonomous diagnosis
- Autonomous prescribing
- Emergency triage replacement
- Medication initiation, discontinuation, or dose changes without clinician review
- Guaranteed cure-time predictions
- Replacement of official drug labels or clinical guidelines

---

## Key Features

- Evidence-based drug information lookup
- Disease-to-drug and drug-to-disease exploration
- Active ingredient and composition lookup
- Approved indication identification
- Generic substitute discovery
- Therapeutic alternative comparison
- Drug–drug, drug–food, and drug–disease interaction retrieval
- Age-group, pregnancy, renal, and hepatic safety checks
- Side-effect and warning summaries
- Treatment onset, duration, and reassessment evidence
- Monitoring requirement retrieval
- Guideline, trial, and regulatory evidence comparison
- Adaptive query routing
- Multi-hop query decomposition
- Hybrid retrieval using dense, sparse, and metadata-based search
- Clinical cross-encoder reranking
- Evidence sufficiency evaluation
- Corrective iterative retrieval
- Conflict detection
- Claim-level citation verification
- Structured evidence and confidence indicators
- Clinician feedback and audit logging

---

## System Architecture

The architecture separates trusted-source ingestion, clinical document processing, structured and vector storage, the medical RAG orchestrator, response generation, verification, and continuous improvement.

![Adaptive and Iterative Medical RAG Architecture](assets/medical-rag-architecture.png)

### Main architecture layers

1. **Trusted medical sources**
2. **Ingestion and knowledge processing**
3. **PostgreSQL metadata and pgvector knowledge store**
4. **Adaptive medical RAG orchestrator**
5. **Grounded generation and citation verification**
6. **Gradio user interface**
7. **Audit, feedback, and continuous improvement loop**

---

## RAG Pipeline Workflow

The online query workflow determines query risk and complexity, selects the most appropriate evidence sources, retrieves and reranks evidence, evaluates sufficiency, and iterates when necessary.

![Adaptive and Iterative Medical RAG Pipeline](assets/medical-rag-pipeline.png)

### High-level flow

```text
User query
    ↓
Safety and privacy screening
    ↓
Medical entity extraction
    ↓
Intent, risk, and complexity classification
    ↓
Query rewriting and decomposition
    ↓
Adaptive source selection
    ↓
Hybrid retrieval
    ↓
Clinical reranking
    ↓
Evidence sufficiency check
    ├── Insufficient → corrective retrieval loop
    └── Sufficient
            ↓
Context assembly
            ↓
Grounded answer generation
            ↓
Claim and citation verification
            ↓
Structured response
            ↓
User feedback and audit logs
```

---

## How Adaptive and Iterative RAG Works

### Adaptive RAG

Adaptive RAG changes the retrieval strategy according to the query.

| Query type | Example | Retrieval policy |
|---|---|---|
| Simple factual | What is the active ingredient in Drug X? | Regulatory label and drug monograph |
| Approved use | What diseases is Drug X approved to treat? | Regulatory label first |
| Guideline question | What is first-line therapy for Disease Y? | Current clinical guidelines |
| Comparative | Compare Drug A and Drug B for Disease Y | Guidelines, systematic reviews, meta-analyses, head-to-head RCTs |
| Interaction | Can Drug A and Drug B be taken together? | Label interaction sections, PK/PD evidence, interaction references |
| High risk | Is Drug X safe during pregnancy or in CKD? | Authoritative sources, strict filters, mandatory uncertainty reporting |
| Complex patient context | Which option is safer for an elderly patient with CKD and diabetes? | Multi-hop retrieval with population-specific filters |

For medical questions, adaptive routing changes the **depth, source selection, filters, and number of retrieval rounds**. It should not permit unsupported model-only clinical answers.

### Iterative RAG

The iterative loop improves weak or incomplete retrieval.

```text
Retrieve
   ↓
Evaluate relevance, authority, coverage, and population match
   ↓
Is evidence sufficient?
   ├── Yes → generate and verify
   └── No
        ↓
Identify missing evidence
        ↓
Rewrite or decompose query
        ↓
Expand synonyms and medical ontology terms
        ↓
Change source collection or metadata filters
        ↓
Retrieve and evaluate again
```

Recommended maximum: **three corrective retrieval rounds**. After the limit, the system should return an evidence-limited answer or abstain.

### Corrective actions

- Expand generic and brand names.
- Map lay terms to clinical terminology.
- Expand abbreviations using medical ontologies.
- Add disease synonyms and MeSH concepts.
- Retrieve missing clinical sections.
- Increase or reduce `top_k`.
- Tighten age, pregnancy, renal, hepatic, or disease filters.
- Search a different evidence collection.
- Prefer current guidelines or regulatory revisions.
- Retrieve older landmark trials when newer direct evidence is unavailable.
- Detect and explain conflicting sources.

---

## Use Cases

### 1. Complete drug information

**Question**

> What is metformin used for, how does it work, what are its common side effects, and which patients require additional caution?

**Expected output**

- Generic and brand information
- Drug class
- Approved indications
- Mechanism of action
- Common and serious adverse effects
- Contraindications and warnings
- Renal and hepatic considerations
- Monitoring requirements
- Evidence sources and limitations

---

### 2. Disease coverage lookup

**Question**

> Which diseases is Drug X approved to treat, and what off-label evidence exists?

**Expected behavior**

- Retrieve the regulatory label for approved indications.
- Keep approved and off-label uses in separate sections.
- Attach evidence type and jurisdiction to every use.
- Avoid presenting an off-label use as regulatory approval.

---

### 3. Generic substitute and therapeutic alternative finder

**Question**

> What are the alternatives to Drug X for hypertension?

**Expected behavior**

The system first determines whether the user is asking for:

1. The same active ingredient from another manufacturer.
2. A pharmaceutically equivalent generic.
3. A medication from the same therapeutic class.
4. A different guideline-supported treatment class.

The answer must not claim interchangeability unless supported by appropriate regulatory evidence.

---

### 4. Patient-specific contraindication review

**Question**

> Can a 70-year-old patient with chronic kidney disease and hypertension take Drug X?

**Expected behavior**

- Classify as a high-risk patient-specific query.
- Retrieve geriatric and renal-impairment sections.
- Search contraindications, warnings, dosage adjustments, and monitoring.
- Evaluate interactions with current antihypertensive medicines.
- State which patient details are still required, such as eGFR.
- Require clinician or pharmacist review for the final decision.

---

### 5. Drug–drug interaction analysis

**Question**

> Are warfarin and aspirin safe to take together?

**Expected output**

- Interaction status: documented, not documented, or uncertain
- Mechanism
- Potential clinical effect
- Severity
- Higher-risk populations
- Monitoring considerations
- Evidence quality and citations

---

### 6. Comparative effectiveness

**Question**

> Compare Drug A and Drug B for Disease Y.

**Expected behavior**

The system decomposes the question into:

- Efficacy
- Adverse effects
- Contraindications
- Patient population
- Treatment duration
- Monitoring
- Guideline position
- Direct versus indirect comparative evidence

The system should not identify a universal winner when patient context or direct evidence is missing.

---

### 7. Treatment onset and duration

**Question**

> How long does Drug X usually take to improve Disease Y?

**Expected output**

- Expected onset of response
- Typical reassessment period
- Duration used in clinical trials
- Usual treatment duration when supported
- Long-term maintenance considerations
- Factors that change the timeline
- Warning against treating the estimate as a guaranteed cure date

---

### 8. Side-effect investigation

**Question**

> A patient developed dizziness after starting Drug X. Could the medicine be responsible?

**Expected behavior**

- Retrieve known adverse-reaction evidence.
- Check time relationship, dose, and interacting medicines.
- Detect urgent warning signs.
- Avoid establishing causality without clinical evaluation.
- Recommend appropriate professional review.

---

### 9. Evidence summary

**Question**

> Summarize current RCT and meta-analysis evidence for SGLT2 inhibitors in heart failure.

**Expected behavior**

- Search systematic reviews, meta-analyses, RCTs, and guidelines.
- Separate outcomes by patient population and heart-failure subtype.
- Explain study endpoints, sample size, and major limitations.
- Highlight inconsistent or missing evidence.

---

## Trusted Evidence Sources

The primary knowledge base should use approved, versioned sources.

### Regulatory and drug-label sources

- [FDA Clinical Decision Support Software Guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software)
- [DailyMed](https://dailymed.nlm.nih.gov/)
- [DailyMed Drug Label Downloads](https://dailymed.nlm.nih.gov/dailymed/spl-resources-all-drug-labels.cfm)
- [Drugs@FDA](https://www.accessdata.fda.gov/scripts/cder/daf/)
- [European Medicines Agency](https://www.ema.europa.eu/)

### Guidelines and global references

- [WHO Guidelines](https://www.who.int/publications/who-guidelines)
- [WHO Drug Information](https://www.who.int/our-work/access-to-medicines-and-health-products/who-drug-information)
- [WHO Model Lists of Essential Medicines](https://www.who.int/groups/expert-committee-on-selection-and-use-of-essential-medicines/essential-medicines-lists)
- Specialty-society guidelines relevant to each disease domain

### Research and trial sources

- [PubMed](https://pubmed.ncbi.nlm.nih.gov/)
- [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/home/develop/api/)
- [ClinicalTrials.gov](https://clinicaltrials.gov/)
- [ClinicalTrials.gov API](https://clinicaltrials.gov/data-api/api)

### Evidence types

- Clinical practice guidelines
- Regulatory product labels
- Systematic reviews
- Meta-analyses
- Randomized controlled trials
- Pharmacokinetic studies
- Pharmacodynamic studies
- Observational studies
- Clinical trial registry records
- Trusted drug monographs

### Source governance

Each source should have:

- Source owner
- Retrieval method
- License or usage terms
- Update frequency
- Last ingestion date
- Document version
- Retraction or supersession status
- Jurisdiction
- Trust tier
- Data-retention policy

Do not ingest arbitrary blogs, advertisements, discussion forums, or unverified health websites into the primary evidence index.

---

## Evidence Prioritization

There is no single fixed hierarchy for every question. Ranking must be **task-dependent**.

| Question | Preferred source |
|---|---|
| Approved indication | Current regulatory label |
| Contraindication or warning | Current regulatory label and current guideline |
| Exact dosage form or composition | Regulatory label |
| First-line therapy | Current clinical guideline |
| Comparative effectiveness | Meta-analysis, systematic review, head-to-head RCT |
| Pharmacokinetics | Label and PK study |
| Pharmacodynamics | Label and PD study |
| Trial recruitment status | ClinicalTrials.gov |
| Generic equivalence | Regulatory equivalence data |
| Treatment duration | Guideline, label, and clinical trial evidence |

### Suggested general scoring factors

```text
final_score =
    semantic_relevance
  + sparse_term_match
  + exact_entity_match
  + patient_population_match
  + evidence_quality
  + source_authority
  + recency
  + section_match
  + jurisdiction_match
  - conflict_penalty
  - superseded_document_penalty
```

The weights should be calibrated using clinician-reviewed evaluation data.

---

## Technology Stack

| Layer | Technology |
|---|---|
| User interface | Gradio |
| API backend | FastAPI |
| Language | Python 3.11+ |
| Relational database | PostgreSQL |
| Vector search | pgvector |
| Sparse search | PostgreSQL full-text search |
| Data validation | Pydantic |
| ORM / database access | SQLAlchemy or SQLModel |
| Migrations | Alembic |
| Retrieval | Custom hybrid retriever or a RAG framework |
| Reranking | Medical cross-encoder |
| Embeddings | Domain-appropriate biomedical embedding model |
| Generation | Configurable LLM with grounded structured output |
| Background ingestion | Celery, RQ, or scheduled workers |
| Cache | Redis, optional |
| Observability | OpenTelemetry and structured logs |
| Containerization | Docker and Docker Compose |
| Testing | Pytest |
| Evaluation | Retrieval, citation, factuality, safety, and clinician review |

---

## Recommended Repository Structure

```text
adaptive-medical-rag/
├── README.md
├── LICENSE
├── .env.example
├── .gitignore
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── alembic.ini
├── assets/
│   ├── medical-rag-architecture.png
│   └── medical-rag-pipeline.png
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── routes_health.py
│   │   ├── routes_query.py
│   │   ├── routes_feedback.py
│   │   └── routes_admin.py
│   ├── models/
│   │   ├── requests.py
│   │   ├── responses.py
│   │   └── database.py
│   ├── safety/
│   │   ├── privacy_filter.py
│   │   ├── emergency_detector.py
│   │   ├── risk_classifier.py
│   │   └── output_policy.py
│   ├── medical_nlp/
│   │   ├── entity_extractor.py
│   │   ├── terminology.py
│   │   ├── query_classifier.py
│   │   └── query_decomposer.py
│   ├── retrieval/
│   │   ├── dense_retriever.py
│   │   ├── sparse_retriever.py
│   │   ├── metadata_filters.py
│   │   ├── hybrid_fusion.py
│   │   ├── reranker.py
│   │   └── sufficiency.py
│   ├── rag/
│   │   ├── orchestrator.py
│   │   ├── corrective_loop.py
│   │   ├── context_builder.py
│   │   ├── generator.py
│   │   ├── conflict_detector.py
│   │   └── citation_verifier.py
│   ├── db/
│   │   ├── session.py
│   │   ├── repositories.py
│   │   └── migrations/
│   ├── ingestion/
│   │   ├── connectors/
│   │   ├── parsers/
│   │   ├── section_chunker.py
│   │   ├── metadata_enricher.py
│   │   ├── deduplicator.py
│   │   └── indexer.py
│   ├── evaluation/
│   │   ├── retrieval_metrics.py
│   │   ├── citation_metrics.py
│   │   ├── safety_metrics.py
│   │   └── benchmark_runner.py
│   └── ui/
│       └── gradio_app.py
├── scripts/
│   ├── ingest_sources.py
│   ├── create_indexes.py
│   ├── reindex_documents.py
│   └── run_evaluation.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── retrieval/
│   ├── safety/
│   └── evaluation/
└── data/
    ├── raw/
    ├── processed/
    └── evaluation/
```

---

## Data Model

### Core tables

```text
sources
documents
document_versions
document_chunks
chunk_embeddings
drugs
drug_names
drug_ingredients
drug_indications
diseases
drug_disease_relations
contraindications
warnings
adverse_effects
drug_interactions
dosage_sections
population_constraints
clinical_guidelines
clinical_studies
study_outcomes
citations
queries
retrieval_runs
generated_answers
answer_claims
claim_citations
user_feedback
audit_events
```

### Example document metadata

```json
{
  "document_id": "doc_123",
  "source_name": "DailyMed",
  "source_type": "regulatory_label",
  "title": "Example Drug Label",
  "publication_date": "2026-01-01",
  "last_reviewed_date": "2026-07-01",
  "version": "4",
  "jurisdiction": "US",
  "evidence_type": "regulatory_label",
  "evidence_level": "authoritative",
  "drug_names": ["generic name", "brand name"],
  "diseases": ["disease concept"],
  "population": ["adult"],
  "clinical_section": "contraindications",
  "source_url": "https://example.org/document",
  "superseded": false,
  "retracted": false
}
```

### pgvector setup

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    chunk_text TEXT NOT NULL,
    clinical_section TEXT,
    metadata JSONB NOT NULL,
    embedding VECTOR(1024),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX document_chunks_metadata_idx
    ON document_chunks
    USING GIN (metadata);

CREATE INDEX document_chunks_text_idx
    ON document_chunks
    USING GIN (to_tsvector('english', chunk_text));

CREATE INDEX document_chunks_embedding_idx
    ON document_chunks
    USING hnsw (embedding vector_cosine_ops);
```

Change the embedding dimension to match the selected embedding model.

---

## Retrieval and Ranking Strategy

### 1. Query understanding

Extract and normalize:

- Drug name
- Active ingredient
- Brand name
- Disease
- Symptom
- Intent
- Age group
- Sex
- Pregnancy or breastfeeding status
- Allergies
- Current medicines
- Renal status
- Hepatic status
- Relevant laboratory values
- Geographic or regulatory jurisdiction

### 2. Query decomposition

Example:

```text
Original:
Is Drug A or Drug B safer for a 68-year-old patient with diabetes and CKD?

Subqueries:
1. What are the approved indications for Drug A and Drug B?
2. What renal contraindications or dose adjustments apply?
3. What evidence is available for adults over 65?
4. Are there important interactions with common diabetes medicines?
5. What comparative safety evidence exists?
6. What do current guidelines recommend?
7. What monitoring is required?
```

### 3. Hybrid retrieval

Use:

- Dense vector similarity
- PostgreSQL full-text search
- Exact entity matching
- Metadata filtering
- Source-specific retrieval
- Reciprocal rank fusion or calibrated weighted fusion

### 4. Reranking

Candidate evidence should be reranked by:

- Relevance
- Drug and disease match
- Population match
- Clinical-section match
- Source authority
- Evidence design
- Publication date
- Guideline currency
- Jurisdiction
- Document status
- Contradiction risk

### 5. Evidence sufficiency

Example internal result:

```json
{
  "relevance": 0.93,
  "authority": 0.96,
  "coverage": 0.68,
  "population_match": 0.72,
  "source_agreement": 0.55,
  "missing_topics": [
    "renal dose adjustment",
    "geriatric subgroup evidence"
  ],
  "action": "iterate"
}
```

### 6. Stopping rules

Stop retrieval when:

- Required clinical sections are covered.
- The evidence meets minimum authority thresholds.
- The patient population is adequately represented.
- The answer can be fully cited.
- No unresolved high-risk contradiction remains.

Abstain or return a limited answer when:

- No authoritative source supports the claim.
- The evidence is outdated or superseded.
- Patient-specific evidence is unavailable.
- Sources materially conflict.
- The query requests unsafe autonomous medical action.
- The maximum corrective-retrieval limit is reached.

---

## Response Contract

Every answer should use a predictable structure.

```json
{
  "question": "Original user question",
  "summary": "Direct, carefully qualified answer",
  "drug_information": {
    "generic_name": null,
    "brand_names": [],
    "drug_class": null,
    "active_ingredients": [],
    "mechanism": null
  },
  "indications": {
    "approved": [],
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
    "expected_onset": null,
    "reassessment_period": null,
    "typical_duration": null,
    "limitations": null
  },
  "monitoring": [],
  "evidence_indicators": {
    "evidence_quality": "high | moderate | low",
    "population_match": "high | moderate | low",
    "source_agreement": "high | moderate | low",
    "answer_completeness": "high | moderate | low"
  },
  "limitations": [],
  "citations": []
}
```

### Claim-level citation requirements

Every clinically relevant claim should store:

```text
claim_id
claim_text
supporting_chunk_id
source_document_id
source_passage
citation_url
entailment_status
verification_score
```

Unsupported claims must be removed before the answer is returned.

---

## API Design

### Health check

```http
GET /health
```

### Ask a medical drug-information question

```http
POST /api/v1/query
Content-Type: application/json
```

```json
{
  "question": "Can a patient with CKD take Drug X?",
  "patient_context": {
    "age": 70,
    "sex": "female",
    "conditions": ["chronic kidney disease", "hypertension"],
    "current_medications": [],
    "allergies": [],
    "pregnancy_status": "not_applicable",
    "renal": {
      "egfr": null,
      "stage": null
    },
    "hepatic": {
      "impairment": null
    }
  },
  "jurisdiction": "US",
  "audience": "clinician"
}
```

### Retrieve evidence for review

```http
GET /api/v1/query/{query_id}/evidence
```

### Submit feedback

```http
POST /api/v1/feedback
```

```json
{
  "query_id": "query_uuid",
  "rating": "helpful",
  "citation_quality": "correct",
  "comment": "The renal section was useful."
}
```

### Administrative ingestion

```http
POST /api/v1/admin/ingest
POST /api/v1/admin/reindex
GET  /api/v1/admin/source-status
```

Administrative endpoints must require authentication and authorization.

---

## Local Development

### Prerequisites

- Python 3.11 or later
- PostgreSQL with pgvector
- Docker and Docker Compose, recommended
- An approved embedding model
- An approved LLM provider or locally hosted model
- API credentials for sources that require them

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/adaptive-medical-rag.git
cd adaptive-medical-rag
```

### 2. Create the environment file

```bash
cp .env.example .env
```

Never commit `.env`, credentials, patient data, or private API keys.

### 3. Start PostgreSQL and supporting services

```bash
docker compose up -d postgres
```

### 4. Create a Python environment

```bash
python -m venv .venv

# macOS or Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Run database migrations

```bash
alembic upgrade head
```

### 7. Ingest approved evidence

```bash
python scripts/ingest_sources.py --source dailymed
python scripts/ingest_sources.py --source pubmed
python scripts/ingest_sources.py --source clinicaltrials
python scripts/create_indexes.py
```

Only ingest sources whose licensing, access, update, and attribution requirements have been reviewed.

### 8. Start FastAPI

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

### 9. Start Gradio

```bash
python app/ui/gradio_app.py
```

Typical local URL:

```text
http://localhost:7860
```

### 10. Run tests

```bash
pytest -q
```

### 11. Run evaluation

```bash
python scripts/run_evaluation.py \
  --dataset data/evaluation/clinician_reviewed.jsonl
```

---

## Configuration

Example `.env.example`:

```dotenv
APP_ENV=development
APP_NAME=Adaptive Medical RAG
API_HOST=0.0.0.0
API_PORT=8000
GRADIO_PORT=7860

DATABASE_URL=postgresql+psycopg://medical_rag:medical_rag@localhost:5432/medical_rag
POSTGRES_DB=medical_rag
POSTGRES_USER=medical_rag
POSTGRES_PASSWORD=change_me

EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=<biomedical-embedding-model>
EMBEDDING_DIMENSION=1024

LLM_PROVIDER=<provider-or-local>
LLM_MODEL=<model-name>
LLM_API_KEY=
LLM_TEMPERATURE=0.0

DENSE_TOP_K=30
SPARSE_TOP_K=30
RERANK_TOP_K=12
MAX_RETRIEVAL_ITERATIONS=3
MIN_EVIDENCE_AUTHORITY_SCORE=0.80
MIN_CITATION_SUPPORT_SCORE=0.85

PUBMED_API_KEY=
PUBMED_TOOL_NAME=adaptive-medical-rag
PUBMED_CONTACT_EMAIL=

ENABLE_AUDIT_LOGS=true
ENABLE_QUERY_STORAGE=false
DEIDENTIFY_INPUT=true
```

### Production recommendations

- Use a managed secrets service.
- Encrypt data in transit and at rest.
- Disable raw patient-query retention by default.
- Use role-based access control.
- Separate development, test, and production databases.
- Add request quotas and rate limiting.
- Use immutable source-version records.
- Maintain backups and point-in-time recovery.
- Add model, prompt, retriever, and source-version identifiers to audit logs.

---

## Evaluation

The evaluation process must measure retrieval, generation, citation quality, medical safety, and clinician usability.

### Retrieval metrics

- Recall@K
- Precision@K
- Mean Reciprocal Rank
- nDCG
- Exact drug and disease match
- Clinical-section coverage
- Evidence-authority coverage
- Patient-population match
- Guideline recency
- Retrieval iteration success rate

### Answer metrics

- Claim-supportedness
- Citation precision
- Citation completeness
- Medical factuality
- Numerical and dosage accuracy
- Unsupported-claim rate
- Contradiction rate
- Evidence-conflict disclosure rate
- Correct abstention rate
- Unsafe recommendation rate

### Clinical review

- Physician review
- Pharmacist review
- Inter-rater agreement
- High-risk error rate
- Time required to verify the answer
- Percentage of claims independently reproducible from citations
- Percentage of answers requiring material correction

### Recommended primary metric

> Percentage of clinically relevant claims correctly supported by authoritative citations, with zero unsupported high-risk claims.

### Test-set categories

The evaluation dataset should include:

- Simple drug facts
- Approved versus off-label uses
- Drug–drug interactions
- Pregnancy and lactation
- Pediatric and geriatric questions
- Renal and hepatic impairment
- Allergies and contraindications
- Conflicting evidence
- Rare diseases
- Misspelled drug names
- Brand and generic synonyms
- Missing patient information
- Emergency symptom questions
- Outdated or superseded evidence
- Adversarial prompts requesting unsupported prescribing

---

## Medical Safety and Privacy

### Safety principles

- Treat the application as decision support, not autonomous care.
- Display the evidence basis and limitations.
- Never invent dosage, contraindications, or interactions.
- Never hide disagreement between sources.
- Do not promise a cure or exact recovery date.
- Keep regulatory approval separate from off-label evidence.
- Escalate high-risk questions to clinician review.
- Provide an evidence-insufficient response when support is weak.
- Add emergency guidance when urgent symptoms are detected.
- Validate all dose units, decimal points, age ranges, and frequencies.
- Use deterministic or low-temperature generation.
- Require claim-level citation verification.

### Privacy principles

- Avoid collecting direct identifiers.
- De-identify input before retrieval and logging.
- Store only the minimum necessary information.
- Do not use private medical data for model training without explicit governance.
- Configure retention periods.
- Restrict audit-log access.
- Encrypt sensitive data.
- Maintain access and deletion procedures.
- Consult applicable privacy, medical-device, and clinical software requirements before deployment.

### Required user-facing disclaimer

> This application provides evidence-based drug information for research and clinical decision support. It does not diagnose conditions, prescribe treatment, replace official drug labeling, or replace a licensed healthcare professional. Do not start, stop, substitute, or change the dose of a medicine based only on this system. For emergencies or severe symptoms, contact local emergency services immediately.

### Regulatory note

The legal and regulatory classification of a medical software product depends on its intended use, users, functions, claims, jurisdiction, and deployment context. Obtain qualified regulatory, clinical, privacy, and legal review before any real-world clinical deployment.

---

## Limitations

- Source availability and licensing may restrict full-text ingestion.
- Publication evidence may not represent all populations.
- Trial populations may differ from the patient in question.
- Regulatory indications vary by country.
- Brand names and formulations vary by market.
- Evidence can become outdated.
- Clinical guidelines may conflict.
- Abstract-only evidence may omit important methodological details.
- Embedding retrieval can miss exact numerical or tabular facts.
- LLMs can still produce incorrect statements without strict verification.
- A high retrieval score does not guarantee clinical applicability.
- Treatment response varies between individuals.
- Patient-specific decisions require complete medical history and clinician judgment.

---

## Roadmap

### Phase 1: Foundation

- Finalize intended use and target users.
- Select 5–10 disease domains for the MVP.
- Define the evidence-source allowlist.
- Implement PostgreSQL and pgvector schema.
- Build document ingestion and clinical-section chunking.
- Add regulatory-label and guideline retrieval.
- Create baseline Gradio and FastAPI applications.

### Phase 2: Adaptive retrieval

- Medical entity normalization
- Intent and risk classification
- Query decomposition
- Source routing
- Dense and sparse retrieval
- Metadata filters
- Clinical reranking

### Phase 3: Iterative correction

- Evidence sufficiency scoring
- Missing-section detection
- Corrective query expansion
- Multi-hop retrieval
- Conflict detection
- Retrieval stopping rules

### Phase 4: Verification and safety

- Claim extraction
- Citation entailment verification
- Numerical and dosage validation
- Emergency screening
- Abstention policies
- Structured confidence indicators
- Audit logging

### Phase 5: Evaluation

- Clinician-reviewed benchmark
- Pharmacist and physician evaluation
- High-risk test cases
- Adversarial and hallucination testing
- Regression testing for every source or model update

### Phase 6: Controlled deployment

- Authentication and role-based access
- Privacy and retention controls
- Observability and monitoring
- Source-update automation
- Model and retrieval versioning
- Human-in-the-loop review
- Regulatory assessment

### Future extensions

- FHIR-compatible interoperability
- EHR integration
- Multilingual explanations
- Patient-friendly and clinician-specific answer modes
- Drug-label table extraction
- Clinical trial matching
- Pharmacovigilance integration
- Locally hosted models for controlled environments
- Institution-specific guideline collections

---

## Project Status

**Current status:** Research and development prototype.

This repository should not be described as clinically validated until it has completed:

- Formal source governance
- Clinical expert evaluation
- Safety testing
- Privacy review
- Security review
- Regulatory assessment
- Prospective real-world validation

---

## References

### Medical and regulatory sources

- [FDA Clinical Decision Support Software Guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software)
- [WHO Guidelines](https://www.who.int/publications/who-guidelines)
- [WHO Drug Information](https://www.who.int/our-work/access-to-medicines-and-health-products/who-drug-information)
- [WHO Essential Medicines Lists](https://www.who.int/groups/expert-committee-on-selection-and-use-of-essential-medicines/essential-medicines-lists)
- [DailyMed](https://dailymed.nlm.nih.gov/)
- [ClinicalTrials.gov API](https://clinicaltrials.gov/data-api/api)
- [PubMed](https://pubmed.ncbi.nlm.nih.gov/)
- [NCBI Developer APIs](https://www.ncbi.nlm.nih.gov/home/develop/api/)

### Technical documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Gradio Documentation](https://www.gradio.app/docs)
- [pgvector](https://github.com/pgvector/pgvector)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### RAG research concepts

Useful research areas for this architecture include:

- Adaptive Retrieval-Augmented Generation
- Corrective Retrieval-Augmented Generation
- Self-reflective Retrieval-Augmented Generation
- Hybrid dense and sparse retrieval
- Retrieval reranking
- Natural language inference for citation verification
- Medical evidence grading
- Clinical question decomposition
- Selective generation and abstention

Review original publications and licenses before reproducing implementation details.

---

## Contributing

Contributions should preserve the project's accuracy-first principles.

Before opening a pull request:

1. Add or update tests.
2. Document new data sources and licensing constraints.
3. Record source-update behavior.
4. Include retrieval and safety evaluation results.
5. Avoid weakening abstention or citation requirements.
6. Do not commit patient data or credentials.
7. Request clinical review for changes affecting medical logic.

Suggested branch naming:

```text
feature/<name>
fix/<name>
data-source/<name>
evaluation/<name>
safety/<name>
```

---

## License

Choose a license after reviewing:

- Source-data licenses
- Model licenses
- Embedding-model licenses
- Clinical terminology licenses
- Drug-database usage conditions
- Deployment and liability requirements

A permissive software license does not override restrictions attached to medical source data, model weights, terminology systems, or third-party APIs.

---

## Acknowledgment

This project is intended to improve access to traceable medical evidence while keeping healthcare professionals in control of clinical decisions. Accuracy, transparency, source quality, and appropriate abstention are treated as core product requirements rather than optional enhancements.
