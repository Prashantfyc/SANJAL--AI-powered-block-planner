from app.models import MaintenanceTask, Urgency

URGENCY_WEIGHT = 3
OVERDUE_WEIGHT = 1
IMPACT_WEIGHT = 2

URGENCY_LEVELS = {
    Urgency.LOW: 1,
    Urgency.MEDIUM: 2,
    Urgency.HIGH: 3,
    Urgency.CRITICAL: 4,
}


def estimate_impact(task: MaintenanceTask) -> float:
    urgency_factor = URGENCY_LEVELS[task.urgency]
    return urgency_factor * (task.estimated_duration_hours / 6.0)


def calculate_priority_score(task: MaintenanceTask):
    urgency_component = round(URGENCY_WEIGHT * URGENCY_LEVELS[task.urgency], 2)
    overdue_component = round(OVERDUE_WEIGHT * task.overdue_days, 2)
    impact_component = round(IMPACT_WEIGHT * estimate_impact(task), 2)

    total = round(urgency_component + overdue_component + impact_component, 2)
    breakdown = {
        "urgency_component": urgency_component,
        "overdue_component": overdue_component,
        "impact_component": impact_component,
    }

    reasoning = (
        f"{task.urgency.value} urgency contributes {urgency_component} pts "
        f"({URGENCY_WEIGHT} x urgency level {URGENCY_LEVELS[task.urgency]}). "
        f"{task.overdue_days} day(s) overdue contributes {overdue_component} pts "
        f"({OVERDUE_WEIGHT} x overdue days). "
        f"Estimated impact on asset availability contributes {impact_component} pts "
        f"({IMPACT_WEIGHT} x urgency-weighted duration). "
        f"Total priority score: {total}."
    )

    return total, breakdown, reasoning


def score_all_tasks(tasks: list[MaintenanceTask]) -> list[MaintenanceTask]:
    for task in tasks:
        score, breakdown, reasoning = calculate_priority_score(task)
        task.priority_score = score
        task.score_breakdown = breakdown
        task.reasoning = reasoning
    return tasks


def rank_tasks(tasks: list[MaintenanceTask]) -> list[MaintenanceTask]:
    scored = score_all_tasks(tasks)
    return sorted(scored, key=lambda t: t.priority_score, reverse=True)