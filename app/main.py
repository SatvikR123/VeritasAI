from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router

app = FastAPI(
    title="Agentic Multi-Agent News Intelligence Platform",
    description="An AI-powered multi-agent platform for event clustering, summarization, bias detection, fact verification, and consensus reporting.",
    version="1.0.0",
)

# Set up CORS middleware for secure frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register sub-agent endpoints
app.include_router(router)

@app.get("/")
async def root():

    return {
        "message": "Welcome to the Agentic Multi-Agent News Intelligence API",
        "docs_url": "/docs",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
