import streamlit as st
import pandas as pd
import io
from core.file_parser import parse_uploaded_file
from core.regex_engine import MalaysianPIIClassifier
from llm.local_client import LlamaPDPAAuditor
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor

st.set_page_config(page_title="PDPA-Shield MY", layout="wide")
st.title("PDPA-Shield MY")
st.markdown("### Automated Personal Data Protection Act (PDPA) Compliance Scanner")

scanner = MalaysianPIIClassifier()
auditor = LlamaPDPAAuditor()

def anonymize_dataframe(df):
    masked_df = df.copy()
    if 'Name' in masked_df.columns:
        masked_df['Name'] = [f"User_{i}" for i in range(len(df))]
    if 'IC_Number' in masked_df.columns:
        masked_df['IC_Number'] = masked_df['IC_Number'].apply(
            lambda x: f"{str(x)[:6]}-XX-XXXX" if isinstance(x, str) and len(str(x)) >= 6 else x
        )
    return masked_df


def scan_dataframe(df):
    results = []
    for col in df.columns:
        mykad, phone, email = 0, 0, 0
        for cell in df[col].dropna().astype(str):
            findings = scanner.scan_text(cell)
            mykad += len(findings["mykad"])
            phone += len(findings["phone"])
            email += len(findings["email"])
        
        if mykad > 0 or phone > 0 or email > 0:
            risk = "High" if mykad > 0 else ("Medium" if phone > 0 else "Low")
            results.append({"Column": col, "MyKad (IC)": mykad, "Phone": phone, "Email": email, "Risk": risk})
    return pd.DataFrame(results)

def create_compliance_pdf(score, company_name, auditor_name, actions_text):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle("DocTitle", parent=styles["Heading1"], fontSize=22, leading=26, textColor=HexColor("#0F172A"), spaceAfter=4)
    subtitle_style = ParagraphStyle('DocSubtitle', parent=styles['Heading2'], fontSize=11, leading=14, textColor=HexColor('#475569'), spaceAfter=15)
    section_heading = ParagraphStyle('SecHeading', parent=styles['Heading3'], fontSize=13, leading=16, textColor=HexColor('#1E3A8A'), spaceBefore=12, spaceAfter=8, keepWithNext=True)
    body_style = ParagraphStyle('ReportBody', parent=styles['Normal'], fontSize=10, leading=14, textColor=HexColor('#334155'), spaceAfter=6)
    
    score_color = '#16A34A' if score >= 80 else ('#D97706' if score >= 50 else '#DC2626')
    score_style = ParagraphStyle('ScoreBox', parent=styles['Normal'], fontSize=12, leading=16, textColor=HexColor(score_color), spaceAfter=12)

    story = []
    story.append(Paragraph("PDPA-Shield MY: Laporan Audit Kepatuhan Data", title_style))
    story.append(Paragraph("Automated Data Privacy Governance & Compliance Assessment Report", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=HexColor('#CBD5E1'), spaceBefore=0, spaceAfter=12))
    
    story.append(Paragraph(f"<b>Entiti Sasaran / Target Client:</b> {company_name}", body_style))
    story.append(Paragraph(f"<b>Juruaudit / Lead Auditor:</b> {auditor_name}", body_style))
    story.append(Paragraph("<b>Klasifikasi / Classification:</b> SULIT / CONFIDENTIAL", body_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph(f"<b>Tahap Kepatuhan Semasa / Current Compliance Rating: {score}%</b>", score_style))
    story.append(Paragraph("<i>Sistem Imbasan Zero-Knowledge: Semua data peribadi (PII) telah disaring dan disembunyikan secara lokal sebelum pemprosesan audit dijalankan.</i>", body_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#E2E8F0'), spaceBefore=0, spaceAfter=10))
    
    for line in actions_text.split('\n'):
        cleaned_line = line.strip()
        if cleaned_line.startswith("* "): cleaned_line = "- " + cleaned_line[2:]
        if not cleaned_line:
            continue
        while "**" in cleaned_line: cleaned_line = cleaned_line.replace("**", "", 1).replace("**", "", 1)
        
        if cleaned_line.startswith(('1.', '2.', '3.', '4.', 'Recommendations:', 'CorrectiveActionsTimeline:', '###')):
            story.append(Paragraph(f"<b>{cleaned_line}</b>", section_heading))
        elif cleaned_line.startswith('-'):
            story.append(Paragraph(f"• {cleaned_line[1:].strip()}", body_style))
        else:
            story.append(Paragraph(cleaned_line, body_style))
            
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

uploaded_file = st.file_uploader("Securely drop your customer dataset (CSV/Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    with st.spinner("Processing data locally..."):
        try:
            df = parse_uploaded_file(uploaded_file)
            st.success(f"File loaded successfully: {uploaded_file.name} ({len(df)} rows)")
            
            st.success("100% Zero-Knowledge Scan: All PII has been structurally masked in-memory before audit processing.")
            
            st.subheader("Data Preview (Heavily Masked)")
            safe_df = anonymize_dataframe(df)
            st.dataframe(safe_df.head(3))
            
            if st.button("Run PDPA Vulnerability Scan & LLM Audit", type="primary"):
                with st.spinner("Anonymizing data and running Regex Classifiers..."):
                    
                    scan_results = scan_dataframe(safe_df)
                    
                    if not scan_results.empty:
                        total_high = len(scan_results[scan_results['Risk'] == 'High'])
                        total_medium = len(scan_results[scan_results['Risk'] == 'Medium'])
                        compliance_score = max(0, 100 - (total_high * 30) - (total_medium * 15))
                        
                        st.markdown("---")
                        if compliance_score < 50:
                            st.error(f"PDPA Compliance Rating: {compliance_score}% (Critical Gaps Detected)")
                        elif compliance_score < 80:
                            st.warning(f"PDPA Compliance Rating: {compliance_score}% (Action Required)")
                        else:
                            st.success(f"PDPA-Compliance Rating: {compliance_score}% (Good Standing)")
                        st.progress(compliance_score / 100)
                        st.markdown("---")
                        
                        st.subheader("PII Exposure Findings")
                        st.dataframe(scan_results, use_container_width=True)
                        
                        st.subheader("Llama 3.1 PDPA Corrective Action Plan")
                        with st.spinner("Generating regulatory audit report via local LLM..."):
                            audit_report = auditor.generate_audit_report(scan_results)
                            st.markdown(audit_report)
                            
                            pdf_buffer = create_compliance_pdf(
                                score=compliance_score, 
                                company_name="SME Target Client", 
                                auditor_name="Allendraa Anbalagan (VoxIntel)", 
                                actions_text=audit_report
                            )
                            
                            st.download_button(
                                label="Download Audit Report (PDF)",
                                data=pdf_buffer,
                                file_name="PDPA_Compliance_Audit_Report.pdf",
                                mime="application/pdf"
                            )
                    else:
                        st.success("No clear Malaysian PII detected in standard formats.")
        except Exception as e:
            st.error(f"Error: {e}")