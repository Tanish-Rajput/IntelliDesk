import faiss
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from fastapi import APIRouter
from agno.agent import Agent
from agno.models.google import Gemini
from global_resources import model, faiss_index, metadata_df  # ✅ Global imports
from pydantic import BaseModel
from fastapi.responses import JSONResponse

load_dotenv()

router = APIRouter(prefix="/queries", tags=["main"])

gemini_model = Gemini()
assistant = Agent(model=gemini_model)

# Constants
INDEX_PATH = "../database/faiss_index.bin"
META_PATH = "../database/metadata.parquet"

class QueryInput(BaseModel):
    q: str

def load_faiss_index():
    """Return the global FAISS index (no local load)."""
    return faiss_index  # ✅ Use shared FAISS index

def load_metadata():
    """Return the global metadata dataframe."""
    return metadata_df  # ✅ Use shared metadata

def search_query(query: str, top_k: int = 2):
    """
    Search the FAISS index using a natural language query.
    Returns top_k relevant chunks with metadata.
    """
    # Use global resources
    index = load_faiss_index()
    df_meta = load_metadata()

    # Encode query using global model
    query_emb = model.encode([query], convert_to_numpy=True).astype("float32")

    # Search in FAISS
    distances, indices = index.search(query_emb, top_k)

    # Get top results
    results = []
    if len(df_meta) == 0:
        return results

    for idx, dist in zip(indices[0], distances[0]):
        if 0 <= idx < len(df_meta):  # ✅ safe index check
            row = df_meta.iloc[idx].to_dict()
            row["score"] = float(dist)
            results.append(f"{row}")

    return results 

def compose_prompt(query: str, retrieved_chunks: list) -> str:
    context_text = "\n\n".join(retrieved_chunks)
    prompt = f"""You are an advanced AI assistant developed by Tanish Raghav. 
This system is part of a project built by Tanish to demonstrate his expertise in AI and LLM-based application development. 
The goal of this application is to provide companies with a personalized AI system that can understand and respond using their own internal data and documents — securely connected through sources like Google Drive, Notion, or uploaded PDFs.

Your role is to analyze the provided context and answer the user's query accurately. 
All data used here is securely handled and remains private.

Context:
{context_text}

Question:
{query}

Provide a complete, clear, easy-to-understand and CONCISE response 
"""
    return prompt

@router.post("/")
def answer_query(data: QueryInput) -> str:
    q = data.q
    search = search_query(q)
    prompt = compose_prompt(q, search)
    answer = assistant.run(prompt)
    return JSONResponse(content={"answer": answer.content})
