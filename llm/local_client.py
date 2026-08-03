from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from llm.prompt_templates import PDPA_SYSTEM_PROMPT

class LlamaPDPAAuditor:
    def __init__(self, model_name="llama3.1"):
        self.llm = Ollama(model=model_name)
        self.prompt = PromptTemplate(
            input_variables=["scan_summary"],
            template=PDPA_SYSTEM_PROMPT
        )
        self.chain = self.prompt | self.llm

    def generate_audit_report(self, scan_summary_df):
        summary_text = scan_summary_df.to_markdown(index=False)
        try:
            response = self.chain.invoke({"scan_summary": summary_text})
            return response
        except Exception as e:
            return f"LLM Connection Error: Ensure Ollama is running. Details: {str(e)}"