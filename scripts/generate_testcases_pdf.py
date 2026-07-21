import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# Define NumberedCanvas for professional page headers and footers
class NumberedCanvas(canvas.Canvas):
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
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (drawn on pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 755, "MEDRAG DECISION SUPPORT - SYSTEM VERIFICATION TEST CASES")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, 748, 558, 748)
        
        # Footer (drawn on all pages)
        self.setFont("Helvetica", 8)
        self.drawString(54, 30, "Disclaimer: For evaluation and validation purposes only. Not for clinical diagnostic use.")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 30, page_text)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 42, 558, 42)
        
        self.restoreState()

# Clinical test cases content data
TEST_CASES = [
    {
        "id": "TC-001",
        "title": "Renal Contraindication (Metformin)",
        "query": "Can a patient with diabetes and severe renal impairment take Metformin?",
        "context": {
            "Age": "62 years",
            "Sex": "Male",
            "Conditions": "Type 2 Diabetes, Chronic Kidney Disease (CKD)",
            "eGFR": "25 mL/min/1.73m² (Severe Impairment)",
            "Current Medications": "None",
            "Known Allergies": "None"
        },
        "expected_synthesis": "Metformin is strictly contraindicated in this patient. FDA regulations and clinical guidelines specify that Metformin must not be initiated or continued in patients with an eGFR below 30 mL/min/1.73m² due to the significant risk of drug accumulation and associated Lactic Acidosis (a rare but potentially fatal metabolic complication).",
        "key_citations": [
            "Metformin FDA Label - Contraindications Section (eGFR < 30)",
            "Diabetes Clinical Guidelines (Recommendation to discontinue Metformin)"
        ]
    },
    {
        "id": "TC-002",
        "title": "Pregnancy Safety Warning (Losartan)",
        "query": "Is Losartan safe to control high blood pressure in a pregnant patient?",
        "context": {
            "Age": "29 years",
            "Sex": "Female",
            "Conditions": "Essential Hypertension",
            "Pregnancy Status": "Pregnant (2nd Trimester)",
            "Current Medications": "None",
            "Known Allergies": "None"
        },
        "expected_synthesis": "Losartan is contraindicated. Angiotensin II Receptor Blockers (ARBs) carry a Boxed Warning for fetal toxicity. Exposure during the second and third trimesters of pregnancy reduces fetal renal function and increases fetal/neonatal morbidity and death.",
        "key_citations": [
            "Losartan FDA Label - Boxed Warning: Fetal Toxicity",
            "Hypertension Guidelines - Pregnant patients should be switched to safe alternatives (e.g. Methyldopa, Labetalol, Nifedipine)"
        ]
    },
    {
        "id": "TC-003",
        "title": "Dual RAAS Blockade Interaction",
        "query": "Can a patient take Lisinopril and Losartan together to manage high blood pressure?",
        "context": {
            "Age": "55 years",
            "Sex": "Male",
            "Conditions": "Hypertension",
            "Current Medications": "Lisinopril 20mg daily",
            "Known Allergies": "None",
            "Other Details": "Adding Losartan 50mg daily"
        },
        "expected_synthesis": "Dual blockade of the renin-angiotensin-aldosterone system (RAAS) by combining an ACE inhibitor (Lisinopril) and an ARB (Losartan) is not recommended. Clinical studies show no additional therapeutic benefit, but significantly higher rates of hypotension, hyperkalemia, and acute kidney injury.",
        "key_citations": [
            "Lisinopril and Losartan FDA Labels - Drug Interactions Section",
            "Hypertension Guidelines - Recommendation against combining ACEi and ARB therapy"
        ]
    },
    {
        "id": "TC-004",
        "title": "Ethambutol Visual Toxicity & Monitoring",
        "query": "What is the main side effect associated with Ethambutol and what checkups are needed?",
        "context": {
            "Age": "45 years",
            "Sex": "Female",
            "Conditions": "Active Tuberculosis (Pulmonary TB)",
            "Current Medications": "RIPE regimen (Rifampicin, Isoniazid, Pyrazinamide, Ethambutol)",
            "Known Allergies": "None"
        },
        "expected_synthesis": "The primary serious side effect of Ethambutol is Optic Neuritis, which causes decreased visual acuity and red-green color blindness. Patients must undergo baseline and periodic visual testing (Snellen chart and Ishihara color plates) during treatment.",
        "key_citations": [
            "Ethambutol FDA Label - Warnings & Precautions (Visual Acuity)",
            "Tuberculosis Clinical Guidelines - Monitoring parameters for active pulmonary TB"
        ]
    },
    {
        "id": "TC-005",
        "title": "First-Line Hypertension Guidelines",
        "query": "What are the first-line drug choices recommended for newly diagnosed Hypertension?",
        "context": {
            "Age": "50 years",
            "Sex": "Male",
            "Conditions": "Essential Hypertension",
            "Current Medications": "None (Treatment naive)",
            "Known Allergies": "None"
        },
        "expected_synthesis": "First-line pharmacotherapy options include four classes: Thiazide Diuretics (e.g. Chlorthalidone, Hydrochlorothiazide), Calcium Channel Blockers (CCBs, e.g. Amlodipine), ACE Inhibitors (ACEi, e.g. Lisinopril), or Angiotensin Receptor Blockers (ARBs, e.g. Losartan). Selection should account for ethnicity, comorbidities, and age.",
        "key_citations": [
            "Hypertension Clinical Practice Guidelines (First-line Recommendations)",
            "Amlodipine, Lisinopril, Losartan, Chlorthalidone FDA Labels"
        ]
    }
]

