from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.database import DocumentChunk
from app.config import settings

class SparseRetriever:
    @staticmethod
    def search(
        db: Session,
        query: str,
        top_k: int = None,
        clinical_section: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> List[DocumentChunk]:
        """
        Performs lexical keyword search using PostgreSQL Full-Text Search.
        Includes a fallback for SQLite tests.
        """
        if top_k is None:
            top_k = settings.SPARSE_TOP_K

        # Dialect portability: SQLite does not support PostgreSQL full-text search operators
        if db.bind.dialect.name == "sqlite":
            from sqlalchemy import or_
            # Tokenize query into lowercase keywords of length > 2
            words = [w.strip().lower() for w in query.split() if len(w.strip()) > 2]
            if not words:
                words = [query.lower()]
                
            # Filter chunks containing any of the terms
            filters = [DocumentChunk.chunk_text.ilike(f"%{word}%") for word in words]
            stmt = db.query(DocumentChunk).filter(or_(*filters))
            
            if clinical_section:
                stmt = stmt.filter(DocumentChunk.clinical_section == clinical_section)
            if document_id:
                stmt = stmt.filter(DocumentChunk.document_id == document_id)
            return stmt.limit(top_k).all()

        # PostgreSQL Full-Text Search query
        stmt = db.query(DocumentChunk)
        
        # Apply filters
        if clinical_section:
            stmt = stmt.filter(DocumentChunk.clinical_section == clinical_section)
        if document_id:
            stmt = stmt.filter(DocumentChunk.document_id == document_id)
            
        # Match using plainto_tsquery
        stmt = stmt.filter(
            func.to_tsvector('english', DocumentChunk.chunk_text).op('@@')(
                func.plainto_tsquery('english', query)
            )
        )
        
        # Rank by term frequency score (ts_rank)
        stmt = stmt.order_by(
            func.ts_rank(
                func.to_tsvector('english', DocumentChunk.chunk_text),
                func.plainto_tsquery('english', query)
            ).desc()
        )
        
        return stmt.limit(top_k).all()
