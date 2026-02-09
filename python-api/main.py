from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os

from supabase import create_client
from transformers import pipeline


# CARGA DE VARIABLES DE ENTORNO

load_dotenv()


# FASTAPI

app = FastAPI(title="AI Support Co-Pilot")


# SUPABASE

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# MODELO IA (CLASIFICACIÓN)

classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli"
)

CATEGORIES = ["Tecnico", "Facturacion", "Comercial"]
SENTIMENTS = ["Positivo", "Neutral", "Negativo"]

# SCHEMA

class TicketRequest(BaseModel):
    ticket_id: str
    description: str


# ENDPOINT PRINCIPAL

@app.post("/process-ticket")
def process_ticket(payload: TicketRequest):
    try:
        # Clasificar categoría
        category_result = classifier(
            payload.description,
            candidate_labels=CATEGORIES
        )

        # Clasificar sentimiento
        sentiment_result = classifier(
            payload.description,
            candidate_labels=SENTIMENTS
        )

        category = category_result["labels"][0]
        sentiment = sentiment_result["labels"][0]

        # Actualizar Supabase
        supabase.table("tickets").update({
            "category": category,
            "sentiment": sentiment,
            "processed": True
        }).eq("id", payload.ticket_id).execute()

        return {
            "ticket_id": payload.ticket_id,
            "category": category,
            "sentiment": sentiment,
            "processed": True,
            "status": "success"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando ticket: {str(e)}"
        )


# HEALTH CHECK

@app.get("/")
def health_check():
    return {
        "status": "online",
        "model": "facebook/bart-large-mnli"
    }
