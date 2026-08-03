import re
from typing import List, Dict

class MalaysianPIIClassifier:
    def __init__(self):
        self.mykad_pattern = re.compile(r"\b(?:[0-9]{2})(?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[0-1])(?:-?)(?:\d{2})(?:-?)(?:\d{4})\b")
        self.phone_pattern = re.compile(r"\b(?:\+?60|0)[1-9]\d{1,2}(?:-?|\s?)\d{3,4}(?:-?|\s?)\d{4}\b")
        self.email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")

    def scan_text(self, text: str) -> Dict[str, List[str]]:
        if not isinstance(text, str): return {"mykad": [], "phone": [], "email": []}
        return {
            "mykad": self.mykad_pattern.findall(text),
            "phone": self.phone_pattern.findall(text),
            "email": self.email_pattern.findall(text)
        }

    def mask_pii(self, text: str) -> str:
        if not isinstance(text, str): return text
        m = self.mykad_pattern.sub(lambda x: "*" * 8 + x.group(0)[-4:], text)
        m = self.phone_pattern.sub(lambda x: "*" * (len(x.group(0)) - 4) + x.group(0)[-4:], m)
        return m