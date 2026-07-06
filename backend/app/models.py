import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class WorkOrderStatus(str, enum.Enum):
    PENDING = "pending"
    RELEASED = "released"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CLOSED = "closed"


class StationTaskStatus(str, enum.Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class QualityResult(str, enum.Enum):
    PENDING = "pending"
    PASS = "pass"
    FAIL = "fail"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    bom_items: Mapped[list["BomItem"]] = relationship(back_populates="product")
    routes: Mapped[list["ProcessRoute"]] = relationship(back_populates="product")


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    unit: Mapped[str] = mapped_column(String(20), default="件")
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    stock_qty: Mapped[float] = mapped_column(Float, default=0)

    bom_items: Mapped[list["BomItem"]] = relationship(back_populates="material")


class BomItem(Base):
    __tablename__ = "bom_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    quantity: Mapped[float] = mapped_column(Float, default=1)

    product: Mapped["Product"] = relationship(back_populates="bom_items")
    material: Mapped["Material"] = relationship(back_populates="bom_items")


class WorkStation(Base):
    __tablename__ = "work_stations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    line: Mapped[str] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    route_steps: Mapped[list["ProcessRouteStep"]] = relationship(
        back_populates="station"
    )
    tasks: Mapped[list["StationTask"]] = relationship(back_populates="station")


class ProcessRoute(Base):
    __tablename__ = "process_routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    product: Mapped["Product"] = relationship(back_populates="routes")
    steps: Mapped[list["ProcessRouteStep"]] = relationship(
        back_populates="route", order_by="ProcessRouteStep.sequence"
    )


class ProcessRouteStep(Base):
    __tablename__ = "process_route_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("process_routes.id"))
    station_id: Mapped[int] = mapped_column(ForeignKey("work_stations.id"))
    sequence: Mapped[int] = mapped_column(Integer)
    sop_content: Mapped[str] = mapped_column(Text)
    standard_time_min: Mapped[int] = mapped_column(Integer, default=30)
    safety_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    route: Mapped["ProcessRoute"] = relationship(back_populates="steps")
    station: Mapped["WorkStation"] = relationship(back_populates="route_steps")


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_no: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[WorkOrderStatus] = mapped_column(
        Enum(WorkOrderStatus), default=WorkOrderStatus.PENDING
    )
    customer: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=5)
    planned_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    planned_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    released_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    product: Mapped["Product"] = relationship()
    station_tasks: Mapped[list["StationTask"]] = relationship(
        back_populates="work_order", order_by="StationTask.sequence"
    )
    quality_records: Mapped[list["QualityRecord"]] = relationship(
        back_populates="work_order"
    )


class StationTask(Base):
    __tablename__ = "station_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_order_id: Mapped[int] = mapped_column(ForeignKey("work_orders.id"))
    station_id: Mapped[int] = mapped_column(ForeignKey("work_stations.id"))
    sequence: Mapped[int] = mapped_column(Integer)
    sop_content: Mapped[str] = mapped_column(Text)
    safety_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[StationTaskStatus] = mapped_column(
        Enum(StationTaskStatus), default=StationTaskStatus.WAITING
    )
    operator: Mapped[str | None] = mapped_column(String(50), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    report_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    work_order: Mapped["WorkOrder"] = relationship(back_populates="station_tasks")
    station: Mapped["WorkStation"] = relationship(back_populates="tasks")


class MaterialIssue(Base):
    __tablename__ = "material_issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_order_id: Mapped[int] = mapped_column(ForeignKey("work_orders.id"))
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    quantity: Mapped[float] = mapped_column(Float)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(20), default="pending")

    work_order: Mapped["WorkOrder"] = relationship()
    material: Mapped["Material"] = relationship()


class QualityRecord(Base):
    __tablename__ = "quality_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_order_id: Mapped[int] = mapped_column(ForeignKey("work_orders.id"))
    station_id: Mapped[int] = mapped_column(ForeignKey("work_stations.id"))
    inspector: Mapped[str] = mapped_column(String(50))
    check_item: Mapped[str] = mapped_column(String(200))
    standard: Mapped[str] = mapped_column(String(200))
    result: Mapped[QualityResult] = mapped_column(
        Enum(QualityResult), default=QualityResult.PENDING
    )
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    inspected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    work_order: Mapped["WorkOrder"] = relationship(back_populates="quality_records")
    station: Mapped["WorkStation"] = relationship()
