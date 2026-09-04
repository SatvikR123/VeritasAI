from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from app.agents.graph import app_graph
from app.models.report import IntelligenceReport

router = APIRouter(prefix="/api/v1", tags=["News Intelligence"])

class AnalyzeRequest(BaseModel):
    query: str = Field(
        ..., 
        json_schema_extra={"example": "AetherCorp"}, 
        description="The search query or news topic to analyze"
    )

class AnalyzeResponse(BaseModel):
    query: str
    reports: Dict[str, IntelligenceReport] = Field(
        ..., 
        description="Mapping of cluster_id to the compiled structured intelligence reports"
    )
    errors: List[str]

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_topic(request: AnalyzeRequest):
    """
    Executes the 8-agent LangGraph workflow for event collection, clustering,
    summarization, fact verification, bias checks, source credibility scoring,
    and consensus resolution. Returns structured reports and generated markdown.
    """
    try:
        # Initialize graph state
        initial_state = {
            "query": request.query,
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
        
        # Execute the multi-agent graph synchronously
        result = app_graph.invoke(initial_state)
        
        final_reports = result.get("final_reports", {})
        errors = result.get("errors", [])
        
        # If no reports were generated and errors exist, fail the request
        if not final_reports and errors:
            raise HTTPException(
                status_code=500, 
                detail=f"Workflow failed to compile any reports: {'; '.join(errors)}"
            )
            
        return AnalyzeResponse(
            query=request.query,
            reports=final_reports,
            errors=errors
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error executing multi-agent workflow: {str(e)}"
        )
