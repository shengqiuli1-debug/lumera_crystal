from __future__ import annotations

import html
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

StepCode = Literal[
    "order_paid",
    "warehouse_picking",
    "warehouse_packed",
    "shipped",
    "in_transit",
    "out_for_delivery",
    "delivered",
]

TASK_NODE = Literal["assigned", "accepted", "picked_up", "delivered"]
ASSIGNMENT_TYPE = Literal["supplier", "internal_driver"]

STEP_FLOW: list[tuple[str, str]] = [
    ("order_paid", "订单已支付"),
    ("warehouse_picking", "仓库拣货中"),
    ("warehouse_packed", "仓库已打包"),
    ("shipped", "已发货"),
    ("in_transit", "运输中"),
    ("out_for_delivery", "派送中"),
    ("delivered", "已签收"),
]

TASK_NODE_FLOW: list[tuple[str, str]] = [
    ("assigned", "已派单"),
    ("accepted", "已接单"),
    ("picked_up", "已提货/提箱"),
    ("delivered", "已送达"),
]

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_SQLITE_URL = f"sqlite:///{(DATA_DIR / 'logistics.db').as_posix()}"
DATABASE_URL = os.getenv("LOGISTICS_DATABASE_URL", DEFAULT_SQLITE_URL)


class Base(DeclarativeBase):
    pass


class Trace(Base):
    __tablename__ = "logistics_traces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trace_no: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    order_no: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    order_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    carrier: Mapped[str] = mapped_column(String(80), nullable=False, default="mock-express")
    current_step: Mapped[str] = mapped_column(String(50), nullable=False)
    current_label: Mapped[str] = mapped_column(String(120), nullable=False)
    tracking_no: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    events: Mapped[list["TraceEvent"]] = relationship(
        back_populates="trace",
        cascade="all, delete-orphan",
        order_by="TraceEvent.occurred_at.asc(), TraceEvent.id.asc()",
    )


class TraceEvent(Base):
    __tablename__ = "logistics_trace_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trace_id: Mapped[int] = mapped_column(ForeignKey("logistics_traces.id", ondelete="CASCADE"), nullable=False, index=True)
    step_code: Mapped[str] = mapped_column(String(50), nullable=False)
    step_label: Mapped[str] = mapped_column(String(120), nullable=False)
    detail: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    trace: Mapped[Trace] = relationship(back_populates="events")


class CustomerIntakeOrder(Base):
    __tablename__ = "customer_intake_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    intake_no: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    source_order_no: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    source_platform: Mapped[str] = mapped_column(String(40), nullable=False, default="lumera_shop")
    customer_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    customer_phone: Mapped[str] = mapped_column(String(60), nullable=False, default="")
    customer_address: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    demand_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="received", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    planned_order: Mapped["PlannedOrder | None"] = relationship(back_populates="intake", cascade="all, delete-orphan")


class PlannedOrder(Base):
    __tablename__ = "planned_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    planned_no: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    intake_id: Mapped[int] = mapped_column(ForeignKey("customer_intake_orders.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="scheduled", index=True)
    estimated_pickup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_delivery_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resource_snapshot: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    intake: Mapped[CustomerIntakeOrder] = relationship(back_populates="planned_order")
    transport_order: Mapped["TransportOrder | None"] = relationship(back_populates="planned_order", cascade="all, delete-orphan")


class TransportOrder(Base):
    __tablename__ = "transport_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transport_no: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    planned_id: Mapped[int] = mapped_column(ForeignKey("planned_orders.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="dispatching", index=True)
    dispatch_center: Mapped[str] = mapped_column(String(120), nullable=False, default="华东调度中心")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    planned_order: Mapped[PlannedOrder] = relationship(back_populates="transport_order")
    tasks: Mapped[list["DispatchTask"]] = relationship(
        back_populates="transport_order",
        cascade="all, delete-orphan",
        order_by="DispatchTask.created_at.asc(), DispatchTask.id.asc()",
    )


