from fastapi import Depends
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..main import app
from ..models import StationTask, WorkOrder
from ..schemas import AskOrderInput, AskOrderOutput, WorkOrderOut
from .client import chat, config, llm_client


@app.post("/api/agent/ask", response_model=AskOrderOutput)
def ask(data: AskOrderInput, db: Session = Depends(get_db)):
    work_orders = (
        db.query(WorkOrder)
        .options(
            joinedload(WorkOrder.product),
            joinedload(WorkOrder.station_tasks).joinedload(StationTask.station),
        )
        .order_by(WorkOrder.priority, WorkOrder.created_at.desc())
        .all()
    )
    format_orders = [
        WorkOrderOut.model_validate(order).model_dump(mode="json") for order in work_orders
    ]
    answer = chat(
        llm_client,
        config["model_pro"],
        data.question,
        format_orders,
        stream=False,
        thinking=True,
    )
    return AskOrderOutput(answer=answer)
