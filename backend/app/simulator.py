import random
from datetime import datetime, timedelta
from app.models import (
    Section, MaintenanceTask, TimetableSlot,
    Department, Urgency, TaskStatus, TrainType
)


def generate_sections() -> list[Section]:
    return [
        Section(section_id="SEC1", name="Ludhiana-Jalandhar", connects=["Ludhiana", "Jalandhar"]),
        Section(section_id="SEC2", name="Jalandhar-Amritsar", connects=["Jalandhar", "Amritsar"]),
        Section(section_id="SEC3", name="Ludhiana-Chandigarh", connects=["Ludhiana", "Chandigarh"]),
        Section(section_id="SEC4", name="Chandigarh-Ambala", connects=["Chandigarh", "Ambala"]),
    ]


def generate_tasks(sections: list[Section], count: int = 15) -> list[MaintenanceTask]:
    defect_types = {
        Department.ENGINEERING: [
            "Rail fracture", "Rail crack", "Ballast deficiency", "Track geometry defect", "Weld failure"
        ],
        Department.SIGNAL: [
            "Signal failure", "Point failure", "Track circuit failure", "Cable fault", "Interlocking defect"
        ],
        Department.TRACTION: [
            "OHE wire wear", "Insulator flashover", "Feeder fault", "OHE tension defect", "Traction pole damage"
        ],
    }

    tasks = []
    for i in range(count):
        department = random.choice(list(Department))
        section = random.choice(sections)
        urgency = random.choices(
            list(Urgency),
            weights=[30, 35, 25, 10],  # Low, Medium, High, Critical
        )[0]
        overdue_days = random.randint(0, 20) if urgency in (Urgency.HIGH, Urgency.CRITICAL) else random.randint(0, 5)

        tasks.append(MaintenanceTask(
            task_id=f"TASK{i+1:03d}",
            department=department,
            section_id=section.section_id,
            defect_type=random.choice(defect_types[department]),
            urgency=urgency,
            overdue_days=overdue_days,
            estimated_duration_hours=round(random.uniform(1.5, 6.0), 1),
            status=TaskStatus.PENDING,
        ))
    return tasks


def generate_timetable(sections: list[Section], days: int = 7) -> list[TimetableSlot]:
    slots = []
    base_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    train_counter = 1

    for day in range(days):
        for section in sections:
            # Passenger trains: fixed morning and evening slots
            for hour in [7, 9, 17, 19]:
                start = base_time + timedelta(days=day, hours=hour)
                slots.append(TimetableSlot(
                    section_id=section.section_id,
                    train_id=f"PASS{train_counter:04d}",
                    start_time=start,
                    end_time=start + timedelta(minutes=20),
                    type=TrainType.PASSENGER,
                ))
                train_counter += 1

            # Goods trains: more random, less fixed
            for _ in range(random.randint(2, 4)):
                hour = random.randint(0, 23)
                start = base_time + timedelta(days=day, hours=hour)
                slots.append(TimetableSlot(
                    section_id=section.section_id,
                    train_id=f"GOODS{train_counter:04d}",
                    start_time=start,
                    end_time=start + timedelta(minutes=30),
                    type=TrainType.GOODS,
                ))
                train_counter += 1

    return slots