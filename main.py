import os
import json
import uuid
import logging
import asyncio
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Query, HTTPException, Header, Depends
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
from app.db import (
    init_db, create_user, get_user_by_username, get_user_by_id,
    verify_password, create_session, get_session_user, delete_session,
    get_user_reports, save_report, delete_report, log_analysis,
    get_system_analytics, get_trending_topics, update_trending_topic
)
init_db()

app = FastAPI(title="Veritas AI API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication schemas
class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str
    role: str

class LoginRequest(BaseModel):
    username: str
    password: str

class GoogleLoginRequest(BaseModel):
    id_token: str

# Helper to verify Google OAuth Token
def verify_google_token(id_token: str) -> Optional[Dict[str, Any]]:
    try:
        response = requests.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}", timeout=5)
        if response.status_code != 200:
            logger.error(f"Google Token Info failed with status {response.status_code}: {response.text}")
            return None
        payload = response.json()
        client_id = os.getenv("CLIENT_ID")
        # Check aud claim
        if payload.get("aud") != client_id:
            logger.error(f"Audience mismatch: {payload.get('aud')} != {client_id}")
            return None
        return payload
    except Exception as e:
        logger.error(f"Failed to verify Google token: {e}")
        return None

# Dependency to get current user from Authorization Header
async def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    return get_session_user(token)

# API Routes - Authentication
@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    try:
        user = create_user(
            username=req.username,
            password=req.password,
            full_name=req.full_name,
            role=req.role,
            auth_provider="local"
        )
        token = create_session(user["id"])
        return {"user": user, "token": token}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/auth/login")
