import sys
import os
import argparse

# Add root folder to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.models.database import DocumentChunk
from app.config import settings

def main():
    parser = argparse.ArgumentParser(description="Create embedding indexes for document chunks in the MedRAG database.")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size for generating embeddings.")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        # Fetch chunks without embeddings
        chunks_to_index = db.query(DocumentChunk).filter(DocumentChunk.embedding == None).all()
        total_chunks = len(chunks_to_index)
        
        if total_chunks == 0:
            print("All document chunks are already indexed. Nothing to do!")
            return

        print(f"Found {total_chunks} chunks that require indexing.")
        print(f"Embedding Provider: {settings.EMBEDDING_PROVIDER}")
        print(f"Embedding Model: {settings.EMBEDDING_MODEL}")
        print(f"Embedding Dimension: {settings.EMBEDDING_DIMENSION}")

        if settings.EMBEDDING_PROVIDER != "local":
            print(f"Error: Embedding provider '{settings.EMBEDDING_PROVIDER}' is not supported locally. Please set EMBEDDING_PROVIDER=local in your environment to build indexes offline.")
            return

        print("Loading SentenceTransformer model...")
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(settings.EMBEDDING_MODEL)

        # Generate and save embeddings in batches
        processed = 0
        for i in range(0, total_chunks, args.batch_size):
            batch = chunks_to_index[i:i + args.batch_size]
            texts = [c.chunk_text for c in batch]
            
            # Encode texts using local embedding model
            embeddings = model.encode(texts, show_progress_bar=False)
            
            for chunk, emb in zip(batch, embeddings):
                chunk.embedding = emb.tolist()
            
            db.commit()
            processed += len(batch)
            print(f"  Processed {processed}/{total_chunks} chunks...")

        print("\nIndexing completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"\nAn error occurred during indexing: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    main()
