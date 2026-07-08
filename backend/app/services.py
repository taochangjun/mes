from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from .models import (
    BomItem,
    Material,
    MaterialIssue,
    ProcessRoute,
    ProcessRouteStep,
    Product,
    QualityRecord,
    QualityResult,
    StationTask,
    StationTaskStatus,
    WorkOrder,
    WorkOrderStatus,
)
from .schemas import DashboardStats, WorkOrderCreate


def generate_order_no(db: Session) -> str:
    today = datetime.utcnow().strftime("%Y%m%d")
    count = db.query(WorkOrder).filter(WorkOrder.order_no.like(f"WO-{today}-%")).count()
    return f"WO-{today}-{count + 1:03d}"


def create_work_order(db: Session, data: WorkOrderCreate) -> WorkOrder:
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise ValueError("产品不存在")

    route = (
        db.query(ProcessRoute)
        .options(joinedload(ProcessRoute.steps).joinedload(ProcessRouteStep.station))
        .filter(ProcessRoute.product_id == data.product_id, ProcessRoute.is_active.is_(True))
        .first()
    )
    if not route:
        raise ValueError("产品未配置工艺路线")

    order = WorkOrder(
        order_no=generate_order_no(db),
        product_id=data.product_id,
        quantity=data.quantity,
        customer=data.customer,
        priority=data.priority,
        status=WorkOrderStatus.PENDING,
    )
    db.add(order)
    db.flush()

    for step in route.steps:
        db.add(
            StationTask(
                work_order_id=order.id,
                station_id=step.station_id,
                sequence=step.sequence,
                sop_content=step.sop_content,
                safety_notes=step.safety_notes,
            )
        )

    bom_items = (
        db.query(BomItem)
        .options(joinedload(BomItem.material))
        .filter(BomItem.product_id == data.product_id)
        .all()
    )
    for item in bom_items:
        db.add(
            MaterialIssue(
                work_order_id=order.id,
                material_id=item.material_id,
                quantity=item.quantity * data.quantity,
                status="pending",
            )
        )

    db.commit()
    db.refresh(order)
    return order


def release_work_order(db: Session, order_id: int) -> WorkOrder:
    order = _get_order(db, order_id)
    if order.status != WorkOrderStatus.PENDING:
        raise ValueError("只有待下达状态的工单可以下达")

    order.status = WorkOrderStatus.RELEASED
    order.released_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    return order


def start_task(db: Session, task_id: int, operator: str) -> StationTask:
    task = (
        db.query(StationTask)
        .options(joinedload(StationTask.work_order), joinedload(StationTask.station))
        .filter(StationTask.id == task_id)
        .first()
    )
    if not task:
        raise ValueError("工位任务不存在")
    if task.status not in (StationTaskStatus.WAITING, StationTaskStatus.BLOCKED):
        raise ValueError("任务状态不允许开工")

    prev = (
        db.query(StationTask)
        .filter(
            StationTask.work_order_id == task.work_order_id,
            StationTask.sequence == task.sequence - 1,
        )
        .first()
    )
    if prev and prev.status != StationTaskStatus.COMPLETED:
        raise ValueError("上一道工序尚未完成")

    task.status = StationTaskStatus.IN_PROGRESS
    task.operator = operator
    task.started_at = datetime.utcnow()

    order = task.work_order
    if order.status == WorkOrderStatus.RELEASED:
        order.status = WorkOrderStatus.IN_PROGRESS

    db.commit()
    db.refresh(task)
    return task


def complete_task(db: Session, task_id: int, operator: str, report_note: str | None) -> StationTask:
    task = (
        db.query(StationTask)
        .options(joinedload(StationTask.work_order), joinedload(StationTask.station))
        .filter(StationTask.id == task_id)
        .first()
    )
    if not task:
        raise ValueError("工位任务不存在")
    if task.status != StationTaskStatus.IN_PROGRESS:
        raise ValueError("只有进行中的任务可以报完工")

    task.status = StationTaskStatus.COMPLETED
    task.operator = operator
    task.report_note = report_note
    task.completed_at = datetime.utcnow()

    remaining = (
        db.query(StationTask)
        .filter(
            StationTask.work_order_id == task.work_order_id,
            StationTask.status != StationTaskStatus.COMPLETED,
        )
        .count()
    )
    if remaining == 0:
        order = task.work_order
        order.status = WorkOrderStatus.COMPLETED
        order.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(task)
    return task


def issue_materials(db: Session, order_id: int) -> list[MaterialIssue]:
    issues = (
        db.query(MaterialIssue)
        .options(joinedload(MaterialIssue.material))
        .filter(MaterialIssue.work_order_id == order_id, MaterialIssue.status == "pending")
        .all()
    )
    for issue in issues:
        material = db.query(Material).filter(Material.id == issue.material_id).first()
        if material and material.stock_qty >= issue.quantity:
            material.stock_qty -= issue.quantity
            issue.status = "delivered"
        else:
            issue.status = "shortage"

    db.commit()
    return issues


def get_dashboard_stats(db: Session) -> DashboardStats:
    total = db.query(WorkOrder).count()
    pending = db.query(WorkOrder).filter(WorkOrder.status == WorkOrderStatus.PENDING).count()
    in_progress = db.query(WorkOrder).filter(
        WorkOrder.status.in_([WorkOrderStatus.RELEASED, WorkOrderStatus.IN_PROGRESS])
    ).count()
    completed = db.query(WorkOrder).filter(
        WorkOrder.status.in_([WorkOrderStatus.COMPLETED, WorkOrderStatus.CLOSED])
    ).count()

    active_stations = db.query(StationTask).filter(
        StationTask.status == StationTaskStatus.IN_PROGRESS
    ).count()
    total_stations = db.query(StationTask).count()

    quality_total = db.query(QualityRecord).filter(QualityRecord.result != QualityResult.PENDING).count()
    quality_pass = db.query(QualityRecord).filter(QualityRecord.result == QualityResult.PASS).count()
    pass_rate = (quality_pass / quality_total * 100) if quality_total else 100.0

    low_stock = db.query(Material).filter(
        Material.is_critical.is_(True), Material.stock_qty < 5
    ).count()

    return DashboardStats(
        total_orders=total,
        pending_orders=pending,
        in_progress_orders=in_progress,
        completed_orders=completed,
        active_stations=active_stations,
        total_stations=total_stations,
        quality_pass_rate=round(pass_rate, 1),
        critical_materials_low_stock=low_stock,
    )


def _get_order(db: Session, order_id: int) -> WorkOrder:
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise ValueError("工单不存在")
    return order


def get_order_by_no(db: Session, order_no: str):
    order = db.query(WorkOrder).filter(WorkOrder.order_no == order_no).first()
    if not order:
        raise ValueError("工单不存在")
    return order
