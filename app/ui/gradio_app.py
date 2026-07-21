import sys
import os
import gradio as gr
from typing import Tuple, Optional

# Add root folder to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.db.session import SessionLocal
from app.api.routes import ask_question, submit_feedback
from app.models.requests import QueryRequest, PatientContext, PatientRenal, FeedbackRequest
from app.config import settings

DISCLAIMER = """
⚠️ **Disclaimer:** This application provides evidence-based drug information for research and clinical decision support. 
It does not diagnose conditions, prescribe treatment, replace official drug labeling, or replace a licensed healthcare professional. 
Do not start, stop, substitute, or change the dose of a medicine based only on this system. 
For emergencies or severe symptoms, contact local emergency services immediately.
"""

def handle_query(
    question: str,
    age: Optional[float],
    sex: str,
    comorbidities: str,
    meds: str,
    allergies: str,
    egfr: Optional[float]
) -> Tuple[str, str, str, str, str, str, str, str, str, str, str]:
    if not question.strip():
        return "Please enter a clinical query.", "", "", "", "", "", "", "", "", "", ""
        
    db = SessionLocal()
    try:
        # Build patient context
        conditions_list = [c.strip() for c in comorbidities.split(",") if c.strip()]
        meds_list = [m.strip() for m in meds.split(",") if m.strip()]
        allergies_list = [a.strip() for a in allergies.split(",") if a.strip()]
        
        renal_ctx = None
        if egfr is not None:
            renal_ctx = PatientRenal(egfr=egfr)
            
        patient_ctx = PatientContext(
            age=int(age) if age else None,
            sex=sex if sex != "N/A" else None,
            conditions=conditions_list,
            current_medications=meds_list,
            allergies=allergies_list,
            renal=renal_ctx
        )
        
        req = QueryRequest(
            question=question,
            patient_context=patient_ctx
        )
        
        # Execute query using consolidated backend endpoint
        res = ask_question(req, db)
        
        # Format outputs
        summary_md = f"### Summary Answer\n{res.summary}"
        
        drug_info_md = f"""### Drug Profile
- **Generic Name:** {res.drug_information.generic_name or 'N/A'}
- **Brand Names:** {', '.join(res.drug_information.brand_names) if res.drug_information.brand_names else 'N/A'}
- **Drug Class:** {res.drug_information.drug_class or 'N/A'}
- **Active Ingredients:** {', '.join(res.drug_information.active_ingredients) if res.drug_information.active_ingredients else 'N/A'}
- **Mechanism of Action:** {res.drug_information.mechanism or 'N/A'}"""

        indications_md = f"""### Indications
#### Approved
{chr(10).join([f'- {ind}' for ind in res.indications.approved]) if res.indications.approved else 'No approved indications documented.'}

#### Off-Label (Evidence Grounded)
{chr(10).join([f'- {ind}' for ind in res.indications.off_label_with_evidence]) if res.indications.off_label_with_evidence else 'No off-label uses documented.'}"""

        considerations_md = f"""### Patient Specific Considerations
- **Age Adjustments:** {', '.join(res.patient_considerations.age) if res.patient_considerations.age else 'None'}
- **Pregnancy & Lactation:** {', '.join(res.patient_considerations.pregnancy) if res.patient_considerations.pregnancy else 'None'}
- **Renal Adjustments:** {', '.join(res.patient_considerations.renal) if res.patient_considerations.renal else 'None'}
- **Hepatic Adjustments:** {', '.join(res.patient_considerations.hepatic) if res.patient_considerations.hepatic else 'None'}
- **Allergies/Sensitivities:** {', '.join(res.patient_considerations.allergies) if res.patient_considerations.allergies else 'None'}
- **Comorbidities:** {', '.join(res.patient_considerations.comorbidities) if res.patient_considerations.comorbidities else 'None'}"""

        safety_md = f"""### Safety, Warnings & Contraindications
#### Absolute Contraindications
{chr(10).join([f'- {c}' for c in res.contraindications]) if res.contraindications else 'No absolute contraindications listed.'}

#### Warnings & Precautions
{chr(10).join([f'- {w}' for w in res.warnings]) if res.warnings else 'No warnings listed.'}"""

        side_effects_md = f"""### Side Effects / Adverse Reactions
#### Common
{chr(10).join([f'- {se}' for se in res.side_effects.common]) if res.side_effects.common else 'None listed.'}

#### Serious
{chr(10).join([f'- {se}' for se in res.side_effects.serious]) if res.side_effects.serious else 'None listed.'}"""

        timeline_md = f"""### Treatment Timeline & Monitoring
- **Expected Onset:** {res.treatment_timeline.expected_onset or 'N/A'}
- **Reassessment Period:** {res.treatment_timeline.reassessment_period or 'N/A'}
- **Typical Duration:** {res.treatment_timeline.typical_duration or 'N/A'}
- **Onset Limitations:** {res.treatment_timeline.limitations or 'N/A'}

#### Recommended Monitoring
{chr(10).join([f'- {m}' for m in res.monitoring]) if res.monitoring else 'No specific monitoring listed.'}"""

        alternatives_md = f"""### Therapeutic Alternatives
- **Generic Equivalents:** {', '.join(res.alternatives.generic_equivalents) if res.alternatives.generic_equivalents else 'None'}
- **Same-Class Options:** {', '.join(res.alternatives.same_class) if res.alternatives.same_class else 'None'}
- **Other Guideline Options:** {', '.join(res.alternatives.other_guideline_supported_options) if res.alternatives.other_guideline_supported_options else 'None'}"""

        indicators_md = f"""### Evidence & Consensus Indicators
- **Evidence Quality Score:** `{res.evidence_indicators.evidence_quality.upper()}`
- **Population Similarity Match:** `{res.evidence_indicators.population_match.upper()}`
- **Evidence Consensus/Agreement:** `{res.evidence_indicators.source_agreement.upper()}`
- **Retrieval Completeness:** `{res.evidence_indicators.answer_completeness.upper()}`"""

        evidence_md = "### Retrieved Evidence Citations\n"
        for i, cit in enumerate(res.citations):
            evidence_md += f"""\n**[{i+1}] {cit.claim_text}**
- *Source Passage:* "{cit.source_passage}"
- *Entailment:* {cit.entailment_status} (Score: {cit.verification_score})
---\n"""
        if not res.citations:
            evidence_md += "No retrieved guidelines or drug labels were linked to the response claims."

        return (
            str(res.query_id),
            summary_md,
            drug_info_md,
            indications_md,
            considerations_md,
            safety_md,
            side_effects_md,
            timeline_md,
            alternatives_md,
            indicators_md,
            evidence_md
        )
    except Exception as e:
        print(f"Error handling Gradio query: {e}")
        return f"Error occurred: {e}", "", "", "", "", "", "", "", "", "", ""
    finally:
        db.close()

