from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.database import DocumentChunk
from app.retrieval.embeddings import EmbeddingService
from app.config import settings

class DenseRetriever:
    @staticmethod
    def search(
        db: Session,
        query: str,
        top_k: int = None,
        clinical_section: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> List[DocumentChunk]:
        """
        Performs dense vector similarity search using pgvector.
        Includes a fallback for SQLite tests.
        """
        if top_k is None:
            top_k = settings.DENSE_TOP_K

        # Convert search query to embedding vector
        query_vector = EmbeddingService.get_embedding(query)

        # Dialect portability: SQLite does not support pgvector functions
        if db.bind.dialect.name == "sqlite":
            stmt = db.query(DocumentChunk)
            if clinical_section:
                stmt = stmt.filter(DocumentChunk.clinical_section == clinical_section)
            if document_id:
                stmt = stmt.filter(DocumentChunk.document_id == document_id)
            return stmt.limit(top_k).all()

        # PostgreSQL pgvector similarity query
        stmt = db.query(DocumentChunk)
        
        # Apply metadata filters
        if clinical_section:
            stmt = stmt.filter(DocumentChunk.clinical_section == clinical_section)
        if document_id:
            stmt = stmt.filter(DocumentChunk.document_id == document_id)
            
        # Sort by pgvector cosine distance
        stmt = stmt.order_by(DocumentChunk.embedding.cosine_distance(query_vector))
        
        return stmt.limit(top_k).all()
