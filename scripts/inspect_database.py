import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add root folder to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings
from app.models.database import Base, Document, DocumentChunk, Disease, Drug

def inspect_db():
    print("====================================================")
    print("       MEDRAG DATABASE INSPECTOR & VISUALIZER       ")
    print("====================================================")
    print(f"Active Connection: {settings.DATABASE_URL}")
    print("----------------------------------------------------\n")
    
    # Establish connection
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Inspect Diseases
        diseases = session.query(Disease).all()
        print(f"Diseases Monitored ({len(diseases)} total):")
        for d in diseases:
            print(f"  - {d.name}")
        print()
        
        # 2. Inspect Drugs
        drugs = session.query(Drug).all()
        print(f"Ingested Drugs ({len(drugs)} total):")
        drug_names = [f"{dr.generic_name} ({dr.drug_class or 'Unclassified'})" for dr in drugs]
        print("  " + ", ".join(drug_names[:15]) + ("..." if len(drugs) > 15 else ""))
        print()

        # 3. Inspect Documents (Guidelines & FDA labels)
        docs = session.query(Document).all()
        print(f"Ingested PDF Documents ({len(docs)} total):")
        for doc in docs[:10]:
            print(f"  - [{doc.evidence_type.upper() if doc.evidence_type else 'UNKNOWN'}] {doc.title[:45]}... (Path: {os.path.basename(doc.file_path) if doc.file_path else 'N/A'})")
        if len(docs) > 10:
            print(f"  ... and {len(docs) - 10} more documents.")
        print()

        # 4. Inspect Document Chunks and Vector Embeddings
        total_chunks = session.query(DocumentChunk).count()
        print(f"Indexed Chunks ({total_chunks} total):")
        
        # Pull a sample chunk to display the text and vector coordinates
        sample_chunk = session.query(DocumentChunk).filter(DocumentChunk.embedding != None).first()
        if sample_chunk:
            print("  --- Sample Chunk Preview ---")
            print(f"  Document ID: {sample_chunk.document_id}")
            print(f"  Chunk ID: {sample_chunk.id}")
            print(f"  Clinical Section: {sample_chunk.clinical_section}")
            print(f"  Page Number: {sample_chunk.metadata_json.get('page_number', 'N/A')}")
            
            # Print text snippet
            text_snippet = sample_chunk.chunk_text.strip().replace("\n", " ")
            print(f"  Text Snippet: \"{text_snippet[:150]}...\"")
            
            # Print vector coordinates
            vector = sample_chunk.embedding
            # If SQLite, the vector is stored as a list (via custom type)
            if isinstance(vector, list):
                vector_coords = vector
            else:
                # pgvector returns it as a list/numpy array depending on driver
                vector_coords = list(vector) if vector is not None else []
                
            print(f"  Embedding Vector Dimension: {len(vector_coords)}")
            print(f"  Vector Coordinates (first 10 components): {vector_coords[:10]}")
            print("  ----------------------------")
        else:
            print("  [Warning] No document chunks with vector embeddings found in the database. Please run scripts/create_indexes.py first.")
            
    except Exception as e:
        print(f"Error querying database: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    inspect_db()
