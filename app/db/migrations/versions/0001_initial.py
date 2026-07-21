"""initial migration

Revision ID: 0001_initial
Revises: 
Create Date: 2026-07-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from app.config import settings

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Enable vector extension (PostgreSQL only)
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create sources table
    op.create_table(
        'sources',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('authority_score', sa.Float(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('source_id', sa.Uuid(), sa.ForeignKey('sources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('publication_date', sa.Date(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('jurisdiction', sa.String(), nullable=True),
        sa.Column('evidence_type', sa.String(), nullable=True),
        sa.Column('evidence_level', sa.String(), nullable=True),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('is_superseded', sa.Boolean(), nullable=True),
        sa.Column('is_retracted', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create document_chunks table
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('document_id', sa.Uuid(), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('clinical_section', sa.String(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('embedding', Vector(settings.EMBEDDING_DIMENSION), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create drugs table
    op.create_table(
        'drugs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('generic_name', sa.String(), nullable=False),
        sa.Column('brand_names', sa.JSON(), nullable=False),
        sa.Column('drug_class', sa.String(), nullable=True),
        sa.Column('active_ingredients', sa.JSON(), nullable=False),
        sa.Column('mechanism_of_action', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('generic_name')
    )

    # Create diseases table
    op.create_table(
        'diseases',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create drug_disease_relations table
    op.create_table(
        'drug_disease_relations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('drug_id', sa.Uuid(), sa.ForeignKey('drugs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('disease_id', sa.Uuid(), sa.ForeignKey('diseases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relation_type', sa.String(), nullable=False),
        sa.Column('evidence_description', sa.Text(), nullable=True),
        sa.Column('document_id', sa.Uuid(), sa.ForeignKey('documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create query_logs table
    op.create_table(
        'query_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('patient_context', sa.JSON(), nullable=True),
        sa.Column('jurisdiction', sa.String(), nullable=True),
        sa.Column('generated_answer', sa.Text(), nullable=True),
        sa.Column('structured_response', sa.JSON(), nullable=True),
        sa.Column('evidence_quality_score', sa.String(), nullable=True),
        sa.Column('source_agreement_score', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create feedback table
    op.create_table(
        'feedback',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('query_id', sa.Uuid(), sa.ForeignKey('query_logs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating', sa.String(), nullable=False),
        sa.Column('citation_quality', sa.String(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('query_id', sa.Uuid(), sa.ForeignKey('query_logs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_details', sa.JSON(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('feedback')
    op.drop_table('query_logs')
    op.drop_table('drug_disease_relations')
    op.drop_table('diseases')
    op.drop_table('drugs')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('sources')
