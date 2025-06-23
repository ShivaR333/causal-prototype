from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
from ..models import CausalQuery as CausalQueryUnion
from ..dispatch import dispatch_query
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from causal_agent import CausalAnalysisAgent

app = FastAPI(title="Causal Analysis API", version="0.1.0")

# Global agent sessions storage (in production, use Redis or database)
agent_sessions: Dict[str, CausalAnalysisAgent] = {}

# Configure CORS to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CausalQueryRequest(BaseModel):
    query: Dict[str, Any]
    dag_file: str = "causal_analysis/config/sample_dag.json"
    data_file: str

class LegacyCausalQuery(BaseModel):
    treatment_variable: str
    outcome_variable: str
    confounders: List[str]
    treatment_value: Optional[float] = None
    dag_file: Optional[str] = "causal_analysis/config/sample_dag.json"
    data_file: Optional[str] = None

class CausalResult(BaseModel):
    estimate: Optional[float] = None
    confidence_interval: Optional[List[float]] = None
    summary: str
    success: bool
    error: Optional[str] = None
    query_type: Optional[str] = None
    results: Optional[Dict[str, Any]] = None

class AgentRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class AgentResponse(BaseModel):
    response: str
    session_id: str
    state: str
    requires_confirmation: bool = False

@app.get("/")
async def root():
    return {"message": "Causal Analysis API", "version": "0.1.0"}

@app.post("/agent/chat", response_model=AgentResponse)
async def chat_with_agent(request: AgentRequest):
    """Chat with the causal analysis agent using the conversational workflow."""
    import uuid
    
    # Get or create session
    session_id = request.session_id or str(uuid.uuid4())
    
    if session_id not in agent_sessions:
        try:
            # Initialize agent (skip OpenAI requirement for now)
            agent_sessions[session_id] = CausalAnalysisAgent()
        except Exception as e:
            # Fallback for cases where OpenAI key is not available
            raise HTTPException(
                status_code=503, 
                detail="Agent initialization failed. OpenAI API key may be missing."
            )
    
    agent = agent_sessions[session_id]
    
    try:
        # Process user message through agent workflow
        response = agent.process_user_question(request.message)
        
        # Determine if confirmation is needed based on agent state
        requires_confirmation = agent.state.value in [
            "dag_proposed", 
            "eda_completed", 
            "analysis_plan_proposed"
        ]
        
        return AgentResponse(
            response=response,
            session_id=session_id,
            state=agent.state.value,
            requires_confirmation=requires_confirmation
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent processing error: {str(e)}")

@app.post("/agent/reset")
async def reset_agent_session(session_id: str):
    """Reset an agent session."""
    if session_id in agent_sessions:
        agent_sessions[session_id].reset()
        return {"message": "Session reset successfully"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/agent/status/{session_id}")
async def get_agent_status(session_id: str):
    """Get the current status of an agent session."""
    if session_id in agent_sessions:
        agent = agent_sessions[session_id]
        return agent.get_state_info()
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.post("/query", response_model=Dict[str, Any])
async def execute_causal_query(request: CausalQueryRequest):
    """Execute causal query using dispatch system."""
    try:
        result = dispatch_query(
            query_json=request.query,
            dag_path=request.dag_file,
            data_path=request.data_file
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze", response_model=CausalResult)
async def analyze_causal_effect(query: LegacyCausalQuery):
    """Legacy endpoint for causal effect analysis."""
    try:
        if not query.data_file:
            raise HTTPException(status_code=400, detail="data_file is required")
            
        # Convert legacy query to new format
        effect_query = {
            "query_type": "effect_estimation",
            "treatment_variable": query.treatment_variable,
            "outcome_variable": query.outcome_variable,
            "confounders": query.confounders,
            "treatment_value": query.treatment_value
        }
        
        result = dispatch_query(
            query_json=effect_query,
            dag_path=query.dag_file or "causal_analysis/config/sample_dag.json",
            data_path=query.data_file
        )
        
        # Convert result to legacy format
        if result["success"]:
            return CausalResult(
                estimate=result.get("estimate"),
                confidence_interval=result.get("confidence_interval"),
                summary=result.get("summary", "Analysis completed"),
                success=True,
                query_type=result.get("query_type"),
                results=result
            )
        else:
            return CausalResult(
                summary=result.get("error", "Analysis failed"),
                success=False,
                error=result.get("error"),
                query_type=result.get("query_type")
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))