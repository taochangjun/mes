from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class WorkOrderStatus(str, Enum):
    PENDING = "pending"
    RELEASED = "released"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CLOSED = "closed"


class StationTaskStatus(str, Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class QualityResult(str, Enum):
    PENDING = "pending"
    PASS = "pass"
    FAIL = "fail"


class ProductOut(BaseModel):
    id: int
    code: str
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class MaterialOut(BaseModel):
    id: int
    code: str
    name: str
    unit: str
    is_critical: bool
    stock_qty: float

    model_config = {"from_attributes": True}


class BomItemOut(BaseModel):
    id: int
    material: MaterialOut
    quantity: float

    model_config = {"from_attributes": True}


class WorkStationOut(BaseModel):
    id: int
    code: str
    name: str
    line: str
    description: str | None = None

    model_config = {"from_attributes": True}


class ProcessRouteStepOut(BaseModel):
    id: int
    sequence: int
    station: WorkStationOut
    sop_content: str
    standard_time_min: int
    safety_notes: str | None = None

    model_config = {"from_attributes": True}


class StationTaskOut(BaseModel):
    id: int
    sequence: int
    station: WorkStationOut
    sop_content: str
    safety_notes: str | None = None
    status: StationTaskStatus
    operator: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    report_note: str | None = None

    model_config = {"from_attributes": True}


class WorkOrderOut(BaseModel):
    id: int
    order_no: str
    product: ProductOut
    quantity: int
    status: WorkOrderStatus
    customer: str | None = None
    priority: int
    planned_start: datetime | None = None
    planned_end: datetime | None = None
    created_at: datetime
    released_at: datetime | None = None
    completed_at: datetime | None = None
    station_tasks: list[StationTaskOut] = []

    model_config = {"from_attributes": True}


class WorkOrderCreate(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)
    customer: str | None = None
    priority: int = Field(default=5, ge=1, le=10)


class TaskStartRequest(BaseModel):
    operator: str


class TaskCompleteRequest(BaseModel):
    operator: str
    report_note: str | None = None


class QualityRecordOut(BaseModel):
    id: int
    work_order_id: int
    station: WorkStationOut
    inspector: str
    check_item: str
    standard: str
    result: QualityResult
    remark: str | None = None
    inspected_at: datetime

    model_config = {"from_attributes": True}


class QualityRecordCreate(BaseModel):
    work_order_id: int
    station_id: int
    inspector: str
    check_item: str
    standard: str
    result: QualityResult
    remark: str | None = None


class MaterialIssueOut(BaseModel):
    id: int
    work_order_id: int
    material: MaterialOut
    quantity: float
    issued_at: datetime
    status: str

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_orders: int
    pending_orders: int
    in_progress_orders: int
    completed_orders: int
    active_stations: int
    total_stations: int
    quality_pass_rate: float
    critical_materials_low_stock: int
