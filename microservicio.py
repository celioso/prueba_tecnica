from fastapi import FastAPI
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import os

app = FastAPI()

class TicketInput(BaseModel):
    id: str
    description: str

class TicketAnalysis(BaseModel):
    category: str
    sentiment: str

@app.post("/process-ticket")
async def process_ticket(ticket: TicketInput):
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    
    prompt = ChatPromptTemplate.from_template(
        "Analiza el siguiente ticket de soporte y clasifícalo.\n"
        "Categorías: Técnico, Facturación, Comercial.\n"
        "Sentimiento: Positivo, Neutral, Negativo.\n"
        "Formato de respuesta: JSON con llaves 'category' y 'sentiment'.\n"
        "Ticket: {text}"
    )

    chain = prompt | llm | JsonOutputParser()
    result = chain.invoke({"text": ticket.description})
    
    return {"status": "success", "data": result}