import sys
import os
import json
import argparse
from datetime import datetime

# Add root folder to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.models.database import Source, Document, DocumentChunk, Drug, Disease, DrugDiseaseRelation
from app.ingestion.parsers.pdf_parser import PDFParser
from app.ingestion.section_chunker import SectionChunker

# Title-casing mapping for disease keys
DISEASE_NAMES = {
    "asthma": "Asthma",
    "copd": "COPD",
    "diabetes": "Diabetes",
    "hypertension": "Hypertension",
    "tuberculosis": "Tuberculosis"
}

def find_drug_labels_dir(disease_dir: str) -> str:
    if not os.path.exists(disease_dir):
        return None
    for name in os.listdir(disease_dir):
        if name.lower() == "drug labels":
            return os.path.join(disease_dir, name)
    return None

def main():
    parser = argparse.ArgumentParser(description="Ingest guidelines and drug labels into the MedRAG database.")
    parser.add_argument("--source", type=str, choices=["guidelines", "dailymed", "all"], default="all",
                        help="Select which source files to ingest.")
    args = parser.parse_args()

    # Load diseases.json
    diseases_json_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "../medical_data/diseases.json"))
    if not os.path.exists(diseases_json_path):
        print(f"Error: diseases.json not found at {diseases_json_path}")
        return

    with open(diseases_json_path, "r") as f:
        data = json.load(f)

    db = SessionLocal()
    try:
        # 1. Create or retrieve Sources
        guideline_source = db.query(Source).filter(Source.name == "Clinical Guidelines").first()
        if not guideline_source:
            guideline_source = Source(
                name="Clinical Guidelines",
                source_type="clinical_guideline",
                authority_score=1.0,
                metadata_json={"description": "Official diagnostic and clinical treatment guidelines."}
            )
            db.add(guideline_source)
            db.commit()
            db.refresh(guideline_source)

        dailymed_source = db.query(Source).filter(Source.name == "DailyMed").first()
        if not dailymed_source:
            dailymed_source = Source(
                name="DailyMed",
                source_type="regulatory_label",
                authority_score=1.0,
                metadata_json={"description": "FDA official drug labeling and package inserts."}
            )
            db.add(dailymed_source)
            db.commit()
            db.refresh(dailymed_source)

        # 2. Iterate through diseases in JSON
        for disease_key, info in data.items():
            disease_name = DISEASE_NAMES.get(disease_key, disease_key.capitalize())
            print(f"\nProcessing disease: {disease_name}")

            # Get or create Disease
            disease = db.query(Disease).filter(Disease.name == disease_name).first()
            if not disease:
                disease = Disease(name=disease_name)
                db.add(disease)
                db.commit()
                db.refresh(disease)

            # --- INGEST GUIDELINES ---
            if args.source in ["guidelines", "all"]:
                guideline_filename = info.get("guideline")
                disease_dir_name = os.path.normpath(os.path.join(os.path.dirname(__file__), "../medical_data", disease_name))
                guideline_path = os.path.join(disease_dir_name, guideline_filename)
                
                if os.path.exists(guideline_path):
                    # Check if document already exists
                    doc = db.query(Document).filter(Document.file_path == guideline_path).first()
                    if not doc:
                        print(f"  Ingesting Guideline: {guideline_filename}")
                        pages = PDFParser.extract_pages(guideline_path)
                        
                        doc = Document(
                            source_id=guideline_source.id,
                            title=f"{disease_name} Clinical Guideline",
                            evidence_type="guideline",
                            evidence_level="authoritative",
                            file_path=guideline_path,
                            jurisdiction="Global" if disease_name != "Hypertension" else "US",
                            publication_date=datetime.strptime("2015-01-01", "%Y-%m-%d").date() if "2015" in guideline_filename else datetime.strptime("2024-01-01", "%Y-%m-%d").date(),
                        )
                        db.add(doc)
                        db.commit()
                        db.refresh(doc)

                        # Chunk and save
                        chunks = SectionChunker.chunk_guideline(pages)
                        for chunk in chunks:
                            db_chunk = DocumentChunk(
                                document_id=doc.id,
                                chunk_text=chunk["chunk_text"],
                                clinical_section=chunk["clinical_section"],
                                metadata_json={"page_number": chunk["page_number"]}
                            )
                            db.add(db_chunk)
                        db.commit()
                        print(f"    Saved {len(chunks)} chunks.")
                    else:
                        print(f"  Guideline already exists: {guideline_filename}")
                else:
                    print(f"  Warning: Guideline file not found at {guideline_path}")

            # --- INGEST DRUG LABELS ---
            if args.source in ["dailymed", "all"]:
                drug_names = info.get("drugs", [])
                disease_dir_name = os.path.normpath(os.path.join(os.path.dirname(__file__), "../medical_data", disease_name))
                drug_labels_dir = find_drug_labels_dir(disease_dir_name)
                
                if drug_labels_dir and os.path.exists(drug_labels_dir):
                    for drug_name in drug_names:
                        drug_pdf_filename = f"{drug_name}.pdf"
                        drug_pdf_path = os.path.join(drug_labels_dir, drug_pdf_filename)
                        
                        # Case-insensitive matching for filenames
                        if not os.path.exists(drug_pdf_path):
                            found = False
                            for filename in os.listdir(drug_labels_dir):
                                if filename.lower() == drug_pdf_filename.lower():
                                    drug_pdf_path = os.path.join(drug_labels_dir, filename)
                                    found = True
                                    break
                            if not found:
                                print(f"  Warning: Drug label file not found for {drug_name} at {drug_pdf_path}")
                                continue

                        # Get or create Drug
                        drug = db.query(Drug).filter(Drug.generic_name == drug_name).first()
                        if not drug:
                            drug = Drug(
                                generic_name=drug_name,
                                brand_names=[],
                                active_ingredients=[drug_name]
                            )
                            db.add(drug)
                            db.commit()
                            db.refresh(drug)

                        # Ingest label as Document
                        doc = db.query(Document).filter(Document.file_path == drug_pdf_path).first()
                        if not doc:
                            print(f"  Ingesting Drug Label: {os.path.basename(drug_pdf_path)}")
                            pages = PDFParser.extract_pages(drug_pdf_path)
                            doc = Document(
                                source_id=dailymed_source.id,
                                title=f"{drug_name} FDA Official Label",
                                evidence_type="regulatory_label",
                                evidence_level="authoritative",
                                file_path=drug_pdf_path,
                                jurisdiction="US"
                            )
                            db.add(doc)
                            db.commit()
                            db.refresh(doc)

                            # Chunk and save
                            chunks = SectionChunker.chunk_drug_label(pages)
                            for chunk in chunks:
                                db_chunk = DocumentChunk(
                                    document_id=doc.id,
                                    chunk_text=chunk["chunk_text"],
                                    clinical_section=chunk["clinical_section"],
                                    metadata_json={"page_number": chunk["page_number"]}
                                )
                                db.add(db_chunk)
                            db.commit()
                            print(f"    Saved {len(chunks)} chunks.")
                        else:
                            print(f"  Drug label already exists: {os.path.basename(drug_pdf_path)}")

                        # Link Drug and Disease
                        relation = db.query(DrugDiseaseRelation).filter(
                            DrugDiseaseRelation.drug_id == drug.id,
                            DrugDiseaseRelation.disease_id == disease.id,
                            DrugDiseaseRelation.relation_type == "indication"
                        ).first()
                        if not relation:
                            relation = DrugDiseaseRelation(
                                drug_id=drug.id,
                                disease_id=disease.id,
                                relation_type="indication",
                                evidence_description=f"Indicated for the treatment of {disease_name}.",
                                document_id=doc.id
                            )
                            db.add(relation)
                            db.commit()
                else:
                    print(f"  Warning: Drug labels directory not found for {disease_name}")

        print("\nIngestion completed successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    main()
