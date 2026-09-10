from app.database import Base, engine, SessionLocal
from app.db_models import TaskDB, UserDB
from app.auth import hash_password
from app.simulator import generate_sections, generate_tasks

Base.metadata.create_all(bind=engine)
db = SessionLocal()

if db.query(UserDB).count() == 0:
    users = [
        UserDB(username="admin", hashed_password=hash_password("admin123"), role="admin", full_name="Planning Officer"),
        UserDB(username="engineer1", hashed_password=hash_password("pass123"), role="department", department="Engineering (P.Way)", full_name="P.Way Official"),
        UserDB(username="signal1", hashed_password=hash_password("pass123"), role="department", department="Signal & Telecommunication (S&T)", full_name="S&T Official"),
        UserDB(username="traction1", hashed_password=hash_password("pass123"), role="department", department="Traction Distribution (TRD)", full_name="TRD Official"),
        UserDB(username="crew1", hashed_password=hash_password("pass123"), role="field_crew", full_name="Field Crew Member"),
    ]
    db.add_all(users)
    db.commit()
    print("Seeded 5 users (admin/admin123, engineer1/pass123, signal1/pass123, traction1/pass123, crew1/pass123)")
else:
    print("Users already exist, skipping user seed")

if db.query(TaskDB).count() == 0:
    sections = generate_sections()
    tasks = generate_tasks(sections, count=15)
    for t in tasks:
        db.add(TaskDB(
            task_id=t.task_id,
            department=t.department.value,
            section_id=t.section_id,
            defect_type=t.defect_type,
            urgency=t.urgency.value,
            overdue_days=t.overdue_days,
            estimated_duration_hours=t.estimated_duration_hours,
            status="Pending",
            created_by="system",
        ))
    db.commit()
    print(f"Seeded {len(tasks)} starter tasks")
else:
    print("Tasks already exist, skipping task seed")

db.close()
print("Database ready: block_planning.db")