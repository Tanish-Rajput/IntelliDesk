# 🧠 IntelliDesk

**IntelliDesk** is an **RAG-based (Retrieval-Augmented Generation)** chat system that allows companies to create their own AI chatbot trained on internal data — without the need for retraining any model.  

Users can connect their **Notion**, **Google Drive**, or upload **PDF documents**, and the system automatically builds a knowledge base that can be queried through a chat interface.

---

## 🚀 Overview

The project consists of two main components:

### 🖥️ Frontend (Next.js)
A simple chat interface built with **Next.js** that allows users to:
- Chat with the AI assistant  
- Connect or upload their knowledge sources  

### ⚙️ Backend (FastAPI)
A backend powered by **FastAPI**, responsible for:
- Fetching and processing data from Notion, Google Drive, or uploaded PDFs  
- Converting text into embeddings using **Hugging Face’s Sentence Transformer**  
- Storing embeddings in **FAISS** for fast similarity search  
- Using **Google’s Gemini API** for accurate, context-aware responses  

---

## 🧠 How It Works

1. Extracts text from connected data sources  
2. Converts extracted text into embeddings  
3. Stores these embeddings in a FAISS index  
4. When a user asks a question:
   - The query is embedded  
   - A semantic search finds the most relevant chunks  
   - Gemini generates a response using the retrieved context  

---

## ⚙️ Setup Instructions

### 1. Clone the Repository
```bash
git clone <repo_url>
cd IntelliDesk
```

### Backend Setup (FastAPI)

Navigate to the backend directory:
```bash
cd app
```


Create a .env file and add:

```bash
SUPABASE_URL=<your_supabase_url>
SUPABASE_KEY=<your_supabase_key>
GOOGLE_API_KEY=<your_google_api_key>
```


Make sure you’ve created a Supabase project with a storage bucket named "Pdfs".

Run the backend server:
```bash
python index.py
```
### Frontend Setup (Next.js)

Navigate to the frontend directory:
```bash
cd Frontend
```

Create a .env.local file and add:
```bash
NEXT_PUBLIC_SUPABASE_URL=<your_supabase_url>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your_supabase_anon_key>
```

Install dependencies and start the development server:
```bash
npm install
npm run dev
```
