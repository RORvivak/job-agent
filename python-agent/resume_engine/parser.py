import json
from pathlib import Path
from langchain_core.messages import SystemMessage, HumanMessage

from prompts.resume_prompt import PARSE_RESUME_SYSTEM
from services.llm_limiter import get_llm, llm_guarded


def extract_text(path: str) -> str:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    elif suffix in (".docx", ".doc"):
        import docx2txt
        return docx2txt.process(path)
    raise ValueError(f"Unsupported file type: {suffix}")


def parse(path: str) -> dict:
    text = extract_text(path)
    llm = get_llm()
    messages = [
        SystemMessage(content=PARSE_RESUME_SYSTEM),
        HumanMessage(content=f"Parse this resume:\n\n{text[:8000]}"),
    ]
    response = llm.invoke(messages)
    try:
        return json.loads(response.content)
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{.*\}", response.content, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"raw_text": text, "parse_error": True}
