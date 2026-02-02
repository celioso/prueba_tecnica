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

# CARGA DE VARIABLES DE ENTORNO
load_dotenv()

# CONFIGURACIÓN DE FASTAPI
app = FastAPI(title="AI Support Co-Pilot")

# CLIENTE SUPABASE
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# CONFIGURACIÓN DEL MODELO HUGGING FACE

hf_pipeline = pipeline(
    "text2text-generation",
    model="google/flan-t5-base",
    max_length=128,
    temperature=0
)

llm = HuggingFacePipeline(pipeline=hf_pipeline)

# TEMPLATE DEL PROMPT
prompt_template = PromptTemplate(
    input_variables=["ticket"],
    template="""
Return ONLY valid JSON with this exact structure:
{{
    "category": "Tecnico | Facturacion | Comercial",
    "sentiment": "Positivo | Neutral | Negativo"
}}

Ticket:
"{ticket}"
"""
)

# SCHEMAS DE PYDANTIC
class TicketRequest(BaseModel):
    ticket_id: str
    description: str

def extract_json(text: str) -> dict:
    """
    Intenta extraer JSON de la respuesta del LLM. 
    Si falla el parseo directo, intenta recuperar los campos con Regex.
    """
    try:
        clean_text = text.replace("\\n", "").replace("\n", "").strip()
        
        match = re.search(r"\{.*\}", clean_text, re.DOTALL)
        if match:
            return json.loads(match.group())
        
        category_match = re.search(r'"category":\s*"([^"]+)"', clean_text, re.IGNORECASE)
        sentiment_match = re.search(r'"sentiment":\s*"([^"]+)"', clean_text, re.IGNORECASE)
        
        if category_match and sentiment_match:
            return {
                "category": category_match.group(1).strip(),
                "sentiment": sentiment_match.group(1).strip()
            }
        
        raise ValueError("Formato de respuesta no reconocido")
        
    except Exception as e:
        print(f"Error parseando JSON: {text}")
        raise ValueError(f"No se pudo procesar la respuesta del modelo: {str(e)}")

@app.post("/process-ticket")
def process_ticket(payload: TicketRequest):
    try:
        formatted_prompt = prompt_template.format(ticket=payload.description)
        
        result = llm.invoke(formatted_prompt)

        if hasattr(result, "content"):
            result_str = result.content
        else:
            result_str = str(result)

        parsed = extract_json(result_str)

        category = parsed.get("category", "Tecnico")
        sentiment = parsed.get("sentiment", "Neutral")

        supabase.table("tickets").update({
            "category": category,
            "sentiment": sentiment,
            "processed": True
        }).eq("id", payload.ticket_id).execute()

        return {
            "ticket_id": payload.ticket_id,
            "category": category,
            "sentiment": sentiment,
            "status": "success",
            "processed": True
        }

    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    
    except Exception as e:
        print(f"Error crítico: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/")
def health_check():
    return {"status": "online", "model": "flan-t5-base"}