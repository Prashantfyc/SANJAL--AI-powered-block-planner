import os
import uuid
import json
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db, Base, engine
from app.db_models import TaskDB, UserDB, AuditEventDB
from app.auth import (
    verify_password, create_access_token, get_current_user, require_roles
)
from app.simulator import generate_sections
from app.scoring import rank_tasks
from app.optimizer import generate_candidate_windows, optimize_schedule
from app.models import MaintenanceTask, BlockType

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Automatic Block Planning API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

SECTIONS = generate_sections()
WINDOWS = generate_candidate_windows(SECTIONS, days=30)


def task_to_pydantic(t: TaskDB) -> MaintenanceTask:
    breakdown = json.loads(t.score_breakdown) if t.score_breakdown else None
    return MaintenanceTask(
        task_id=t.task_id,
        department=t.department,
        section_id=t.section_id,
        defect_type=t.defect_type,
        urgency=t.urgency,
        overdue_days=t.overdue_days,
        estimated_duration_hours=t.estimated_duration_hours,
        status=t.status,
        priority_score=t.priority_score,
        score_breakdown=breakdown,
        completion_photo=t.completion_photo,
        completed_at=t.completed_at,
        completion_lat=t.completion_lat,
        completion_lon=t.completion_lon,
    )


def score_pending(db: Session) -> list[MaintenanceTask]:
    pending_db = db.query(TaskDB).filter(TaskDB.status == "Pending").all()
    pending_pyd = [task_to_pydantic(t) for t in pending_db]
    ranked = rank_tasks(pending_pyd)

    by_id = {t.task_id: t for t in ranked}
    for t_db in pending_db:
        updated = by_id[t_db.task_id]
        t_db.priority_score = updated.priority_score
        t_db.score_breakdown = json.dumps(updated.score_breakdown)
    db.commit()

    return ranked


def log_event(db: Session, task_id: str, action: str, detail: str, actor: str):
    db.add(AuditEventDB(
        event_id=uuid.uuid4().hex[:8],
        task_id=task_id,
        action=action,
        detail=detail,
        actor=actor,
        timestamp=datetime.now(),
    ))
    db.commit()


@app.post("/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token({"sub": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "department": user.department,
        "full_name": user.full_name,
        "username": user.username,
    }


@app.get("/")
def root():
    return {"message": "Automatic Block Planning API is running"}


@app.get("/tasks")
def get_tasks(db: Session = Depends(get_db), user: UserDB = Depends(get_current_user)):
    return score_pending(db)


@app.get("/tasks/completed")
def get_completed_tasks(db: Session = Depends(get_db), user: UserDB = Depends(get_current_user)):
    rows = db.query(TaskDB).filter(TaskDB.status == "Done").all()
    return [task_to_pydantic(t) for t in rows]


@app.get("/sections")
def get_sections(user: UserDB = Depends(get_current_user)):
    return SECTIONS


@app.get("/schedule/weekly")
def get_weekly_schedule(db: Session = Depends(get_db), user: UserDB = Depends(get_current_user)):
    ranked = score_pending(db)
    weekly_windows = WINDOWS[: 4 * len(SECTIONS)]
    return optimize_schedule(ranked, weekly_windows, horizon="Weekly")


@app.get("/schedule/monthly")
def get_monthly_schedule(db: Session = Depends(get_db), user: UserDB = Depends(get_current_user)):
    ranked = score_pending(db)
    return optimize_schedule(ranked, WINDOWS, horizon="Monthly")


@app.get("/audit")
def get_audit_log(db: Session = Depends(get_db), user: UserDB = Depends(require_roles("admin"))):
    rows = db.query(AuditEventDB).order_by(AuditEventDB.timestamp.desc()).limit(50).all()
    return [
        {
            "event_id": e.event_id,
            "task_id": e.task_id,
            "action": e.action,
            "detail": e.detail,
            "actor": e.actor,
            "timestamp": e.timestamp,
        }
        for e in rows
    ]


@app.get("/metrics")
def get_metrics(db: Session = Depends(get_db), user: UserDB = Depends(get_current_user)):
    ranked = score_pending(db)
    completed = db.query(TaskDB).filter(TaskDB.status == "Done").count()
    critical_pending = len([t for t in ranked if t.urgency.value == "Critical"])
    weekly_windows = WINDOWS[: 4 * len(SECTIONS)]
    weekly = optimize_schedule(ranked, weekly_windows, horizon="Weekly")
    integrated = len([b for b in weekly if b.block_type == BlockType.INTEGRATED_BLOCK])
    avg_score = round(sum((t.priority_score or 0) for t in ranked) / len(ranked), 2) if ranked else 0

    tasks_scheduled = sum(len(b.tasks_covered) for b in weekly)
    blocks_saved = max(tasks_scheduled - len(weekly), 0)

    return {
        "pending_tasks": len(ranked),
        "completed_tasks": completed,
        "critical_pending": critical_pending,
        "integrated_blocks": integrated,
        "avg_priority_score": avg_score,
        "blocks_saved": blocks_saved,
    }


@app.post("/tasks/add")
def add_task(
    task: dict,
    db: Session = Depends(get_db),
    user: UserDB = Depends(require_roles("admin", "department")),
):
    department = user.department if user.role == "department" else task.get("department")

    new_task = TaskDB(
        task_id=task.get("task_id") or f"TASK{uuid.uuid4().hex[:6].upper()}",
        department=department,
        section_id=task["section_id"],
        defect_type=task["defect_type"],
        urgency=task["urgency"],
        overdue_days=int(task.get("overdue_days", 0)),
        estimated_duration_hours=float(task["estimated_duration_hours"]),
        status="Pending",
        created_by=user.username,
    )
    db.add(new_task)
    db.commit()
    log_event(db, new_task.task_id, "Created", f"{department} reported {new_task.defect_type}", user.username)
    return {"message": "Task added", "task_id": new_task.task_id}


@app.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    photo: UploadFile = File(...),
    lat: Optional[float] = Form(None),
    lon: Optional[float] = Form(None),
    db: Session = Depends(get_db),
    user: UserDB = Depends(require_roles("admin", "field_crew")),
):
    task = db.query(TaskDB).filter(TaskDB.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    ext = os.path.splitext(photo.filename)[1] or ".jpg"
    filename = f"{task_id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(await photo.read())

    task.status = "Done"
    task.completion_photo = f"/uploads/{filename}"
    task.completed_at = datetime.now()
    task.completion_lat = lat
    task.completion_lon = lon
    db.commit()

    location_note = f" at ({lat:.4f}, {lon:.4f})" if lat and lon else ""
    log_event(db, task_id, "Completed", f"Photo proof uploaded by {user.username}{location_note}", user.username)

    return {"message": "Task marked complete", "photo_url": task.completion_photo}


@app.post("/schedule/regenerate")
def regenerate_schedule(db: Session = Depends(get_db), user: UserDB = Depends(require_roles("admin"))):
    ranked = score_pending(db)
    weekly_windows = WINDOWS[: 4 * len(SECTIONS)]
    weekly = optimize_schedule(ranked, weekly_windows, horizon="Weekly")
    monthly = optimize_schedule(ranked, WINDOWS, horizon="Monthly")
    return {"message": "Schedule regenerated", "weekly_blocks": len(weekly), "monthly_blocks": len(monthly)}