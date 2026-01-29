from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import json
import re

from supabase import create_client
from langchain_core.prompts import PromptTemplate
from langchain_community.llms import HuggingFacePipeline
from transformers import pipeline

# ENV
load_dotenv()


# APP

app = FastAPI(title="AI Support Co-Pilot")


# SUPABASE

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# HUGGING FACE MODEL
hf_pipeline = pipeline(
    "text2text-generation",
    model="google/flan-t5-base",
    max_length=128,
    temperature=0
)

llm = HuggingFacePipeline(pipeline=hf_pipeline)

# PROMPT
prompt = PromptTemplate(
    input_variables=["ticket"],
    template="""
Return ONLY valid JSON with this exact structure:

{
    "category": "Tecnico | Facturacion | Comercial",
    "sentiment": "Positivo | Neutral | Negativo"
}

Ticket:
"{ticket}"
"""
)

# SCHEMAS
class TicketRequest(BaseModel):
    ticket_id: str
    description: str

# Clean the LLM response

def extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in LLM response")
    return json.loads(match.group())


# ENDPOINT
@app.post("/process-ticket")
def process_ticket(payload: TicketRequest):
    try:
        formatted_prompt = prompt.format(ticket=payload.description)
        result = llm.invoke(formatted_prompt)

        if hasattr(result, "content"):
            result = result.content

        parsed = extract_json(result)

        category = parsed.get("category")
        sentiment = parsed.get("sentiment")

        if not category or not sentiment:
            raise HTTPException(
                status_code=422,
                detail="LLM response missing required fields"
            )

        supabase.table("tickets").update({
            "category": category,
            "sentiment": sentiment,
            "processed": True
        }).eq("id", payload.ticket_id).execute()

        return {
            "ticket_id": payload.ticket_id,
            "category": category,
            "sentiment": sentiment,
            "processed": True
        }

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="LLM returned invalid JSON"
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))