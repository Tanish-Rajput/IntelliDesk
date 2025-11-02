from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers import data_fetch_and_store, uploaded_pdf, main
from typing import Dict
import uvicorn
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI instance with metadata
app = FastAPI(
    title="RAG System by Tanish",
    description="A Retrieval-Augmented Generation (RAG) system API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for request timing and logging
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"Request to {request.url.path} took {process_time:.2f} seconds")
    return response

# Error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.detail,
            "path": request.url.path
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": str(time.time())
    }

# API version prefix
api_v1_prefix = "/api/v1"

app.include_router(
    data_fetch_and_store.router,
    tags=["Data Operations"]
)
app.include_router(
    uploaded_pdf.router,
    tags=["PDF Operations"]
)
app.include_router(
    main.router,
    tags=["Main Operations"]
)

# Root endpoint
@app.get("/")
async def root() -> Dict[str, str]:
    return {
        "message": "Welcome to RAG System API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "api_version": "1.0.0"
    }


if __name__ == "__main__":
    uvicorn.run("fast_api:app", reload=True)