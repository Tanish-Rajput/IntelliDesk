# app/global_resources.py

from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer
import faiss
import pandas as pd
import os

INDEX_PATH = "/database/faiss_index.bin"
META_PATH = "/database/metadata.parquet"

# ---------- Configuration ----------
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE_TOKENS = 400
CHUNK_OVERLAP_TOKENS = 64
EMBED_DIM = 384

model = None
tokenizer = None
faiss_index = None
metadata_df = None


def load_resources():
    global model, tokenizer, faiss_index, metadata_df

    print("Initializing global resources...")

    if model is None:
        print("🔹 Loading SentenceTransformer model...")
        model = SentenceTransformer(MODEL_NAME)
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        print("Model and tokenizer loaded successfully.")

    if os.path.exists(INDEX_PATH):
        print("🔹 Loading FAISS index...")
        faiss_index = faiss.read_index(INDEX_PATH)
    else:
        print("⚠️ No FAISS index found; initializing empty index")
        faiss_index = faiss.IndexFlatL2(384)

    if os.path.exists(META_PATH):
        print("🔹 Loading metadata file...")
        metadata_df = pd.read_parquet(META_PATH)
    else:
        print("Creating new empty metadata store...")
        metadata_df = pd.DataFrame(columns=["doc_id", "chunk_id", "source_name", "mimeType", "start_token", "end_token", "text"])

    print("Global resources loaded and ready for use.")



load_resources()