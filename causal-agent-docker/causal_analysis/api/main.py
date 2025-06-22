from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
from ..models import CausalQuery as CausalQueryUnion
from ..dispatch import dispatch_query

app = FastAPI(title="Causal Analysis API", version="0.1.0")

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

@app.get("/")
async def root():
    return {"message": "Causal Analysis API", "version": "0.1.0"}

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