async def login(req: LoginRequest):
    user = get_user_by_username(req.username)
    if not user or user["auth_provider"] != "local":
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not verify_password(req.password, user["salt"], user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    token = create_session(user["id"])
    return {
        "user": {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"],
            "avatar_url": user["avatar_url"],
            "auth_provider": user["auth_provider"]
        },
        "token": token
    }

@app.post("/api/auth/google")
async def google_login(req: GoogleLoginRequest):
    payload = verify_google_token(req.id_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid Google token")
        
    email = payload.get("email")
    name = payload.get("name", "Google User")
    picture = payload.get("picture")
    
    if not email:
        raise HTTPException(status_code=400, detail="Google account has no email associated")
        
    user = get_user_by_username(email)
    if not user:
        # Auto register Google user
        try:
            user = create_user(
                username=email,
                password=None, # OAuth users don't have local password
                full_name=name,
                role="Security Analyst",
                avatar_url=picture,
                auth_provider="google"
            )
        except Exception as e:
            logger.error(f"Error registering Google user: {e}")
            raise HTTPException(status_code=500, detail="Failed to create user session")
            
    token = create_session(user["id"])
    return {
        "user": {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"],
            "avatar_url": user["avatar_url"],
            "auth_provider": user["auth_provider"]
        },
        "token": token
    }

@app.post("/api/auth/logout")
async def logout(authorization: Optional[str] = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        delete_session(token)
    return {"status": "success"}

@app.get("/api/auth/me")
async def get_me(user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "id": user["id"],
        "username": user["username"],
        "full_name": user["full_name"],
        "role": user["role"],
        "avatar_url": user["avatar_url"],
        "auth_provider": user["auth_provider"]
    }

# API Routes - History
@app.get("/api/history")
async def get_history(user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    user_id = user["id"] if user else None
    return get_user_reports(user_id)

@app.delete("/api/history/{item_id}")
async def delete_history_item(item_id: str, user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    user_id = user["id"] if user else None
    deleted = delete_report(item_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found or unauthorized")
    return {"status": "success"}

@app.get("/api/analyze")
async def analyze_news_stream(query: str = Query(..., min_length=1), token: Optional[str] = Query(None)):
    """
    Streams LangGraph execution events and the final report using SSE.
    """
    from app.agents.graph import app_graph
    
    # Retrieve user session if token provided
    user_id = None
    if token:
        user = get_session_user(token)
        if user:
            user_id = user["id"]
            
    async def event_generator():
        initial_state = {
            "query": query,
            "articles": [],
            "clusters": [],
            "summaries": {},
            "fact_verifications": {},
            "bias_analyses": {},
            "credibilities": {},
            "consensuses": {},
            "final_reports": {},
            "errors": []
        }
        
        final_reports = {}
        articles_count = 0
        bias_tone = None
        
        try:
            # Pacing update
            yield f"event: status\ndata: {json.dumps({'node': 'collect', 'status': 'running', 'message': 'Contacting NewsAPI...'})}\n\n"
            
            # Execute the compiled LangGraph using async streaming
            async for event in app_graph.astream(initial_state):
                for node_name, node_output in event.items():
                    msg = f"Completed node: {node_name}"
                    status = "completed"
                    
                    if node_name == "collect":
                        count = len(node_output.get("articles", []))
                        articles_count = count
                        msg = f"News Collection Agent gathered {count} articles."
                    elif node_name == "cluster":
                        count = len(node_output.get("clusters", []))
                        msg = f"Event Clustering Agent grouped articles into {count} semantic clusters."
                    elif node_name == "summarize":
                        msg = "Summarization Agent extracted headlines, developments and timelines."
                    elif node_name == "verify":
                        msg = "Fact Verification Agent verified claims and flagged contradictions."
                    elif node_name == "detect_bias":
                        msg = "Bias Detection Agent assessed language patterns and political slants."
                    elif node_name == "assess_credibility":
                        msg = "Credibility Assessment Agent calculated trust and consistency scores."
                    elif node_name == "consensus":
                        msg = "Consensus Agent synthesized narratives and resolved conflicts."
                    elif node_name == "reporter":
                        msg = "Report Generation Agent compiled final markdown documents."
                        final_reports = node_output.get("final_reports", {})
                        
                    yield f"event: status\ndata: {json.dumps({'node': node_name, 'status': status, 'message': msg})}\n\n"
                    
                    # Yield brief sleep to make frontend stepper visual animations smooth
                    await asyncio.sleep(0.5)
            
            # Combine all cluster reports into a single final report markdown
            if final_reports:
                report_markdown = ""
                credibility_scores = []
                for cid, report in final_reports.items():
                    report_markdown += report.markdown_report + "\n\n---\n\n"
                    if report.credibility and hasattr(report.credibility, 'overall_cluster_credibility'):
                        credibility_scores.append(report.credibility.overall_cluster_credibility)
                    if report.bias_analysis and hasattr(report.bias_analysis, 'overall_bias_narrative'):
                        bias_tone = report.bias_analysis.overall_bias_narrative
                        
                avg_cred = sum(credibility_scores) / len(credibility_scores) if credibility_scores else 0.8
                
                report_id = str(uuid.uuid4())
                history_item = {
                    "id": report_id,
                    "query": query,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "report_markdown": report_markdown.rstrip("\n\n---\n\n"),
                    "credibility_score": avg_cred
                }
                
                # Save to database
                save_report(report_id, user_id, query, history_item["report_markdown"], avg_cred)
                log_analysis(user_id, query, articles_count or 3, avg_cred)
                update_trending_topic(query, articles_count or 3, avg_cred, bias_tone)
                
                # Send the final result object
                yield f"event: result\ndata: {json.dumps({'report': history_item})}\n\n"
            else:
                yield f"event: error\ndata: {json.dumps({'message': 'No intelligence reports generated.'})}\n\n"
                
        except Exception as e:
            logger.error(f"Error during stream generation: {e}")
            yield f"event: error\ndata: {json.dumps({'message': f'Analysis failed: {str(e)}'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/analytics")
async def get_analytics():
    return get_system_analytics()

@app.get("/api/trending")
async def get_trending():
    return get_trending_topics()

@app.get("/api/config")
async def get_config():
    return {"google_client_id": os.getenv("CLIENT_ID")}

# Serve Frontend static assets in production
if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
else:
    logger.warning("frontend/dist directory not found. Please build the frontend React app to serve it.")
