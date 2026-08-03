import streamlit as st
from groq import Groq
from .prompt_templates import PDPA_SYSTEM_PROMPT

class LlamaPDPAAuditor:
    def __init__(self):
        # Securely fetch the API key from Streamlit Community Cloud secrets
        self.client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    def generate_audit_report(self, scan_results):
        # Convert the dataframe findings into a string for the LLM
        scan_summary = scan_results.to_string(index=False)
        
        # Request the audit report from Groq's Llama 3.1 model
        response = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": PDPA_SYSTEM_PROMPT},
                {"role": "user", "content": f"Scan Results:\n{scan_summary}"}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
