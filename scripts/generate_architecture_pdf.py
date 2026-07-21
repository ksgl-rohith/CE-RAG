import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# Define Page Number Canvas for professional headers/footers
class ArchitectureDocCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))
        
        # Header (drawn on pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 755, "MEDRAG CLINICAL DECISION SUPPORT - ARCHITECTURE & WORKFLOW MANUAL")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 748, 558, 748)
        
        # Footer (drawn on all pages)
        self.setFont("Helvetica", 8)
        self.drawString(54, 30, "Adaptive & Iterative Medical RAG - Technical Documentation")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 30, page_text)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 42, 558, 42)
        
        self.restoreState()

def build_architecture_pdf(filename: str):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#475569"),
        spaceAfter=15
    )
    
    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1E40AF"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6
    )
    
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    code_box_style = ParagraphStyle(
        'CodeBox',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#0F172A"),
        backColor=colors.HexColor("#F1F5F9"),
        borderColor=colors.HexColor("#CBD5E1"),
        borderWidth=0.5,
        borderPadding=6,
        spaceAfter=8
    )
    
    header_cell_style = ParagraphStyle(
        'HeaderCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white
    )
    
    cell_style = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#334155")
    )
    
    cell_bold_style = ParagraphStyle(
        'CellBold',
        parent=cell_style,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor("#0F172A")
    )

    story = []
    
    # ---------------------------------------------------------
    # COVER / HEADER
    # ---------------------------------------------------------
    story.append(Paragraph("Adaptive Medical RAG Assistant", title_style))
    story.append(Paragraph("System Architecture, End-to-End Workflow, Data Pipeline & Key Functionalities Guide", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A"), spaceAfter=15))
    
    # ---------------------------------------------------------
    # SECTION 1: EXECUTIVE OVERVIEW
    # ---------------------------------------------------------
    story.append(Paragraph("1. Executive Overview & System Goals", h1_style))
    story.append(Paragraph(
        "The <b>Adaptive Medical RAG Assistant</b> is an evidence-based clinical decision support system designed to assist healthcare professionals with drug information, dosing adjustments, safety contraindications, and therapeutic alternatives. Traditional LLMs are prone to medical hallucinations; MedRAG mitigates this risk by grounding responses exclusively in authoritative clinical guidelines (e.g., GINA, GOLD, ADA, JNC) and official FDA prescribing labels (DailyMed).",
        body_style
    ))
    story.append(Paragraph("<b>Core Capabilities:</b>", body_style))
    story.append(Paragraph("• <b>Evidence Grounding:</b> Generates structured clinical responses linked to exact document text passages and page numbers.", bullet_style))
    story.append(Paragraph("• <b>Patient-Specific Contextual Analysis:</b> Factors in patient age, renal function (eGFR), pregnancy status, comorbidities, and current medications.", bullet_style))
    story.append(Paragraph("• <b>Hybrid Retrieval Engine:</b> Combines dense vector semantics with sparse full-text lexical search using Reciprocal Rank Fusion (RRF).", bullet_style))
    story.append(Paragraph("• <b>Dual-Database Support:</b> Runs seamlessly on high-performance PostgreSQL (pgvector) or zero-config local SQLite.", bullet_style))
    story.append(Paragraph("• <b>Feedback & Audit Trail:</b> Logs all queries, patient parameters, retrieved evidence, and clinician ratings for audit compliance.", bullet_style))
    story.append(Spacer(1, 10))
    
    # ---------------------------------------------------------
    # SECTION 2: SYSTEM ARCHITECTURE
    # ---------------------------------------------------------
    story.append(Paragraph("2. System Architecture & Component Layers", h1_style))
    story.append(Paragraph(
        "The application is structured into six modular layers, enforcing clean separation between ingestion, storage, retrieval, synthesis, and UI representation:",
        body_style
    ))
    
    arch_table_data = [
        [Paragraph("Layer", header_cell_style), Paragraph("Component Modules", header_cell_style), Paragraph("Primary Functionality", header_cell_style)],
        [
            Paragraph("Presentation Layer", cell_bold_style),
            Paragraph("app/ui/gradio_app.py", cell_style),
            Paragraph("Dual-panel clinician portal (Gradio Blocks) with forms for patient context, tabbed clinical summaries, citations, and feedback forms.", cell_style)
        ],
        [
            Paragraph("API Service Layer", cell_bold_style),
            Paragraph("app/main.py<br/>app/api/routes.py", cell_style),
            Paragraph("FastAPI web service exposing endpoints (/health, /query, /evidence, /feedback) with Pydantic contract validation.", cell_style)
        ],
        [
            Paragraph("LLM Synthesis Layer", cell_bold_style),
            Paragraph("app/models/requests.py<br/>app/models/responses.py", cell_style),
            Paragraph("Constructs RAG prompts with JSON Mode enforcement (GPT-4o-mini / Gemini), resolving numeric chunk indexes to verified database UUIDs.", cell_style)
        ],
        [
            Paragraph("Hybrid Retrieval Engine", cell_bold_style),
            Paragraph("app/retrieval/dense_retriever.py<br/>app/retrieval/sparse_retriever.py<br/>app/retrieval/hybrid_fusion.py", cell_style),
            Paragraph("Performs parallel dense vector search (cosine distance) and sparse lexical search (FTS / ts_rank), merging ranks via Reciprocal Rank Fusion (RRF).", cell_style)
        ],
        [
            Paragraph("Ingestion Pipeline", cell_bold_style),
            Paragraph("app/ingestion/parsers/pdf_parser.py<br/>app/ingestion/section_chunker.py<br/>scripts/ingest_sources.py", cell_style),
            Paragraph("Parses raw PDF files, scrubs NUL bytes, segments FDA labels into regulatory sections (warnings, contraindications, dosage), and chunks guidelines.", cell_style)
        ],
        [
            Paragraph("Storage & Database Layer", cell_bold_style),
            Paragraph("app/models/database.py<br/>app/db/session.py<br/>app/config.py", cell_style),
            Paragraph("SQLAlchemy ORM models backing PostgreSQL (pgvector) and SQLite. Stores sources, documents, chunks, drugs, diseases, query logs, and audit trails.", cell_style)
        ]
    ]
    
    arch_table = Table(arch_table_data, colWidths=[110, 140, 254])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")])
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 12))
    
    # ---------------------------------------------------------
    # SECTION 3: END-TO-END WORKFLOW
    # ---------------------------------------------------------
    story.append(Paragraph("3. End-to-End Information Processing Workflow", h1_style))
    story.append(Paragraph("The system operates in two main operational phases:", body_style))
    
    story.append(Paragraph("Phase A: Ingestion & Indexing Pipeline (Offline Batch Processing)", h2_style))
    story.append(Paragraph("1. <b>PDF Text Extraction:</b> `PDFParser` reads raw PDF documents page-by-page and strips illegal NUL (`0x00`) characters to prevent database errors.", bullet_style))
    story.append(Paragraph("2. <b>Regulatory Section Chunking:</b> `SectionChunker` uses regular expressions to detect standard FDA sections (<i>INDICATIONS, CONTRAINDICATIONS, WARNINGS, ADVERSE REACTIONS, DRUG INTERACTIONS, DOSAGE</i>) or page blocks for guidelines.", bullet_style))
    story.append(Paragraph("3. <b>Database Storage:</b> Saves source metadata, documents, and individual text chunks to the database.", bullet_style))
    story.append(Paragraph("4. <b>Vector Embedding Generation:</b> `create_indexes.py` computes 384-dimensional dense embeddings (`all-MiniLM-L6-v2`) or 1536-dimensional embeddings (`text-embedding-3-small`) and saves coordinates into `document_chunks.embedding`.", bullet_style))
    story.append(Spacer(1, 4))
    
    story.append(Paragraph("Phase B: Clinical Query & RAG Synthesis Workflow (Real-Time)", h2_style))
    story.append(Paragraph("1. <b>User Query & Context Submission:</b> Clinician enters a query (e.g. <i>\"Can a patient with severe renal impairment take Metformin?\"</i>) along with patient age, eGFR, comorbidities, and medications via Gradio UI or REST API.", bullet_style))
    story.append(Paragraph("2. <b>Dense Semantic Search:</b> Vectorizes the question and queries `DocumentChunk.embedding` using PostgreSQL `<=>` cosine distance.", bullet_style))
    story.append(Paragraph("3. <b>Sparse Lexical Search:</b> Converts question into text search vectors (`to_tsquery`) and ranks matches using PostgreSQL `ts_rank`.", bullet_style))
    story.append(Paragraph("4. <b>Hybrid Rank Fusion (RRF):</b> Merges dense and sparse result sets using Reciprocal Rank Fusion: <i>RRF_score = Σ 1 / (60 + rank)</i>.", bullet_style))
    story.append(Paragraph("5. <b>Contextual Prompt Construction:</b> Assembles top candidate evidence chunks with chunk index numbers into a structured prompt.", bullet_style))
    story.append(Paragraph("6. <b>JSON Mode LLM Generation:</b> Queries GPT-4o-mini / Gemini using `response_format={'type': 'json_object'}`, enforcing a strict clinical schema.", bullet_style))
    story.append(Paragraph("7. <b>Citation Resolution & Audit Logging:</b> Maps numeric `chunk_index` values in citations back to verified database chunk UUIDs and source passages. Writes query log and audit trail to database.", bullet_style))
    story.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # SECTION 4: HYBRID RETRIEVAL SUBSYSTEM
    # ---------------------------------------------------------
    story.append(Paragraph("4. Hybrid Evidence Retrieval & RRF Reranking Algorithm", h1_style))
    story.append(Paragraph(
        "RAG applications relying solely on vector embeddings often miss exact drug name matches or specific numerical dosages. Conversely, keyword search fails on complex semantic phrasing. MedRAG combines both approaches:",
        body_style
    ))
    
    retrieval_box = """<b>Reciprocal Rank Fusion (RRF) Formula:</b><br/>
For each document chunk <i>d</i> appearing in the retrieved sets <i>R_dense</i> and <i>R_sparse</i>:<br/>
<b>RRF_Score(d) = (1 / (k + Rank_dense(d))) + (1 / (k + Rank_sparse(d)))</b><br/>
<i>Where constant k = 60 (standard RRF smoothing factor).</i>
"""
    story.append(Paragraph(retrieval_box, code_box_style))
    story.append(Paragraph("<b>Dialect Portability:</b> When running on PostgreSQL, `DenseRetriever` uses native `pgvector` cosine distance and `SparseRetriever` uses PostgreSQL Full-Text Search. When running on SQLite, fallback mechanisms use tokenized case-insensitive substring matching and metadata filters.", body_style))
    story.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # SECTION 5: API REST CONTRACT & RESPONSE SCHEMA
    # ---------------------------------------------------------
    story.append(Paragraph("5. REST API Endpoints & Response Schema Contract", h1_style))
    story.append(Paragraph("The FastAPI backend (`app/api/routes.py`) provides the following endpoints:", body_style))
    
    api_table_data = [
        [Paragraph("HTTP Method & Endpoint", header_cell_style), Paragraph("Input Payload / Params", header_cell_style), Paragraph("Description & Output", header_cell_style)],
        [
            Paragraph("GET /health", cell_bold_style),
            Paragraph("None", cell_style),
            Paragraph("Returns API operational status, server timestamp, app name, and environment.", cell_style)
        ],
        [
            Paragraph("POST /api/v1/query", cell_bold_style),
            Paragraph("QueryRequest JSON (question, patient_context, jurisdiction)", cell_style),
            Paragraph("Executes RAG search, generates structured QueryResponse JSON, and records QueryLog + AuditLog entries.", cell_style)
        ],
        [
            Paragraph("GET /api/v1/query/{id}/evidence", cell_bold_style),
            Paragraph("query_id (UUID string)", cell_style),
            Paragraph("Retrieves all underlying document text chunks, page numbers, and section labels linked to a query.", cell_style)
        ],
        [
            Paragraph("POST /api/v1/feedback", cell_bold_style),
            Paragraph("FeedbackRequest JSON (query_id, rating, citation_quality, comment)", cell_style),
            Paragraph("Logs clinician evaluation ratings (helpful/unhelpful) and comments into Feedback database table.", cell_style)
        ]
    ]
    
    api_table = Table(api_table_data, colWidths=[130, 150, 224])
    api_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")])
    ]))
    story.append(api_table)
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Structured Response Contract (QueryResponse JSON):", h2_style))
    story.append(Paragraph("1. <b>summary:</b> Direct 1-2 sentence clinical answer.", bullet_style))
    story.append(Paragraph("2. <b>drug_information:</b> Generic name, brand names, class, active ingredients, mechanism.", bullet_style))
    story.append(Paragraph("3. <b>indications:</b> Approved indications vs. evidence-supported off-label uses.", bullet_style))
    story.append(Paragraph("4. <b>patient_considerations:</b> Age, pregnancy/lactation, renal, hepatic, allergies, comorbidities.", bullet_style))
    story.append(Paragraph("5. <b>contraindications & warnings:</b> Absolute contraindications and FDA boxed warnings.", bullet_style))
    story.append(Paragraph("6. <b>side_effects:</b> Common vs. serious adverse reactions.", bullet_style))
    story.append(Paragraph("7. <b>treatment_timeline & monitoring:</b> Expected onset, reassessment period, and required lab monitoring.", bullet_style))
    story.append(Paragraph("8. <b>alternatives:</b> Generic equivalents, same-class options, and guideline-supported options.", bullet_style))
    story.append(Paragraph("9. <b>evidence_indicators:</b> Evidence quality score, population match, source agreement, completeness.", bullet_style))
    story.append(Paragraph("10. <b>citations:</b> List of claims linked to exact chunk IDs, passages, and document URLs.", bullet_style))
    story.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # SECTION 6: HOW TO RUN & VERIFY
    # ---------------------------------------------------------
    story.append(Paragraph("6. System Execution & Operational Commands", h1_style))
    story.append(Paragraph("To start the system locally, execute the following commands in order:", body_style))
    
    cmd_text = """# Step 1: Boot up PostgreSQL + pgvector Docker container
docker compose up -d

# Step 2: Run Alembic database migrations
.venv\\Scripts\\alembic upgrade head

# Step 3: Parse PDF guidelines and drug labels into database
.venv\\Scripts\\python scripts/ingest_sources.py

# Step 4: Calculate vector embeddings & create pgvector index
.venv\\Scripts\\python scripts/create_indexes.py

# Step 5: Launch FastAPI Backend Service
.venv\\Scripts\\python app/main.py

# Step 6: Launch Gradio Clinician Web Interface (http://localhost:7860)
.venv\\Scripts\\python app/ui/gradio_app.py
"""
    story.append(Paragraph(cmd_text.replace("\n", "<br/>"), code_box_style))
    story.append(Spacer(1, 10))
    
    # Inspection command
    story.append(Paragraph("<b>Database Verification:</b> You can verify database tables, chunk counts, and raw vector coordinates at any time by running:", body_style))
    story.append(Paragraph(".venv\\Scripts\\python scripts/inspect_database.py", code_box_style))

    doc.build(story, canvasmaker=ArchitectureDocCanvas)
    print(f"Architecture PDF successfully built: {filename}")

if __name__ == "__main__":
    out_file = "MedRAG_Architecture_and_Workflow.pdf"
    if len(sys.argv) > 1:
        out_file = sys.argv[1]
    build_architecture_pdf(out_file)
