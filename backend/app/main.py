from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload

from .database import Base, engine, get_db
from .models import (
    BomItem,
    Material,
    MaterialIssue,
    Product,
    QualityRecord,
    StationTask,
    WorkOrder,
    WorkStation,
)
from .schemas import (
    BomItemOut,
    DashboardStats,
    MaterialIssueOut,
    MaterialOut,
    ProductOut,
    QualityRecordCreate,
    QualityRecordOut,
    StationTaskOut,
    TaskCompleteRequest,
    TaskStartRequest,
    WorkOrderCreate,
    WorkOrderOut,
    WorkStationOut,
)
from .seed import seed_demo_data
from .services import (
    complete_task,
    create_work_order,
    get_dashboard_stats,
    issue_materials,
    release_work_order,
    start_task,
)

app = FastAPI(title="SanyMES Demo", description="三一重工 MES 简化版演示系统", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    seed_demo_data(db)


@app.get("/api/health")
def health():
    return {"status": "ok", "system": "SanyMES Demo"}


@app.get("/api/dashboard", response_model=DashboardStats)
def dashboard(db: Session = Depends(get_db)):
    return get_dashboard_stats(db)


@app.get("/api/products", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


@app.get("/api/products/{product_id}/bom", response_model=list[BomItemOut])
def get_product_bom(product_id: int, db: Session = Depends(get_db)):
    return (
        db.query(BomItem)
        .options(joinedload(BomItem.material))
        .filter(BomItem.product_id == product_id)
        .all()
    )


@app.get("/api/materials", response_model=list[MaterialOut])
def list_materials(db: Session = Depends(get_db)):
    return db.query(Material).order_by(Material.is_critical.desc(), Material.code).all()


@app.get("/api/stations", response_model=list[WorkStationOut])
def list_stations(db: Session = Depends(get_db)):
    return db.query(WorkStation).order_by(WorkStation.code).all()


@app.get("/api/work-orders", response_model=list[WorkOrderOut])
def list_work_orders(db: Session = Depends(get_db)):
    return (
        db.query(WorkOrder)
        .options(
            joinedload(WorkOrder.product),
            joinedload(WorkOrder.station_tasks).joinedload(StationTask.station),
        )
        .order_by(WorkOrder.priority, WorkOrder.created_at.desc())
        .all()
    )


@app.get("/api/work-orders/{order_id}", response_model=WorkOrderOut)
def get_work_order(order_id: int, db: Session = Depends(get_db)):
    order = (
        db.query(WorkOrder)
        .options(
            joinedload(WorkOrder.product),
            joinedload(WorkOrder.station_tasks).joinedload(StationTask.station),
        )
        .filter(WorkOrder.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    return order


@app.post("/api/work-orders", response_model=WorkOrderOut)
def create_order(data: WorkOrderCreate, db: Session = Depends(get_db)):
    try:
        order = create_work_order(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return get_work_order(order.id, db)


@app.post("/api/work-orders/{order_id}/release", response_model=WorkOrderOut)
def release_order(order_id: int, db: Session = Depends(get_db)):
    try:
        release_work_order(db, order_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return get_work_order(order_id, db)


@app.post("/api/work-orders/{order_id}/issue-materials", response_model=list[MaterialIssueOut])
def issue_order_materials(order_id: int, db: Session = Depends(get_db)):
    issues = issue_materials(db, order_id)
    return (
        db.query(MaterialIssue)
        .options(joinedload(MaterialIssue.material))
        .filter(MaterialIssue.work_order_id == order_id)
        .all()
    )


@app.get("/api/work-orders/{order_id}/materials", response_model=list[MaterialIssueOut])
def get_order_materials(order_id: int, db: Session = Depends(get_db)):
    return (
        db.query(MaterialIssue)
        .options(joinedload(MaterialIssue.material))
        .filter(MaterialIssue.work_order_id == order_id)
        .all()
    )


@app.get("/api/station-tasks", response_model=list[StationTaskOut])
def list_station_tasks(station_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(StationTask).options(
        joinedload(StationTask.station), joinedload(StationTask.work_order)
    )
    if station_id:
        q = q.filter(StationTask.station_id == station_id)
    return q.order_by(StationTask.sequence).all()


@app.post("/api/station-tasks/{task_id}/start", response_model=StationTaskOut)
def start_station_task(task_id: int, data: TaskStartRequest, db: Session = Depends(get_db)):
    try:
        return start_task(db, task_id, data.operator)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/station-tasks/{task_id}/complete", response_model=StationTaskOut)
def complete_station_task(task_id: int, data: TaskCompleteRequest, db: Session = Depends(get_db)):
    try:
        return complete_task(db, task_id, data.operator, data.report_note)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/quality-records", response_model=list[QualityRecordOut])
def list_quality_records(work_order_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(QualityRecord).options(joinedload(QualityRecord.station))
    if work_order_id:
        q = q.filter(QualityRecord.work_order_id == work_order_id)
    return q.order_by(QualityRecord.inspected_at.desc()).all()


@app.post("/api/quality-records", response_model=QualityRecordOut)
def create_quality_record(data: QualityRecordCreate, db: Session = Depends(get_db)):
    record = QualityRecord(**data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return (
        db.query(QualityRecord)
        .options(joinedload(QualityRecord.station))
        .filter(QualityRecord.id == record.id)
        .first()
    )


# 注册 Agent 路由（必须在 app 创建之后 import）
from .agent import router as agent_router  # noqa: E402, F401
