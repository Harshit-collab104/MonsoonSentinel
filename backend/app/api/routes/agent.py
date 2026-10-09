from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter
from app.agent.orchestrator import get_orchestrator
from app.agent.tools import ALL_TOOLS

router = APIRouter(prefix="/agent", tags=["agent"])

class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    incident_id: Optional[str] = None

@router.post("/chat")
def chat_with_agent(payload: AgentChatRequest):
    """Interact directly with Monsoon Sentinel's Strands agent and inspect tool reasoning traces."""
    orch = get_orchestrator()
    return orch.chat_with_agent(message=payload.message, incident_id=payload.incident_id)

@router.get("/tools")
def list_available_tools():
    """Lists the 12 explicit Strands Agent tools available to the municipal system."""
    tool_list = []
    for t in ALL_TOOLS:
        tool_list.append({
            "name": getattr(t, "name", t.__name__),
            "description": getattr(t, "description", t.__doc__ or "").strip(),
            "type": "StrandsAgentTool"
        })
    return {"tools_count": len(tool_list), "tools": tool_list}