class DispatchTask(Base):
    __tablename__ = "dispatch_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_no: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    transport_id: Mapped[int] = mapped_column(ForeignKey("transport_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_type: Mapped[str] = mapped_column(String(30), nullable=False, default="supplier")
    assignee_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    assignee_code: Mapped[str] = mapped_column(String(60), nullable=False, default="")
    current_node: Mapped[str] = mapped_column(String(30), nullable=False, default="assigned")
    current_label: Mapped[str] = mapped_column(String(60), nullable=False, default="已派单")
    detail: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    transport_order: Mapped[TransportOrder] = relationship(back_populates="tasks")
    events: Mapped[list["DispatchTaskEvent"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="DispatchTaskEvent.occurred_at.asc(), DispatchTaskEvent.id.asc()",
    )


class DispatchTaskEvent(Base):
    __tablename__ = "dispatch_task_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("dispatch_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    node_code: Mapped[str] = mapped_column(String(30), nullable=False)
    node_label: Mapped[str] = mapped_column(String(60), nullable=False)
    detail: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    task: Mapped[DispatchTask] = relationship(back_populates="events")


engine_kwargs: dict = {"future": True, "pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class TraceCreateRequest(BaseModel):
    order_no: str = Field(min_length=1, max_length=60)
    order_id: int | None = None
    carrier: str = Field(default="mock-express", min_length=1, max_length=80)
    tracking_no: str = Field(default="")


class TraceAdvanceRequest(BaseModel):
    detail: str = Field(default="", max_length=255)


class TraceEventRead(BaseModel):
    step_code: str
    step_label: str
    detail: str
    occurred_at: datetime


class TraceRead(BaseModel):
    trace_no: str
    order_no: str
    order_id: int | None
    carrier: str
    tracking_no: str
    current_step: str
    current_label: str
    created_at: datetime
    updated_at: datetime
    events: list[TraceEventRead]


class IntakeCreateRequest(BaseModel):
    source_order_no: str = Field(min_length=1, max_length=60)
    source_platform: str = Field(default="lumera_shop", min_length=1, max_length=40)
    customer_name: str = Field(default="", max_length=120)
    customer_phone: str = Field(default="", max_length=60)
    customer_address: str = Field(default="", max_length=255)
    demand_note: str = Field(default="", max_length=2000)


class PlanCreateRequest(BaseModel):
    estimated_pickup_at: datetime | None = None
    estimated_delivery_at: datetime | None = None
    resource_snapshot: str = Field(default="自动资源评估：标准履约通道", max_length=255)


class DispatchCreateRequest(BaseModel):
    assignment_type: ASSIGNMENT_TYPE = "supplier"
    assignee_name: str = Field(min_length=1, max_length=120)
    assignee_code: str = Field(default="", max_length=60)
    detail: str = Field(default="调度中心已派发任务", max_length=255)


class TaskAdvanceRequest(BaseModel):
    detail: str = Field(default="", max_length=255)


class IntakeRead(BaseModel):
    intake_no: str
    source_order_no: str
    source_platform: str
    status: str
    customer_name: str
    customer_phone: str
    customer_address: str
    demand_note: str
    created_at: datetime
    updated_at: datetime


class PlanRead(BaseModel):
    planned_no: str
    intake_no: str
    status: str
    estimated_pickup_at: datetime | None
    estimated_delivery_at: datetime | None
    resource_snapshot: str
    created_at: datetime
    updated_at: datetime


class TransportRead(BaseModel):
    transport_no: str
    planned_no: str
    status: str
    dispatch_center: str
    created_at: datetime
    updated_at: datetime


class DispatchTaskEventRead(BaseModel):
    node_code: str
    node_label: str
    detail: str
    occurred_at: datetime


class DispatchTaskRead(BaseModel):
    task_no: str
    transport_no: str
    assignment_type: str
    assignee_name: str
    assignee_code: str
    current_node: str
    current_label: str
    detail: str
    created_at: datetime
    updated_at: datetime
    events: list[DispatchTaskEventRead]


app = FastAPI(title="Logistics Service", version="0.3.0")


@app.on_event("startup")
def _startup() -> None:
    Base.metadata.create_all(bind=engine)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _format_iso(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _gen_no(prefix: str) -> str:
    return f"{prefix}-{_now().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"


def _to_trace_read(trace: Trace) -> TraceRead:
    return TraceRead(
        trace_no=trace.trace_no,
        order_no=trace.order_no,
        order_id=trace.order_id,
        carrier=trace.carrier,
        tracking_no=trace.tracking_no,
        current_step=trace.current_step,
        current_label=trace.current_label,
        created_at=trace.created_at,
        updated_at=trace.updated_at,
        events=[
            TraceEventRead(
                step_code=event.step_code,
                step_label=event.step_label,
                detail=event.detail,
                occurred_at=event.occurred_at,
            )
            for event in trace.events
        ],
    )


def _to_intake_read(intake: CustomerIntakeOrder) -> IntakeRead:
    return IntakeRead(
        intake_no=intake.intake_no,
        source_order_no=intake.source_order_no,
        source_platform=intake.source_platform,
        status=intake.status,
        customer_name=intake.customer_name,
        customer_phone=intake.customer_phone,
        customer_address=intake.customer_address,
        demand_note=intake.demand_note,
        created_at=intake.created_at,
        updated_at=intake.updated_at,
    )


def _to_plan_read(plan: PlannedOrder) -> PlanRead:
    return PlanRead(
        planned_no=plan.planned_no,
        intake_no=plan.intake.intake_no,
        status=plan.status,
        estimated_pickup_at=plan.estimated_pickup_at,
        estimated_delivery_at=plan.estimated_delivery_at,
        resource_snapshot=plan.resource_snapshot,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


def _to_transport_read(transport: TransportOrder) -> TransportRead:
    return TransportRead(
        transport_no=transport.transport_no,
        planned_no=transport.planned_order.planned_no,
        status=transport.status,
        dispatch_center=transport.dispatch_center,
        created_at=transport.created_at,
        updated_at=transport.updated_at,
    )


def _to_task_read(task: DispatchTask) -> DispatchTaskRead:
    return DispatchTaskRead(
        task_no=task.task_no,
        transport_no=task.transport_order.transport_no,
        assignment_type=task.assignment_type,
        assignee_name=task.assignee_name,
        assignee_code=task.assignee_code,
        current_node=task.current_node,
        current_label=task.current_label,
        detail=task.detail,
        created_at=task.created_at,
        updated_at=task.updated_at,
        events=[
            DispatchTaskEventRead(
                node_code=event.node_code,
                node_label=event.node_label,
                detail=event.detail,
                occurred_at=event.occurred_at,
            )
            for event in task.events
        ],
    )


def _get_trace_or_404(db: Session, *, trace_no: str) -> Trace:
    trace = db.scalar(select(Trace).where(Trace.trace_no == trace_no))
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    _ = trace.events
    return trace


def _get_intake_or_404(db: Session, *, intake_no: str) -> CustomerIntakeOrder:
    intake = db.scalar(select(CustomerIntakeOrder).where(CustomerIntakeOrder.intake_no == intake_no))
    if not intake:
        raise HTTPException(status_code=404, detail="Intake order not found")
    return intake


def _get_plan_or_404(db: Session, *, planned_no: str) -> PlannedOrder:
    plan = db.scalar(select(PlannedOrder).where(PlannedOrder.planned_no == planned_no))
    if not plan:
        raise HTTPException(status_code=404, detail="Planned order not found")
    _ = plan.intake
    return plan


def _get_transport_or_404(db: Session, *, transport_no: str) -> TransportOrder:
    transport = db.scalar(select(TransportOrder).where(TransportOrder.transport_no == transport_no))
    if not transport:
        raise HTTPException(status_code=404, detail="Transport order not found")
    _ = transport.planned_order
    _ = transport.tasks
    return transport


def _get_task_or_404(db: Session, *, task_no: str) -> DispatchTask:
    task = db.scalar(select(DispatchTask).where(DispatchTask.task_no == task_no))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    _ = task.transport_order
    _ = task.events
    return task


def _ensure_intake_by_order_no(db: Session, *, order_no: str) -> CustomerIntakeOrder:
    intake = db.scalar(select(CustomerIntakeOrder).where(CustomerIntakeOrder.source_order_no == order_no))
    if intake:
        return intake

    now = _now()
    intake = CustomerIntakeOrder(
        intake_no=_gen_no("INT"),
        source_order_no=order_no,
        source_platform="lumera_shop",
        customer_name="商城用户",
        customer_phone="",
        customer_address="",
        demand_note="来源于商城支付成功事件",
        status="received",
        created_at=now,
        updated_at=now,
    )
    db.add(intake)
    db.flush()
    return intake


def _create_plan_for_intake(db: Session, *, intake: CustomerIntakeOrder) -> PlannedOrder:
    exists = db.scalar(select(PlannedOrder).where(PlannedOrder.intake_id == intake.id))
    if exists:
        _ = exists.intake
        return exists

    now = _now()
    plan = PlannedOrder(
        planned_no=_gen_no("PLN"),
        intake_id=intake.id,
        status="scheduled",
        estimated_pickup_at=now + timedelta(hours=2),
        estimated_delivery_at=now + timedelta(days=2),
        resource_snapshot="自动资源评估：标准履约通道",
        created_at=now,
        updated_at=now,
    )
    intake.status = "planned"
    intake.updated_at = now
    db.add(intake)
    db.add(plan)
    db.flush()
    _ = plan.intake
    return plan


def _convert_plan_to_transport(db: Session, *, plan: PlannedOrder) -> TransportOrder:
    exists = db.scalar(select(TransportOrder).where(TransportOrder.planned_id == plan.id))
    if exists:
        _ = exists.planned_order
        return exists

    now = _now()
    transport = TransportOrder(
        transport_no=_gen_no("TRN"),
        planned_id=plan.id,
        status="dispatching",
        dispatch_center="华东调度中心",
        created_at=now,
        updated_at=now,
    )
    plan.status = "converted"
    plan.updated_at = now
    db.add(plan)
    db.add(transport)
    db.flush()
    _ = transport.planned_order
    return transport


def _advance_trace(db: Session, *, trace: Trace, detail: str = "") -> Trace:
    current_index = next((i for i, item in enumerate(STEP_FLOW) if item[0] == trace.current_step), None)
    if current_index is None:
        raise HTTPException(status_code=500, detail="Unknown logistics step")
    if current_index >= len(STEP_FLOW) - 1:
        raise HTTPException(status_code=400, detail="Already delivered")

    next_code, next_label = STEP_FLOW[current_index + 1]
    now = _now()
    trace.current_step = next_code
    trace.current_label = next_label
    trace.updated_at = now

    db.add(
        TraceEvent(
            trace=trace,
            step_code=next_code,
            step_label=next_label,
            detail=detail,
            occurred_at=now,
        )
    )
    db.add(trace)
    db.commit()
    db.refresh(trace)
    _ = trace.events
    return trace


def _advance_task(db: Session, *, task: DispatchTask, detail: str) -> DispatchTask:
    current_index = next((i for i, item in enumerate(TASK_NODE_FLOW) if item[0] == task.current_node), None)
    if current_index is None:
        raise HTTPException(status_code=500, detail="Unknown task node")
    if current_index >= len(TASK_NODE_FLOW) - 1:
        raise HTTPException(status_code=400, detail="Task already delivered")

    next_code, next_label = TASK_NODE_FLOW[current_index + 1]
    now = _now()

    task.current_node = next_code
    task.current_label = next_label
    task.detail = detail or task.detail
    task.updated_at = now
    db.add(task)

    db.add(
        DispatchTaskEvent(
            task=task,
            node_code=next_code,
            node_label=next_label,
            detail=detail,
            occurred_at=now,
        )
    )

    task_transport = task.transport_order
    if next_code == "delivered":
        all_done = True
        for sibling in task_transport.tasks:
            if sibling.task_no == task.task_no:
                continue
            if sibling.current_node != "delivered":
                all_done = False
                break
        if all_done:
            task_transport.status = "completed"
            task_transport.updated_at = now
            db.add(task_transport)
    else:
        task_transport.status = "in_progress"
        task_transport.updated_at = now
        db.add(task_transport)

    db.commit()
    db.refresh(task)
    _ = task.events
    _ = task.transport_order
    return task


@app.get("/api/v1/logistics/health")
def health() -> dict:
    return {"ok": True, "service": "logistics", "database": DATABASE_URL}


@app.post("/api/v1/logistics/traces", response_model=TraceRead)
def create_trace(payload: TraceCreateRequest) -> TraceRead:
    with SessionLocal() as db:
        exists = db.scalar(select(Trace).where(Trace.order_no == payload.order_no))
        if exists:
            _ = exists.events
            return _to_trace_read(exists)

        now = _now()
        first_code, first_label = STEP_FLOW[0]
        trace = Trace(
            trace_no=_gen_no("LGS"),
            order_no=payload.order_no,
            order_id=payload.order_id,
            carrier=payload.carrier,
            tracking_no=payload.tracking_no,
            current_step=first_code,
            current_label=first_label,
            created_at=now,
            updated_at=now,
        )
        db.add(trace)
        db.flush()
        db.add(
            TraceEvent(
                trace_id=trace.id,
                step_code=first_code,
                step_label=first_label,
                detail="支付完成，物流系统已接单",
                occurred_at=now,
            )
        )

        # 支付成功事件自动进入物流履约主流程（暂存单->计划单->运输单）
        intake = _ensure_intake_by_order_no(db, order_no=payload.order_no)
        plan = _create_plan_for_intake(db, intake=intake)
        _convert_plan_to_transport(db, plan=plan)

        db.commit()
        db.refresh(trace)
        _ = trace.events
        return _to_trace_read(trace)


@app.get("/api/v1/logistics/traces/{trace_no}", response_model=TraceRead)
def get_trace(trace_no: str) -> TraceRead:
    with SessionLocal() as db:
        trace = _get_trace_or_404(db, trace_no=trace_no)
        return _to_trace_read(trace)


@app.get("/api/v1/logistics/orders/{order_no}", response_model=TraceRead)
def get_trace_by_order(order_no: str) -> TraceRead:
    with SessionLocal() as db:
        trace = db.scalar(select(Trace).where(Trace.order_no == order_no))
        if not trace:
            raise HTTPException(status_code=404, detail="Trace not found")
        _ = trace.events
        return _to_trace_read(trace)


@app.post("/api/v1/logistics/traces/{trace_no}/advance", response_model=TraceRead)
def advance_trace(trace_no: str, payload: TraceAdvanceRequest) -> TraceRead:
    with SessionLocal() as db:
        trace = _get_trace_or_404(db, trace_no=trace_no)
        updated = _advance_trace(db, trace=trace, detail=payload.detail)
        return _to_trace_read(updated)


@app.post("/api/v1/logistics/intake-orders", response_model=IntakeRead)
def create_intake_order(payload: IntakeCreateRequest) -> IntakeRead:
    with SessionLocal() as db:
        exists = db.scalar(select(CustomerIntakeOrder).where(CustomerIntakeOrder.source_order_no == payload.source_order_no))
        if exists:
            return _to_intake_read(exists)

        now = _now()
        intake = CustomerIntakeOrder(
            intake_no=_gen_no("INT"),
            source_order_no=payload.source_order_no,
            source_platform=payload.source_platform,
            customer_name=payload.customer_name,
            customer_phone=payload.customer_phone,
            customer_address=payload.customer_address,
            demand_note=payload.demand_note,
            status="received",
            created_at=now,
            updated_at=now,
        )
        db.add(intake)
        db.commit()
        db.refresh(intake)
        return _to_intake_read(intake)


@app.get("/api/v1/logistics/intake-orders", response_model=list[IntakeRead])
def list_intake_orders() -> list[IntakeRead]:
    with SessionLocal() as db:
        rows = db.scalars(select(CustomerIntakeOrder).order_by(CustomerIntakeOrder.created_at.desc()).limit(200)).all()
        return [_to_intake_read(item) for item in rows]


@app.post("/api/v1/logistics/intake-orders/{intake_no}/plan", response_model=PlanRead)
def create_plan_order(intake_no: str, payload: PlanCreateRequest) -> PlanRead:
    with SessionLocal() as db:
        intake = _get_intake_or_404(db, intake_no=intake_no)
        plan = db.scalar(select(PlannedOrder).where(PlannedOrder.intake_id == intake.id))
        if not plan:
            now = _now()
            plan = PlannedOrder(
                planned_no=_gen_no("PLN"),
                intake_id=intake.id,
                status="scheduled",
                estimated_pickup_at=payload.estimated_pickup_at or (now + timedelta(hours=2)),
                estimated_delivery_at=payload.estimated_delivery_at or (now + timedelta(days=2)),
                resource_snapshot=payload.resource_snapshot,
                created_at=now,
                updated_at=now,
            )
            intake.status = "planned"
            intake.updated_at = now
            db.add(intake)
            db.add(plan)
            db.commit()
            db.refresh(plan)
        _ = plan.intake
        return _to_plan_read(plan)


@app.get("/api/v1/logistics/planned-orders", response_model=list[PlanRead])
def list_planned_orders() -> list[PlanRead]:
    with SessionLocal() as db:
        rows = db.scalars(select(PlannedOrder).order_by(PlannedOrder.created_at.desc()).limit(200)).all()
        for row in rows:
            _ = row.intake
        return [_to_plan_read(item) for item in rows]


@app.post("/api/v1/logistics/planned-orders/{planned_no}/convert", response_model=TransportRead)
def convert_plan_to_transport(planned_no: str) -> TransportRead:
    with SessionLocal() as db:
        plan = _get_plan_or_404(db, planned_no=planned_no)
        transport = _convert_plan_to_transport(db, plan=plan)
        db.commit()
        db.refresh(transport)
        _ = transport.planned_order
        return _to_transport_read(transport)


@app.get("/api/v1/logistics/transport-orders", response_model=list[TransportRead])
def list_transport_orders() -> list[TransportRead]:
    with SessionLocal() as db:
        rows = db.scalars(select(TransportOrder).order_by(TransportOrder.created_at.desc()).limit(200)).all()
        for row in rows:
            _ = row.planned_order
        return [_to_transport_read(item) for item in rows]


@app.post("/api/v1/logistics/transport-orders/{transport_no}/dispatch", response_model=DispatchTaskRead)
def dispatch_transport_task(transport_no: str, payload: DispatchCreateRequest) -> DispatchTaskRead:
    with SessionLocal() as db:
        transport = _get_transport_or_404(db, transport_no=transport_no)

        now = _now()
        first_code, first_label = TASK_NODE_FLOW[0]
        task = DispatchTask(
            task_no=_gen_no("TSK"),
            transport_id=transport.id,
            assignment_type=payload.assignment_type,
            assignee_name=payload.assignee_name,
            assignee_code=payload.assignee_code,
            current_node=first_code,
            current_label=first_label,
            detail=payload.detail,
            created_at=now,
            updated_at=now,
        )
        transport.status = "dispatching"
        transport.updated_at = now
        db.add(transport)
        db.add(task)
        db.flush()
        db.add(
            DispatchTaskEvent(
                task_id=task.id,
                node_code=first_code,
                node_label=first_label,
                detail=payload.detail,
                occurred_at=now,
            )
        )
        db.commit()
        db.refresh(task)
        _ = task.events
        _ = task.transport_order
        return _to_task_read(task)


@app.get("/api/v1/logistics/tasks", response_model=list[DispatchTaskRead])
def list_tasks() -> list[DispatchTaskRead]:
    with SessionLocal() as db:
        rows = db.scalars(select(DispatchTask).order_by(DispatchTask.created_at.desc()).limit(300)).all()
        for row in rows:
            _ = row.transport_order
            _ = row.events
        return [_to_task_read(item) for item in rows]


@app.get("/api/v1/logistics/tasks/{task_no}", response_model=DispatchTaskRead)
def get_task(task_no: str) -> DispatchTaskRead:
    with SessionLocal() as db:
        task = _get_task_or_404(db, task_no=task_no)
        return _to_task_read(task)


@app.post("/api/v1/logistics/tasks/{task_no}/advance", response_model=DispatchTaskRead)
def advance_task(task_no: str, payload: TaskAdvanceRequest) -> DispatchTaskRead:
    with SessionLocal() as db:
        task = _get_task_or_404(db, task_no=task_no)
        updated = _advance_task(db, task=task, detail=payload.detail)
        return _to_task_read(updated)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> str:
    return """
<!doctype html>
<html lang='zh-CN'>
  <head>
    <meta charset='utf-8'>
    <meta name='viewport' content='width=device-width,initial-scale=1'>
    <title>物流系统控制台</title>
    <style>
      :root {
        --bg: #f4f6fb;
        --card: #ffffff;
        --line: #e3e8f5;
        --text: #1e2435;
        --muted: #63708d;
        --accent: #1f4eea;
      }
      * { box-sizing: border-box; }
      body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); }
      .wrap { max-width: 1480px; margin: 0 auto; padding: 16px; }
      .topbar { background: linear-gradient(125deg, #14264d, #1f4eea); color: #fff; border-radius: 16px; padding: 18px 20px; box-shadow: 0 14px 34px rgba(17,34,79,.25); }
      .topbar h1 { margin: 0; font-size: 24px; }
      .topbar p { margin: 8px 0 0; opacity: .9; }
      .layout { margin-top: 12px; display: grid; grid-template-columns: 220px 1fr; gap: 12px; }
      .sidebar { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 10px; height: fit-content; box-shadow: 0 10px 24px rgba(28,38,64,.06); }
      .nav-btn { width: 100%; text-align: left; margin-bottom: 8px; border-radius: 10px; border: 1px solid #dde3f0; padding: 10px 11px; background: #fff; color: #25304a; font-size: 14px; cursor: pointer; }
      .nav-btn:last-child { margin-bottom: 0; }
      .nav-btn.active { background: #eef3ff; border-color: #cfdcff; color: #1d43b3; font-weight: 600; }
      .module { display: none; }
      .module.active { display: block; }
      .module-panel { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 14px; box-shadow: 0 10px 24px rgba(28,38,64,.06); min-height: calc(100vh - 170px); }
      .module-title { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 10px; }
      .module-title h2 { margin: 0; font-size: 19px; }
      .module-sub { margin: 0; color: var(--muted); font-size: 13px; }
      .cards { margin-top: 12px; display: grid; gap: 12px; grid-template-columns: repeat(4, minmax(0,1fr)); }
      .card { border: 1px solid #d9e3ff; background: linear-gradient(135deg, #f8fbff, #eef3ff); border-radius: 12px; padding: 12px; }
      .card p { margin: 0; color: #4d5d8d; font-size: 12px; }
      .card b { display: block; margin-top: 6px; font-size: 28px; color: #1c2747; }
      .process { margin-top: 12px; display: grid; gap: 10px; grid-template-columns: repeat(4, minmax(0,1fr)); }
      .process div { border: 1px dashed #c7d4fb; background: #f7f9ff; border-radius: 10px; padding: 10px; color: #2f3f6f; font-size: 13px; }
      .toolbar { display: flex; gap: 8px; flex-wrap: wrap; margin: 10px 0; }
      input, select, button { border-radius: 9px; border: 1px solid #d7dced; padding: 8px 10px; font-size: 13px; }
      button { cursor: pointer; background: #fff; }
      button.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
      button.ghost { background: #f8faff; }
      .table-shell { border: 1px solid #e8edf9; border-radius: 10px; overflow: hidden; background: #fff; }
      .table-scroll { max-height: calc(100vh - 330px); overflow: auto; }
      table { width: 100%; min-width: 980px; border-collapse: collapse; font-size: 13px; }
      th, td { border-bottom: 1px solid #edf0f8; padding: 9px 8px; text-align: left; vertical-align: top; white-space: nowrap; }
      th { color: var(--muted); font-weight: 600; background: #fafcff; position: sticky; top: 0; z-index: 1; }
      .status { display: inline-block; padding: 2px 8px; border-radius: 999px; background: #eef3ff; color: #2644aa; border: 1px solid #dce6ff; }
      .hint { color: var(--muted); font-size: 12px; margin-bottom: 8px; }
      .toast { position: fixed; right: 14px; bottom: 14px; background: #121a2a; color: #fff; padding: 10px 12px; border-radius: 10px; font-size: 13px; opacity: 0; transform: translateY(8px); transition: all .2s ease; pointer-events: none; }
      .toast.show { opacity: 1; transform: translateY(0); }
      @media (max-width: 1180px) {
        .layout { grid-template-columns: 1fr; }
        .sidebar { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 8px; }
        .nav-btn { margin-bottom: 0; }
        .cards { grid-template-columns: 1fr 1fr; }
        .process { grid-template-columns: 1fr 1fr; }
        .module-panel { min-height: auto; }
      }
      @media (max-width: 760px) {
        .sidebar { grid-template-columns: 1fr 1fr; }
        .cards { grid-template-columns: 1fr; }
        .process { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <div class='wrap'>
      <div class='topbar'>
        <h1>物流系统控制台</h1>
        <p>总览 / 客户暂存单 / 计划订单 / 运输订单 / 调度中心</p>
      </div>

      <div class='layout'>
        <aside class='sidebar'>
          <button class='nav-btn active' data-module='overview'>总览</button>
          <button class='nav-btn' data-module='intake'>客户暂存单</button>
          <button class='nav-btn' data-module='plan'>计划订单</button>
          <button class='nav-btn' data-module='transport'>运输订单</button>
          <button class='nav-btn' data-module='dispatch'>调度中心</button>
        </aside>

        <main>
          <section id='module-overview' class='module active'>
            <div class='module-panel'>
              <div class='module-title'>
                <div>
                  <h2>主页总览</h2>
                  <p class='module-sub'>核心数据与流程概览</p>
                </div>
                <button class='ghost' onclick='loadAll()'>刷新数据</button>
              </div>

              <div class='cards'>
                <div class='card'><p>客户暂存单</p><b id='kpiIntake'>0</b></div>
                <div class='card'><p>计划订单</p><b id='kpiPlan'>0</b></div>
                <div class='card'><p>运输订单</p><b id='kpiTransport'>0</b></div>
                <div class='card'><p>调度任务</p><b id='kpiTask'>0</b></div>
              </div>

              <div class='process'>
                <div>1. 客户暂存单<br>接收商城订单需求</div>
                <div>2. 计划订单<br>资源评估和预计送达</div>
                <div>3. 运输订单<br>转入实际履约执行</div>
                <div>4. 调度中心任务<br>推进已接单/提货/送达</div>
              </div>

              <div class='toolbar'>
                <button onclick="switchModule('intake')">客户暂存单</button>
                <button onclick="switchModule('plan')">计划订单</button>
                <button onclick="switchModule('transport')">运输订单</button>
                <button onclick="switchModule('dispatch')">调度中心</button>
              </div>
            </div>
          </section>

          <section id='module-intake' class='module'>
            <div class='module-panel'>
              <div class='module-title'>
                <div>
                  <h2>客户暂存单</h2>
                  <p class='module-sub'>客户需求单据</p>
                </div>
                <button class='ghost' onclick='loadAll()'>刷新</button>
              </div>
              <div class='toolbar'>
                <input id='newSourceOrderNo' placeholder='source_order_no，例如 ORD-20260416-ABCD1234' style='min-width:300px;'>
                <button class='primary' onclick='createIntake()'>创建暂存单</button>
              </div>
              <div class='table-shell'>
                <div class='table-scroll'>
                  <table>
                    <thead><tr><th>暂存单号</th><th>来源订单</th><th>状态</th><th>更新时间</th><th>操作</th></tr></thead>
                    <tbody id='intakeBody'></tbody>
                  </table>
                </div>
              </div>
            </div>
          </section>

          <section id='module-plan' class='module'>
            <div class='module-panel'>
              <div class='module-title'>
                <div>
                  <h2>计划订单</h2>
                  <p class='module-sub'>按资源能力安排预计提货/送达时间</p>
                </div>
                <button class='ghost' onclick='loadAll()'>刷新</button>
              </div>
              <div class='table-shell'>
                <div class='table-scroll'>
                  <table>
                    <thead><tr><th>计划单号</th><th>暂存单号</th><th>状态</th><th>预计送达</th><th>操作</th></tr></thead>
                    <tbody id='planBody'></tbody>
                  </table>
                </div>
              </div>
            </div>
          </section>

          <section id='module-transport' class='module'>
            <div class='module-panel'>
              <div class='module-title'>
                <div>
                  <h2>运输订单</h2>
                  <p class='module-sub'>代表实际履约执行，支持下发调度</p>
                </div>
                <button class='ghost' onclick='loadAll()'>刷新</button>
              </div>
              <div class='toolbar'>
                <select id='dispatchType'>
                  <option value='supplier'>派给供应商</option>
                  <option value='internal_driver'>派给内部司机</option>
                </select>
                <input id='dispatchAssignee' placeholder='调度对象名称（例如 王师傅 / 顺丰承运商）' style='min-width:260px;'>
              </div>
              <div class='table-shell'>
                <div class='table-scroll'>
                  <table>
                    <thead><tr><th>运输单号</th><th>计划单号</th><th>状态</th><th>调度中心</th><th>操作</th></tr></thead>
                    <tbody id='transportBody'></tbody>
                  </table>
                </div>
              </div>
            </div>
          </section>

          <section id='module-dispatch' class='module'>
            <div class='module-panel'>
              <div class='module-title'>
                <div>
                  <h2>调度中心</h2>
                  <p class='module-sub'>任务统一四节点：已派单 → 已接单 → 已提货/提箱 → 已送达</p>
                </div>
                <button class='ghost' onclick='loadAll()'>刷新</button>
              </div>
              <div class='table-shell'>
                <div class='table-scroll'>
                  <table>
                    <thead><tr><th>任务单号</th><th>运输单号</th><th>分派对象</th><th>当前节点</th><th>最近说明</th><th>操作</th></tr></thead>
                    <tbody id='taskBody'></tbody>
                  </table>
                </div>
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>

    <div id='toast' class='toast'></div>

    <script>
      function switchModule(moduleName) {
        document.querySelectorAll('.module').forEach((el) => el.classList.remove('active'));
        document.querySelectorAll('.nav-btn').forEach((btn) => btn.classList.remove('active'));
        const target = document.getElementById(`module-${moduleName}`);
        const btn = document.querySelector(`.nav-btn[data-module="${moduleName}"]`);
        if (target) target.classList.add('active');
        if (btn) btn.classList.add('active');
        window.location.hash = moduleName;
      }

      document.querySelectorAll('.nav-btn').forEach((btn) => {
        btn.addEventListener('click', () => switchModule(btn.getAttribute('data-module')));
      });

      const hashModule = window.location.hash.replace('#', '');
      if (hashModule) switchModule(hashModule);

      function showToast(msg) {
        const el = document.getElementById('toast');
        el.textContent = msg;
        el.classList.add('show');
        setTimeout(() => el.classList.remove('show'), 1600);
      }

      async function api(path, options) {
        const res = await fetch('/api/v1/logistics' + path, {
          method: options?.method || 'GET',
          headers: options?.body ? { 'Content-Type': 'application/json' } : undefined,
          body: options?.body ? JSON.stringify(options.body) : undefined,
        });
        if (!res.ok) {
          const raw = await res.text();
          throw new Error(raw || ('HTTP ' + res.status));
        }
        return res.json();
      }

      function td(text) {
        const s = String(text ?? '');
        return s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
      }

      async function loadAll() {
        const [intakes, plans, transports, tasks] = await Promise.all([
          api('/intake-orders'),
          api('/planned-orders'),
          api('/transport-orders'),
          api('/tasks'),
        ]);

        document.getElementById('kpiIntake').textContent = intakes.length;
        document.getElementById('kpiPlan').textContent = plans.length;
        document.getElementById('kpiTransport').textContent = transports.length;
        document.getElementById('kpiTask').textContent = tasks.length;

        document.getElementById('intakeBody').innerHTML = intakes.map(row =>
          `<tr>
            <td>${td(row.intake_no)}</td>
            <td>${td(row.source_order_no)}</td>
            <td><span class='status'>${td(row.status)}</span></td>
            <td>${new Date(row.updated_at).toLocaleString()}</td>
            <td><button onclick="planFromIntake('${td(row.intake_no)}')">生成计划单</button></td>
          </tr>`
        ).join('') || `<tr><td colspan='5'>暂无数据</td></tr>`;

        document.getElementById('planBody').innerHTML = plans.map(row =>
          `<tr>
            <td>${td(row.planned_no)}</td>
            <td>${td(row.intake_no)}</td>
            <td><span class='status'>${td(row.status)}</span></td>
            <td>${row.estimated_delivery_at ? new Date(row.estimated_delivery_at).toLocaleString() : '-'}</td>
            <td><button onclick="convertPlan('${td(row.planned_no)}')">转运输单</button></td>
          </tr>`
        ).join('') || `<tr><td colspan='5'>暂无数据</td></tr>`;

        document.getElementById('transportBody').innerHTML = transports.map(row =>
          `<tr>
            <td>${td(row.transport_no)}</td>
            <td>${td(row.planned_no)}</td>
            <td><span class='status'>${td(row.status)}</span></td>
            <td>${td(row.dispatch_center)}</td>
            <td><button onclick="dispatch('${td(row.transport_no)}')">下发调度</button></td>
          </tr>`
        ).join('') || `<tr><td colspan='5'>暂无数据</td></tr>`;

        document.getElementById('taskBody').innerHTML = tasks.map(row =>
          `<tr>
            <td>${td(row.task_no)}</td>
            <td>${td(row.transport_no)}</td>
            <td>${td(row.assignment_type)} / ${td(row.assignee_name)}</td>
            <td><span class='status'>${td(row.current_label)}</span></td>
            <td>${td(row.detail || '-')}</td>
            <td><button onclick="advanceTask('${td(row.task_no)}')">推进节点</button></td>
          </tr>`
        ).join('') || `<tr><td colspan='6'>暂无数据</td></tr>`;
      }

      async function createIntake() {
        const sourceOrderNo = document.getElementById('newSourceOrderNo').value.trim();
        if (!sourceOrderNo) {
          showToast('请先输入 source_order_no');
          return;
        }
        await api('/intake-orders', {
          method: 'POST',
          body: {
            source_order_no: sourceOrderNo,
            demand_note: '手工录入：来自控制台'
          }
        });
        showToast('暂存单创建完成');
        await loadAll();
      }

      async function planFromIntake(intakeNo) {
        await api(`/intake-orders/${intakeNo}/plan`, { method: 'POST', body: {} });
        showToast('计划订单已生成');
        await loadAll();
      }

      async function convertPlan(plannedNo) {
        await api(`/planned-orders/${plannedNo}/convert`, { method: 'POST' });
        showToast('已转为运输订单');
        await loadAll();
      }

      async function dispatch(transportNo) {
        const type = document.getElementById('dispatchType').value;
        const assignee = document.getElementById('dispatchAssignee').value.trim();
        if (!assignee) {
          showToast('请填写调度对象名称');
          return;
        }
        await api(`/transport-orders/${transportNo}/dispatch`, {
          method: 'POST',
          body: {
            assignment_type: type,
            assignee_name: assignee,
            detail: '调度中心派单成功'
          }
        });
        showToast('调度任务已创建');
        switchModule('dispatch');
        await loadAll();
      }

      async function advanceTask(taskNo) {
        await api(`/tasks/${taskNo}/advance`, { method: 'POST', body: { detail: '控制台手工推进' } });
        showToast('任务节点已推进');
        await loadAll();
      }

      loadAll().catch(err => {
        console.error(err);
        showToast('加载失败，请检查服务');
      });
    </script>
  </body>
</html>
"""


@app.get("/dashboard/traces/{trace_no}", response_class=HTMLResponse)
def dashboard_trace_detail(trace_no: str) -> str:
    with SessionLocal() as db:
        trace = _get_trace_or_404(db, trace_no=trace_no)

    event_lines = "".join(
        f"<li>{_format_iso(event.occurred_at)} · {html.escape(event.step_label)} · {html.escape(event.detail or '')}</li>"
        for event in trace.events
    )

    return f"""
<!doctype html>
<html lang='zh-CN'>
  <head>
    <meta charset='utf-8'>
    <meta name='viewport' content='width=device-width,initial-scale=1'>
    <title>物流详情 - {html.escape(trace.trace_no)}</title>
  </head>
  <body style='font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; background:#f5f7fb;'>
    <div style='max-width:960px;margin:24px auto;padding:14px;'>
      <div style='background:#fff;border:1px solid #e4e8f2;border-radius:14px;padding:16px;'>
        <h2 style='margin:0 0 8px;'>物流详情：{html.escape(trace.trace_no)}</h2>
        <p>订单号：{html.escape(trace.order_no)}</p>
        <p>运单号：{html.escape(trace.tracking_no)}</p>
        <p>当前节点：{html.escape(trace.current_label)}</p>
        <h3>轨迹</h3>
        <ul>{event_lines}</ul>
        <form method='post' action='/dashboard/traces/{html.escape(trace.trace_no)}/advance' style='display:flex;gap:8px;'>
          <input name='detail' placeholder='推进说明（可选）' style='padding:8px 10px;border:1px solid #d7dced;border-radius:8px;min-width:260px;'>
          <button type='submit' style='padding:8px 10px;border:1px solid #d7dced;border-radius:8px;background:#fff;'>推进到下一节点</button>
          <a href='/dashboard' style='padding:8px 10px;border:1px solid #d7dced;border-radius:8px;background:#fff;text-decoration:none;color:#111;'>返回控制台</a>
        </form>
      </div>
    </div>
  </body>
</html>
"""


@app.post("/dashboard/traces/{trace_no}/advance")
def dashboard_trace_advance(trace_no: str, detail: str = Form(default="")) -> RedirectResponse:
    with SessionLocal() as db:
        trace = _get_trace_or_404(db, trace_no=trace_no)
        _advance_trace(db, trace=trace, detail=detail)
    return RedirectResponse(url=f"/dashboard/traces/{trace_no}", status_code=303)
