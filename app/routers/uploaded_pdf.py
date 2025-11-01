from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer
from typing import List, Dict, Tuple
from fastapi import APIRouter
import faiss
import os
import pandas as pd
import numpy as np
import io
import pdfplumber

router = APIRouter(prefix="/pdfData", tags=["pdfData"])

# ---------- CONFIG ----------
modelName = "sentence-transformers/all-MiniLM-L6-v2"
model = SentenceTransformer(modelName)
CHUNK_SIZE_TOKENS = 400
CHUNK_OVERLAP_TOKENS = 64
EMBED_DIM = 384

# ---------- Utilities ----------
tokenizer = AutoTokenizer.from_pretrained(modelName)

# ========= Your existing function =========
def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    """Extract text from PDF bytes using pdfplumber."""
    text_chunks = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            txt = page.extract_text()
            if txt:
                text_chunks.append(txt)
    return "\n".join(text_chunks)

# ========= Supabase Setup =========
def initialize_supabase():
    """Initialize Supabase client using environment variables or constants."""
    SUPABASE_URL = "https://rhihmakcvscsodsbmrej.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJoaWhtYWtjdnNjc29kc2JtcmVqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE3MTY2NjQsImV4cCI6MjA3NzI5MjY2NH0.HoGQ-mM1gpoY9c6-MG9-1hlrij-myENqyb8jDkhIcnM"

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase


# ========= Fetch and Extract Function =========
def fetch_pdf_and_extract(pdf_name: str):
    """
    Fetch a PDF file from a given folder in Supabase Storage
    and extract its text using pdfplumber.
    """
    supabase = initialize_supabase()
    bucket_name = "Pdfs"  # change this to your bucket name

    # Download the file
    response = supabase.storage.from_(bucket_name).download(pdf_name)

    if not response:
        print(f"File not found: {pdf_name}")
        return None

    # Extract text from bytes
    pdf_bytes = response
    extracted_text = extract_text_from_pdf_bytes(pdf_bytes)

    print(f"Successfully extracted text from {pdf_name}")
    return extracted_text

def chunk_text_token_level(text: str, chunk_size: int = CHUNK_SIZE_TOKENS, overlap: int = CHUNK_OVERLAP_TOKENS) -> List[Tuple[str,int,int]]:
    """
    Returns list of tuples: (chunk_text, start_token_idx, end_token_idx)
    Uses tokenizer.encode(add_special_tokens=False) so chunks are decoded back to text.
    """
    token_ids = tokenizer.encode(text, add_special_tokens=False)
    chunks = []
    if len(token_ids) == 0:
        return chunks
    step = chunk_size - overlap
    for start in range(0, max(1, len(token_ids)), step):
        end = start + chunk_size
        chunk_tokens = token_ids[start:end]
        # decode back to text; keep it safe by ignoring special tokens cleanup
        chunk_text = tokenizer.decode(chunk_tokens, clean_up_tokenization_spaces=True)
        chunks.append((chunk_text, start, min(end, len(token_ids))))
        if end >= len(token_ids):
            break
    return chunks

# ---------- Build FAISS index and metadata store ----------
def build_or_load_faiss(index_path: str, dim: int = EMBED_DIM):
    if index_path and os.path.exists(index_path):
        idx = faiss.read_index(index_path)
    else:
        idx = faiss.IndexFlatL2(dim)  # use L2 
    return idx

def save_faiss_and_metadata(index, index_path: str, metadata: List[Dict], meta_path: str):
    faiss.write_index(index, index_path)
    pd.DataFrame(metadata).to_parquet(meta_path, index=False)

def load_metadata(meta_path: str) -> List[Dict]:
    if not os.path.exists(meta_path):
        return []  # Return empty list if file does not exist
    return pd.read_parquet(meta_path).to_dict(orient="records")

# ---------- Pipeline: ingest docs to FAISS ----------
def ingest_documents_to_faiss(docs: List[Dict], index, metadata_store: List[Dict], persist_every: int = 1000):
    """
    docs: list of {"id","name","mimeType","text"}
    index: faiss index
    metadata_store: list to append chunk metadata
    returns index, metadata_store
    """
    all_chunk_texts = []
    meta_batch = []
    for doc in docs:
        doc_id = doc.get("id")
        name = doc.get("name")
        text = doc.get("text", "")
        if not text or len(text.strip()) == 0:
            continue
        chunks = chunk_text_token_level(text, chunk_size=CHUNK_SIZE_TOKENS, overlap=CHUNK_OVERLAP_TOKENS)
        for i, (c_text, start_t, end_t) in enumerate(chunks):
            chunk_id = f"{doc_id}__{i}"
            meta = {
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "source_name": name,
                "mimeType": doc.get("mimeType"),
                "start_token": int(start_t),
                "end_token": int(end_t),
                "text": c_text
            }
            meta_batch.append(meta)
            all_chunk_texts.append(c_text)
    if not all_chunk_texts:
        return index, metadata_store
    # create embeddings in batches for memory control
    B = 64
    embeddings_list = []
    for i in range(0, len(all_chunk_texts), B):
        batch_texts = all_chunk_texts[i:i+B]
        embs = model.encode(batch_texts, convert_to_numpy=True, show_progress_bar=False)
        embeddings_list.append(embs)
    embeddings = np.vstack(embeddings_list)
    embeddings = embeddings.astype("float32")
    index.add(embeddings)
    metadata_store.extend(meta_batch)
    return index, metadata_store

@router.post("/")
def fetch_data(pdf_file: str):

    text = fetch_pdf_and_extract(pdf_file)
    INDEX_PATH = "../database/faiss_index.bin"
    META_PATH = "../database/metadata.parquet"
    index = build_or_load_faiss(INDEX_PATH, EMBED_DIM)
    metadata_store = load_metadata(META_PATH)

    index, metadata_store = ingest_documents_to_faiss(text, index, metadata_store)

    # Persist
    save_faiss_and_metadata(index, INDEX_PATH, metadata_store, META_PATH)
    return {"message": "Ingest complete. total chunks in metadata:", "total_chunks": len(metadata_store)}