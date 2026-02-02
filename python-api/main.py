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

# 1. CARGA DE VARIABLES DE ENTORNO
load_dotenv()

# 2. CONFIGURACIÓN DE FASTAPI
app = FastAPI(title="AI Support Co-Pilot")

# 3. CLIENTE SUPABASE
# Asegúrate de que estas variables estén en tu archivo .env o en el Dashboard de Render
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# 4. CONFIGURACIÓN DEL MODELO HUGGING FACE
# Usamos Flan-T5-base. Nota: En Render Free (512MB RAM) este modelo puede dar error de memoria.
hf_pipeline = pipeline(
    "text2text-generation",
    model="google/flan-t5-base",
    max_length=128,
    temperature=0
)

llm = HuggingFacePipeline(pipeline=hf_pipeline)

# 5. TEMPLATE DEL PROMPT
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

# 6. SCHEMAS DE PYDANTIC
class TicketRequest(BaseModel):
    ticket_id: str
    description: str

# 7. FUNCIÓN DE EXTRACCIÓN ROBUSTA (EL CORAZÓN DE LA SOLUCIÓN)
def extract_json(text: str) -> dict:
    """
    Intenta extraer JSON de la respuesta del LLM. 
    Si falla el parseo directo, intenta recuperar los campos con Regex.
    """
    try:
        # Limpieza básica de saltos de línea y espacios
        clean_text = text.replace("\\n", "").replace("\n", "").strip()
        
        # Intento 1: Buscar contenido entre llaves { }
        match = re.search(r"\{.*\}", clean_text, re.DOTALL)
        if match:
            return json.loads(match.group())
        
        # Intento 2: Si el modelo no puso llaves, buscar patrones clave:valor
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

# 8. ENDPOINT PRINCIPAL
@app.post("/process-ticket")
def process_ticket(payload: TicketRequest):
    try:
        # Formatear el prompt con el contenido del ticket
        formatted_prompt = prompt_template.format(ticket=payload.description)
        
        # Invocar al modelo
        result = llm.invoke(formatted_prompt)

        # Asegurar que el resultado sea un string procesable
        if hasattr(result, "content"):
            result_str = result.content
        else:
            result_str = str(result)

        # Extraer la data (aquí es donde fallaba antes)
        parsed = extract_json(result_str)

        category = parsed.get("category", "Tecnico")
        sentiment = parsed.get("sentiment", "Neutral")

        # 9. ACTUALIZAR EN SUPABASE
        # Importante: Asegúrate de que la tabla se llame 'tickets' y el ID coincida
        supabase.table("tickets").update({
            "category": category,
            "sentiment": sentiment,
            "processed": True
        }).eq("id", payload.ticket_id).execute()

        # 10. RESPUESTA EXITOSA
        return {
            "ticket_id": payload.ticket_id,
            "category": category,
            "sentiment": sentiment,
            "status": "success",
            "processed": True
        }

    except ValueError as ve:
        # Errores de parseo del modelo
        raise HTTPException(status_code=422, detail=str(ve))
    
    except Exception as e:
        # Errores generales (Supabase, Memoria, etc)
        print(f"Error crítico: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# Healthcheck para Render
@app.get("/")
def health_check():
    return {"status": "online", "model": "flan-t5-base"}