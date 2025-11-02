from sentence_transformers import SentenceTransformer
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from notion_client import Client
from transformers import AutoTokenizer
from fastapi import APIRouter, UploadFile, File, Form
import json
import math
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
import pandas as pd
import pdfplumber
import io
import faiss
import os

# ---------- CONFIG ----------

router = APIRouter(prefix="/fetchData", tags=["fetchData"])

modelName = "sentence-transformers/all-MiniLM-L6-v2"
model = SentenceTransformer(modelName)
CHUNK_SIZE_TOKENS = 400
CHUNK_OVERLAP_TOKENS = 64
EMBED_DIM = 384

# ---------- Utilities ----------
tokenizer = AutoTokenizer.from_pretrained(modelName)

# ---------- PDF extraction ----------
def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    """Extract text from PDF bytes using pdfplumber."""
    text_chunks = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            txt = page.extract_text()
            if txt:
                text_chunks.append(txt)
    return "\n".join(text_chunks)

# ---------- Google Drive fetcher ----------
def fetch_text_files_from_drive(credentials_dict: dict, query: str = None, page_size: int = 10) -> List[Dict]:
    """
    credentials_dict: dict from `google-auth` authorized user info or service-account json.
    query: optional Drive query string, e.g. "mimeType='application/pdf'".
    Returns list of dicts: [{"id":..., "name":..., "mimeType":..., "text":...}, ...]
    """
    creds = Credentials.from_authorized_user_info(credentials_dict)
    service = build("drive", "v3", credentials=creds, cache_discovery=False)

    q = query if query else "trashed=false"
    results = service.files().list(q=q, pageSize=page_size, fields="files(id,name,mimeType)").execute()
    files = results.get("files", [])
    docs = []
    for f in files:
        fid = f["id"]; name = f["name"]; mime = f.get("mimeType", "")
        try:
            if mime == "application/pdf":
                request = service.files().get_media(fileId=fid)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                fh.seek(0)
                content_bytes = fh.read()
                text = extract_text_from_pdf_bytes(content_bytes)
            elif mime.startswith("text/") or mime in ("application/vnd.google-apps.document",):
                # For Google Docs, export plain text
                if mime == "application/vnd.google-apps.document":
                    request = service.files().export_media(fileId=fid, mimeType="text/plain")
                    fh = io.BytesIO()
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                    fh.seek(0)
                    text = fh.read().decode("utf-8", errors="ignore")
                else:
                    # generic text files
                    request = service.files().get_media(fileId=fid)
                    fh = io.BytesIO()
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                    fh.seek(0)
                    text = fh.read().decode("utf-8", errors="ignore")
            else:
                # Skip or try export for other types
                text = ""
        except Exception as e:
            print(f"Error fetching {name}: {e}")
            text = ""
        docs.append({"id": fid, "name": name, "mimeType": mime, "text": text})
    return docs

# ---------- Notion fetcher ----------
def fetch_texts_from_notion(api_key: str, database_id: str, page_size: int = 10) -> List[Dict]:
    notion = Client(auth=api_key)
    # Query pages in DB
    response = notion.databases.query(database_id=database_id, page_size=page_size)
    out = []
    for page in response.get("results", []):
        page_id = page["id"]
        # Fetch block children to collect paragraph text (simple approach)
        blocks = notion.blocks.children.list(page_id).get("results", [])
        text_parts = []
        for block in blocks:
            t = None
            if block.get("type") == "paragraph":
                rt = block["paragraph"].get("rich_text", [])
                if rt:
                    t = "".join([r.get("plain_text", "") for r in rt])
            elif block.get("type") == "heading_1":
                rt = block["heading_1"].get("rich_text", [])
                t = "".join([r.get("plain_text", "") for r in rt])
            # add other block types as needed
            if t:
                text_parts.append(t)
        text = "\n".join(text_parts)
        out.append({"id": page_id, "name": page_id, "mimeType": "notion-page", "text": text})
    return out

# ---------- Token-level chunking (sliding window) ----------
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
async def fetch_data(file: UploadFile = File(...), notion_api_key: str = Form(...), notion_db: str = Form(...)):
    google_creds_json = await file.read()

    all_docs = []

    if len(google_creds_json) > 0:
        creds_dict = json.loads(google_creds_json)
        # optional: query to fetch PDFs and Google Docs
        q = "mimeType='application/pdf' or mimeType='application/vnd.google-apps.document' or mimeType contains 'text/'"
        drive_docs = fetch_text_files_from_drive(creds_dict, query=q, page_size=100)
        all_docs.extend(drive_docs)
        print(f"Fetched {len(drive_docs)} files from Drive")

    if len(notion_api_key) > 0 and len(notion_db) > 0:
        notion_docs = fetch_texts_from_notion(notion_api_key, notion_db, page_size=100)
        all_docs.extend(notion_docs)
        print(f"Fetched {len(notion_docs)} pages from Notion")

    # Create or load FAISS index and metadata
    INDEX_PATH = "../database/faiss_index.bin"
    META_PATH = "../database/metadata.parquet"
    index = build_or_load_faiss(INDEX_PATH, EMBED_DIM)
    metadata_store = load_metadata(META_PATH)

    index, metadata_store = ingest_documents_to_faiss(all_docs, index, metadata_store)

    # Persist
    save_faiss_and_metadata(index, INDEX_PATH, metadata_store, META_PATH)
    return {"message": "Ingest complete. total chunks in metadata:", "total_chunks": len(metadata_store)}