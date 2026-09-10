from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from datetime import datetime
from app.database import Base


class TaskDB(Base):
    __tablename__ = "tasks"

    task_id = Column(String, primary_key=True, index=True)
    department = Column(String, nullable=False)
    section_id = Column(String, nullable=False)
    defect_type = Column(String, nullable=False)
    urgency = Column(String, nullable=False)
    overdue_days = Column(Integer, default=0)
    estimated_duration_hours = Column(Float, nullable=False)
    status = Column(String, default="Pending")
    priority_score = Column(Float, nullable=True)
    score_breakdown = Column(Text, nullable=True)  # stored as JSON string
    completion_photo = Column(String, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    completion_lat = Column(Float, nullable=True)
    completion_lon = Column(Float, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class UserDB(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "admin", "department", "field_crew"
    department = Column(String, nullable=True)
    full_name = Column(String, nullable=True)


class AuditEventDB(Base):
    __tablename__ = "audit_events"

    event_id = Column(String, primary_key=True, index=True)
    task_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    detail = Column(String, nullable=False)
    actor = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)