def handle_feedback(query_id: str, rating: str, quality: str, comment: str) -> str:
    if not query_id:
        return "⚠️ Please perform a search query before submitting feedback."
    
    db = SessionLocal()
    try:
        req = FeedbackRequest(
            query_id=query_id,
            rating=rating.lower(),
            citation_quality=quality.lower(),
            comment=comment
        )
        submit_feedback(req, db)
        return "✅ Feedback submitted successfully! Thank you."
    except Exception as e:
        return f"⚠️ Error submitting feedback: {e}"
    finally:
        db.close()

# Define Gradio Theme & Interface
theme = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="slate",
    neutral_hue="slate",
).set(
    body_background_fill="*neutral_50",
    block_background_fill="white",
    block_border_width="1px",
)

with gr.Blocks(theme=theme, title="MedRAG Assistant") as demo:
    gr.Markdown("# ⚕️ Adaptive Medical RAG\n### Clinician Drug Information & Decision-Support Assistant")
    
    query_id_state = gr.State("")

    with gr.Row():
        # Input parameters (Left panel)
        with gr.Column(scale=1):
            gr.Markdown("### 1. Clinical Query & Patient Profile")
            question_input = gr.Textbox(
                label="Clinical Question",
                placeholder="e.g., Can a patient with CKD and diabetes take Metformin?",
                lines=3
            )
            
            with gr.Accordion("Patient Context Variables (Optional)", open=True):
                age_input = gr.Number(label="Age (Years)", value=None, precision=0)
                sex_input = gr.Dropdown(label="Sex", choices=["N/A", "Male", "Female", "Other"], value="N/A")
                comorbidities_input = gr.Textbox(
                    label="Comorbidities",
                    placeholder="e.g., hypertension, chronic kidney disease",
                )
                meds_input = gr.Textbox(
                    label="Current Medications",
                    placeholder="e.g., Lisinopril, Aspirin",
                )
                allergies_input = gr.Textbox(
                    label="Known Drug Allergies",
                    placeholder="e.g., Penicillin",
                )
                egfr_input = gr.Number(label="Renal eGFR (mL/min/1.73m²)", value=None, precision=1)
                
            submit_btn = gr.Button("Analyze & Retrieve Evidence", variant="primary")
            
        # Outputs (Right panel)
        with gr.Column(scale=2):
            gr.Markdown("### 2. Evidence Synthesis")
            
            with gr.Tabs():
                with gr.TabItem("📋 Synthesis Summary"):
                    summary_out = gr.Markdown(value="Enter a query on the left to synthesize clinical evidence.")
                    
                    with gr.Row():
                        with gr.Column():
                            drug_info_out = gr.Markdown()
                            indications_out = gr.Markdown()
                        with gr.Column():
                            safety_out = gr.Markdown()
                            side_effects_out = gr.Markdown()
                            
                with gr.TabItem("📖 Clinical Details"):
                    with gr.Row():
                        with gr.Column():
                            considerations_out = gr.Markdown()
                            timeline_out = gr.Markdown()
                        with gr.Column():
                            alternatives_out = gr.Markdown()
                            indicators_out = gr.Markdown()
                            
                with gr.TabItem("🔍 Retrieved Passages & Citations"):
                    evidence_out = gr.Markdown()
                    
                with gr.TabItem("✍️ Feedback & Quality Review"):
                    gr.Markdown("#### Help us improve. Rate the synthesized clinical response:")
                    rating_input = gr.Radio(label="Overall Rating", choices=["Helpful", "Unhelpful"], value="Helpful")
                    quality_input = gr.Radio(label="Citation Accuracy Check", choices=["Correct", "Hallucination", "Missing"], value="Correct")
                    comment_input = gr.Textbox(label="Clinical Comments / Corrections", placeholder="Describe any inaccuracies or suggestions...", lines=3)
                    feedback_btn = gr.Button("Submit Review", variant="secondary")
                    feedback_status = gr.Markdown()

    gr.Markdown(DISCLAIMER)

    # Click triggers
    submit_btn.click(
        fn=handle_query,
        inputs=[
            question_input,
            age_input,
            sex_input,
            comorbidities_input,
            meds_input,
            allergies_input,
            egfr_input
        ],
        outputs=[
            query_id_state,
            summary_out,
            drug_info_out,
            indications_out,
            considerations_out,
            safety_out,
            side_effects_out,
            timeline_out,
            alternatives_out,
            indicators_out,
            evidence_out
        ]
    )

    feedback_btn.click(
        fn=handle_feedback,
        inputs=[
            query_id_state,
            rating_input,
            quality_input,
            comment_input
        ],
        outputs=feedback_status
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=settings.GRADIO_PORT)
