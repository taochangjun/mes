import re

from sqlalchemy.orm import Session, joinedload

from ..models import StationTask, StationTaskStatus, WorkOrder
from ..schemas import AskOrderOutput
from ..settings import get_settings

from .llm import complete
from .prompts import build_messages

ORDER_NO_RE = re.compile(r"WO-\d{8}-\d{3}")

STATUS_LABELS = {
    "pending": "待下达",
    "released": "已下达",
    "in_progress": "生产中",
    "completed": "已完工",
    "closed": "已关闭",
}


def extract_order_no(question: str) -> str | None:
    match = ORDER_NO_RE.search(question)
    return match.group(0) if match else None


def _task_progress(tasks: list[StationTask]) -> tuple[int, int]:
    total = len(tasks)
    done = sum(1 for t in tasks if t.status == StationTaskStatus.COMPLETED)
    return done, total


def _current_station(tasks: list[StationTask]) -> str | None:
    for task in tasks:
        if task.status == StationTaskStatus.IN_PROGRESS:
            return task.station.name
    for task in tasks:
        if task.status == StationTaskStatus.WAITING:
            return task.station.name
    return None


def _order_summary(order: WorkOrder) -> dict:
    done, total = _task_progress(order.station_tasks)
    status = order.status.value
    return {
        "order_no": order.order_no,
        "status": status,
        "status_label": STATUS_LABELS.get(status, status),
        "customer": order.customer,
        "product": order.product.name,
        "progress": f"{done}/{total}",
        "current_station": _current_station(order.station_tasks),
    }


def build_order_context(order: WorkOrder) -> dict:
    ctx = _order_summary(order)
    ctx["type"] = "order_detail"
    ctx["quantity"] = order.quantity
    ctx["priority"] = order.priority
    ctx["tasks"] = [
        {
            "sequence": t.sequence,
            "station": t.station.name,
            "status": t.status.value,
            "operator": t.operator,
        }
        for t in order.station_tasks
    ]
    return ctx


def build_orders_summary(db: Session) -> dict:
    orders = (
        db.query(WorkOrder)
        .options(
            joinedload(WorkOrder.product),
            joinedload(WorkOrder.station_tasks).joinedload(StationTask.station),
        )
        .order_by(WorkOrder.priority, WorkOrder.created_at.desc())
        .all()
    )
    summaries = [_order_summary(order) for order in orders]
    by_status: dict[str, int] = {}
    for summary in summaries:
        by_status[summary["status"]] = by_status.get(summary["status"], 0) + 1

    return {
        "type": "orders_summary",
        "total": len(summaries),
        "by_status": by_status,
        "orders": summaries,
    }


def llm_explain(question: str, context: dict, *, thinking: bool = False) -> str:
    messages = build_messages(question, context)
    settings = get_settings()
    print(settings)
    return complete(messages, model=settings.deepseek_model_pro, thinking=thinking)


def maybe_direct_answer(question: str, context: dict) -> str | None:
    if context.get("type") != "order_detail":
        return None
    if "状态" in question or "进度" in question:
        return (
            f"{context['order_no']} 当前状态：{context['status_label']}，"
            f"进度 {context['progress']}，当前工位：{context.get('current_station') or '无'}"
        )
    return None


def _load_order(db: Session, order_no: str) -> WorkOrder:
    order = (
        db.query(WorkOrder)
        .options(
            joinedload(WorkOrder.product),
            joinedload(WorkOrder.station_tasks).joinedload(StationTask.station),
        )
        .filter(WorkOrder.order_no == order_no)
        .first()
    )
    if not order:
        raise ValueError("工单不存在")
    return order


def ask_about_orders(question: str, db: Session) -> AskOrderOutput:
    order_no = extract_order_no(question)

    if order_no:
        try:
            order = _load_order(db, order_no)
        except ValueError:
            return AskOrderOutput(
                answer=f"{order_no} 工单不存在",
                order_no=order_no,
                matched=False,
            )
        context = build_order_context(order)
    else:
        context = build_orders_summary(db)

    if direct := maybe_direct_answer(question, context):
        return AskOrderOutput(answer=direct, order_no=order_no, matched=True)

    answer = llm_explain(question, context)
    return AskOrderOutput(answer=answer, order_no=order_no, matched=True)
