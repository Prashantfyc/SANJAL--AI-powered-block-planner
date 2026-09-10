from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime


class Department(str, Enum):
    ENGINEERING = "Engineering (P.Way)"
    SIGNAL = "Signal & Telecommunication (S&T)"
    TRACTION = "Traction Distribution (TRD)"


class Urgency(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class TaskStatus(str, Enum):
    PENDING = "Pending"
    SCHEDULED = "Scheduled"
    DONE = "Done"


class TrainType(str, Enum):
    PASSENGER = "Passenger"
    GOODS = "Goods"


class BlockType(str, Enum):
    TRAFFIC_BLOCK = "Traffic Block"
    POWER_BLOCK = "Power Block"
    INTEGRATED_BLOCK = "Integrated Block"


class Section(BaseModel):
    section_id: str
    name: str
    connects: List[str]


class MaintenanceTask(BaseModel):
    task_id: str
    department: Department
    section_id: str
    defect_type: str
    urgency: Urgency
    overdue_days: int
    estimated_duration_hours: float
    status: TaskStatus = TaskStatus.PENDING
    priority_score: Optional[float] = None
    score_breakdown: Optional[Dict[str, float]] = None
    reasoning: Optional[str] = None
    completion_photo: Optional[str] = None
    completed_at: Optional[datetime] = None
    completion_lat: Optional[float] = None
    completion_lon: Optional[float] = None


class TimetableSlot(BaseModel):
    section_id: str
    train_id: str
    start_time: datetime
    end_time: datetime
    type: TrainType


class BlockSchedule(BaseModel):
    block_id: str
    section_id: str
    start_time: datetime
    end_time: datetime
    tasks_covered: List[str]
    horizon: str
    block_type: BlockType
    reasoning: Optional[str] = None