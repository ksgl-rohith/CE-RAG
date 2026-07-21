import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, Boolean, Date, DateTime, ForeignKey, JSON, Uuid
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.config import settings
from pgvector.sqlalchemy import Vector

class Source(Base):
    __tablename__ = "sources"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    source_type = Column(String, nullable=False)  # e.g., "regulatory_label", "clinical_guideline"
    authority_score = Column(Float, default=1.0)
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="source", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(Uuid(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    title = Column(String, nullable=False)
    publication_date = Column(Date, nullable=True)
    version = Column(String, nullable=True)
    jurisdiction = Column(String, nullable=True)  # e.g., "US", "Global"
    evidence_type = Column(String, nullable=True)  # e.g., "guideline", "regulatory_label"
    evidence_level = Column(String, nullable=True)  # e.g., "authoritative", "peer_reviewed"
    source_url = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    is_superseded = Column(Boolean, default=False)
    is_retracted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    source = relationship("Source", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    drug_relations = relationship("DrugDiseaseRelation", back_populates="document")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(Uuid(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    clinical_section = Column(String, nullable=True)  # e.g., "warnings", "contraindications", "dosage"
    metadata_json = Column(JSON, nullable=False, default=dict)
    embedding = Column(Vector(settings.EMBEDDING_DIMENSION), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="chunks")


class Drug(Base):
    __tablename__ = "drugs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    generic_name = Column(String, unique=True, nullable=False)
    brand_names = Column(JSON, nullable=False, default=list)  # list of strings
    drug_class = Column(String, nullable=True)
    active_ingredients = Column(JSON, nullable=False, default=list)  # list of strings
    mechanism_of_action = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    disease_relations = relationship("DrugDiseaseRelation", back_populates="drug", cascade="all, delete-orphan")


class Disease(Base):
    __tablename__ = "diseases"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    drug_relations = relationship("DrugDiseaseRelation", back_populates="disease", cascade="all, delete-orphan")


class DrugDiseaseRelation(Base):
    __tablename__ = "drug_disease_relations"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drug_id = Column(Uuid(as_uuid=True), ForeignKey("drugs.id"), nullable=False)
    disease_id = Column(Uuid(as_uuid=True), ForeignKey("diseases.id"), nullable=False)
    relation_type = Column(String, nullable=False)  # e.g., "indication", "contraindication"
    evidence_description = Column(Text, nullable=True)
    document_id = Column(Uuid(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    drug = relationship("Drug", back_populates="disease_relations")
    disease = relationship("Disease", back_populates="drug_relations")
    document = relationship("Document", back_populates="drug_relations")


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    patient_context = Column(JSON, nullable=True)  # de-identified clinical history
    jurisdiction = Column(String, nullable=True)
    generated_answer = Column(Text, nullable=True)
    structured_response = Column(JSON, nullable=True)  # response contract payload
    evidence_quality_score = Column(String, nullable=True)  # e.g. "high", "moderate", "low"
    source_agreement_score = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    feedback = relationship("Feedback", back_populates="query", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="query", cascade="all, delete-orphan")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_id = Column(Uuid(as_uuid=True), ForeignKey("query_logs.id"), nullable=False)
    rating = Column(String, nullable=False)  # "helpful" or "unhelpful"
    citation_quality = Column(String, nullable=True)  # "correct", "hallucination", "missing"
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    query = relationship("QueryLog", back_populates="feedback")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String, nullable=False)  # e.g. "query_received", "deidentification_performed"
    query_id = Column(Uuid(as_uuid=True), ForeignKey("query_logs.id"), nullable=True)
    event_details = Column(JSON, nullable=False, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)

    query = relationship("QueryLog", back_populates="audit_logs")
