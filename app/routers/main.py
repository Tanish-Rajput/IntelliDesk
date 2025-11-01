import faiss
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from fastapi import APIRouter
from agno.agent import Agent 
from agno.models.google import Gemini

load_dotenv()

router = APIRouter(prefix="/queries", tags=["main"])

gemini_model = Gemini()

assistant = Agent(model=gemini_model)

# Constants
INDEX_PATH = "../database/faiss_index.bin"
META_PATH = "../database/metadata.parquet"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Load model once
model = SentenceTransformer(MODEL_NAME)

def load_faiss_index(index_path: str = INDEX_PATH):
    """Load FAISS index from disk if exists, else raise error."""
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Index file not found: {index_path}")
    index = faiss.read_index(index_path)
    return index

def load_metadata(meta_path: str = META_PATH):
    """Load stored metadata from parquet file."""
    if not os.path.exists(meta_path):
        raise FileNotFoundError(f"Metadata file not found: {meta_path}")
    df = pd.read_parquet(meta_path)
    return df

def search_query(query: str, top_k: int = 2):
    """
    Search the FAISS index using a natural language query.
    Returns top_k relevant chunks with metadata.
    """
    # Load index + metadata
    index = load_faiss_index()
    df_meta = load_metadata()

    # Encode query
    query_emb = model.encode([query], convert_to_numpy=True).astype("float32")

    # Search in FAISS
    distances, indices = index.search(query_emb, top_k)

    # Get top results
    results = []
    for idx, dist in zip(indices[0], distances[0]):
        if idx < len(df_meta):
            row = df_meta.iloc[idx].to_dict()
            row["score"] = float(dist)
            results.append(f"{row}")
    return results

def compose_prompt(query: str, retrieved_chunks: list) -> str:
    context_text = "\n\n".join(retrieved_chunks)
    prompt = f"""You are an advanced AI assistant developed by Tanish Raghav. 
This system is part of a project built by Tanish to demonstrate his expertise in AI and LLM-based application development. 
The goal of this application is to provide companies with a personalized AI system that can understand and respond using their own internal data and documents — securely connected through sources like Google Drive, Notion, or uploaded PDFs.

Your role is to analyze the provided context and answer the users query accurately. 
All data used here is securely handled and remains private.

Context:
{context_text}

Question:
{query}

Provide a complete, clear, and easy-to-understand response in under 300 to 350 words.
"""
    return prompt

@router.post("/")
def answer_query(q: str) -> str:

    search = search_query(q)
    prompt = compose_prompt(q, search)
    answer = assistant.run(prompt)
    return answer.content   