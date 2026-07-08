from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import AskOrderInput, AskOrderOutput
from .service import ask_about_orders

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/ask", response_model=AskOrderOutput)
def ask(data: AskOrderInput, db: Session = Depends(get_db)):
    return ask_about_orders(data.question, db)
