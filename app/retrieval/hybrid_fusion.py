from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.database import DocumentChunk
from app.retrieval.dense_retriever import DenseRetriever
from app.retrieval.sparse_retriever import SparseRetriever
from app.config import settings

class HybridRetriever:
    @staticmethod
    def search(
        db: Session,
        query: str,
        top_k: int = None,
        clinical_section: Optional[str] = None,
        document_id: Optional[str] = None,
        rrf_constant: int = 60
    ) -> List[DocumentChunk]:
        """
        Retrieves document chunks using hybrid search (Dense + Sparse) fused via
        Reciprocal Rank Fusion (RRF).
        """
        if top_k is None:
            top_k = settings.RERANK_TOP_K  # Final fused candidate count

        # Retrieve dense and sparse lists of candidates
        dense_candidates = DenseRetriever.search(
            db=db,
            query=query,
            top_k=settings.DENSE_TOP_K,
            clinical_section=clinical_section,
            document_id=document_id
        )

        sparse_candidates = SparseRetriever.search(
            db=db,
            query=query,
            top_k=settings.SPARSE_TOP_K,
            clinical_section=clinical_section,
            document_id=document_id
        )

        # Reciprocal Rank Fusion scoring dict
        # Map: chunk_id -> [chunk_object, rrf_score]
        fused_scores = {}

        # Fusing Dense candidates
        for rank, chunk in enumerate(dense_candidates):
            chunk_id = chunk.id
            if chunk_id not in fused_scores:
                fused_scores[chunk_id] = [chunk, 0.0]
            fused_scores[chunk_id][1] += 1.0 / (rrf_constant + (rank + 1))

        # Fusing Sparse candidates
        for rank, chunk in enumerate(sparse_candidates):
            chunk_id = chunk.id
            if chunk_id not in fused_scores:
                fused_scores[chunk_id] = [chunk, 0.0]
            fused_scores[chunk_id][1] += 1.0 / (rrf_constant + (rank + 1))

        # Sort and take top_k
        sorted_results = sorted(fused_scores.values(), key=lambda x: x[1], reverse=True)

        return [item[0] for item in sorted_results[:top_k]]
