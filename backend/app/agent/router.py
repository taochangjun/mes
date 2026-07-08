from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .loop import run_agent

from ..database import get_db
from ..schemas import AskOrderInput, AskOrderOutput, AgentChatOutput
from .service import ask_about_orders

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/ask", response_model=AskOrderOutput)
def ask(data: AskOrderInput, db: Session = Depends(get_db)):
    return ask_about_orders(data.question, db)

@router.post("/chat", response_model=AgentChatOutput)
def chat(data: AskOrderInput, db: Session = Depends(get_db)):
    answer, trace =  run_agent(data.question, db)
    return AgentChatOutput(answer=answer, tool_calls=trace)