def build_pdf(filename: str):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=5
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        spaceAfter=15
    )
    
    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6
    )
    
    header_cell_style = ParagraphStyle(
        'HeaderCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white
    )
    
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#334155")
    )
    
    bold_cell_style = ParagraphStyle(
        'BoldCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0F172A")
    )

    story = []
    
    # Title & Introduction
    story.append(Paragraph("MedRAG System Verification Test Cases", title_style))
    story.append(Paragraph("A standardized set of verification cases including patient profile inputs and expected evidence-based clinical outputs.", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Overview Table
    story.append(Paragraph("I. Summary Table of Test Cases", h1_style))
    
    table_data = [[
        Paragraph("ID", header_cell_style),
        Paragraph("Test Case Title", header_cell_style),
        Paragraph("Target Clinical Query", header_cell_style),
        Paragraph("Primary Evidence Source", header_cell_style)
    ]]
    
    for tc in TEST_CASES:
        source_name = "DailyMed / FDA Label" if "TC-002" in tc["id"] or "TC-001" in tc["id"] or "TC-003" in tc["id"] else "Clinical Guidelines"
        table_data.append([
            Paragraph(tc["id"], bold_cell_style),
            Paragraph(tc["title"], bold_cell_style),
            Paragraph(tc["query"], table_cell_style),
            Paragraph(source_name, table_cell_style)
        ])
        
    t = Table(table_data, colWidths=[50, 130, 200, 124])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")])
    ]))
    story.append(t)
    story.append(Spacer(1, 15))
    
    # Detailed Test Cases
    story.append(Paragraph("II. Detailed Patient Profiles & Expected Outputs", h1_style))
    
    for tc in TEST_CASES:
        story.append(Spacer(1, 5))
        story.append(Paragraph(f"<b>{tc['id']}: {tc['title']}</b>", ParagraphStyle('TCTitle', parent=h1_style, textColor=colors.HexColor("#1E40AF"), spaceBefore=8)))
        
        # Query box
        story.append(Paragraph(f"<b>Clinical Query:</b> <i>\"{tc['query']}\"</i>", body_style))
        
        # Context Table
        ctx_data = [[Paragraph("Patient Context Parameter", header_cell_style), Paragraph("Input Context Value", header_cell_style)]]
        for k, v in tc["context"].items():
            ctx_data.append([Paragraph(k, bold_cell_style), Paragraph(v, table_cell_style)])
            
        ctx_table = Table(ctx_data, colWidths=[150, 354])
        ctx_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#475569")),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")])
        ]))
        story.append(ctx_table)
        story.append(Spacer(1, 6))
        
        # Expected outputs & Citations
        story.append(Paragraph(f"<b>Expected Output Summary:</b> {tc['expected_synthesis']}", body_style))
        
        cits_str = "<b>Expected Reference Citations to look for:</b><br/>"
        for i, cit in enumerate(tc["key_citations"]):
            cits_str += f"{i+1}. {cit}<br/>"
        story.append(Paragraph(cits_str, ParagraphStyle('TCCitations', parent=body_style, leftIndent=15)))
        story.append(Spacer(1, 8))
        story.append(Paragraph("<font color='#CBD5E1'>__________________________________________________________________________________________</font>", body_style))
        
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully built: {filename}")

if __name__ == "__main__":
    output_filename = "clinical_test_cases.pdf"
    if len(sys.argv) > 1:
        output_filename = sys.argv[1]
    build_pdf(output_filename)
