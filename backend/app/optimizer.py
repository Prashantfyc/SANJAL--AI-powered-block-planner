from datetime import datetime, timedelta
from ortools.sat.python import cp_model
from app.models import MaintenanceTask, Section, BlockSchedule, BlockType, Department


def generate_candidate_windows(sections: list[Section], days: int = 7, capacity_hours: float = 4.0):
    base_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    windows = []
    window_counter = 1

    for day in range(days):
        for section in sections:
            start = base_time + timedelta(days=day, hours=0)
            end = start + timedelta(hours=capacity_hours)
            windows.append({
                "window_id": f"WIN{window_counter:04d}",
                "section_id": section.section_id,
                "start_time": start,
                "end_time": end,
                "capacity_hours": capacity_hours,
            })
            window_counter += 1

    return windows


def optimize_schedule(
    tasks: list[MaintenanceTask],
    windows: list[dict],
    horizon: str = "Weekly",
) -> list[BlockSchedule]:
    model = cp_model.CpModel()

    pending_tasks = [t for t in tasks if getattr(t.status, "value", t.status) == "Pending"]

    x = {}
    for task in pending_tasks:
        eligible_windows = [w for w in windows if w["section_id"] == task.section_id]
        for w in eligible_windows:
            x[(task.task_id, w["window_id"])] = model.NewBoolVar(f"x_{task.task_id}_{w['window_id']}")

    for task in pending_tasks:
        relevant_vars = [x[(task.task_id, w["window_id"])] for w in windows if (task.task_id, w["window_id"]) in x]
        if relevant_vars:
            model.Add(sum(relevant_vars) <= 1)

    for w in windows:
        relevant_vars = [
            (x[(task.task_id, w["window_id"])], task.estimated_duration_hours)
            for task in pending_tasks
            if (task.task_id, w["window_id"]) in x
        ]
        if relevant_vars:
            model.Add(
                sum(var * int(dur * 10) for var, dur in relevant_vars) <= int(w["capacity_hours"] * 10)
            )

    objective_terms = []
    for task in pending_tasks:
        for w in windows:
            if (task.task_id, w["window_id"]) in x:
                score = int((task.priority_score or 0) * 10)
                objective_terms.append(x[(task.task_id, w["window_id"])] * score)
    model.Maximize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    status = solver.Solve(model)

    schedules = []
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        window_assignments = {}
        for (task_id, window_id), var in x.items():
            if solver.Value(var) == 1:
                window_assignments.setdefault(window_id, []).append(task_id)

        block_counter = 1
        for w in windows:
            covered = window_assignments.get(w["window_id"], [])
            if covered:
                covered_tasks = [t for t in pending_tasks if t.task_id in covered]
                departments_involved = {t.department for t in covered_tasks}
                traction_involved = any(t.department == Department.TRACTION for t in covered_tasks)
                used_hours = round(sum(t.estimated_duration_hours for t in covered_tasks), 1)

                if len(departments_involved) > 1:
                    block_type = BlockType.INTEGRATED_BLOCK
                    dept_list = ", ".join(sorted(d.value for d in departments_involved))
                    reasoning = (
                        f"Merged {len(covered_tasks)} tasks from {len(departments_involved)} departments "
                        f"({dept_list}) into one shared window because they target the same section and fit "
                        f"within the {w['capacity_hours']}h capacity (used {used_hours}h). "
                        f"This avoids blocking the section separately for each department."
                    )
                elif traction_involved:
                    block_type = BlockType.POWER_BLOCK
                    reasoning = (
                        f"Flagged as a Power Block because it involves Traction Distribution (TRD) work, "
                        f"which requires disconnecting the overhead traction supply. "
                        f"Uses {used_hours}h of the {w['capacity_hours']}h window."
                    )
                else:
                    block_type = BlockType.TRAFFIC_BLOCK
                    reasoning = (
                        f"Single-department window for {covered_tasks[0].department.value}. "
                        f"Uses {used_hours}h of the {w['capacity_hours']}h window "
                        f"(highest-priority task in this window scored {covered_tasks[0].priority_score})."
                    )

                schedules.append(BlockSchedule(
                    block_id=f"BLK{block_counter:04d}",
                    section_id=w["section_id"],
                    start_time=w["start_time"],
                    end_time=w["end_time"],
                    tasks_covered=covered,
                    horizon=horizon,
                    block_type=block_type,
                    reasoning=reasoning,
                ))
                block_counter += 1

    return schedules