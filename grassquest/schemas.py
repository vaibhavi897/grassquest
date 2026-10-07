"""Validated data models returned by the local language model."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, field_validator

Category = Literal["Look", "Listen", "Touch-safe", "Smell-safe", "Move", "Photo"]


class QuestTask(BaseModel):
    instruction: str = Field(min_length=5, max_length=180)
    category: Category
    fun_hint: str = Field(min_length=3, max_length=120)


class Quest(BaseModel):
    title: str = Field(min_length=3, max_length=90)
    estimated_time: int = Field(ge=15, le=90)
    tasks: list[QuestTask] = Field(min_length=8, max_length=8)

    @field_validator("tasks")
    @classmethod
    def require_variety_and_no_equipment(cls, tasks: list[QuestTask]) -> list[QuestTask]:
        categories = [task.category for task in tasks]
        if categories.count("Photo") > 2:
            raise ValueError("At most two tasks may be Photo tasks")
        if categories.count("Move") < 1:
            raise ValueError("At least one task must be Move")
        if categories.count("Listen") + categories.count("Look") < 2:
            raise ValueError("At least two tasks must be Listen or Look")
        return tasks


class PhotoCheck(BaseModel):
    description: str = Field(min_length=2, max_length=350)
    match: Literal["Yes", "Maybe", "No"]
    confidence: Literal["Low", "Medium", "High"]


def parse_quest_text(raw: str, estimated_time: int = 30) -> Quest:
    """Tolerantly parse a plain-text model fallback into eight safe task rows."""
    import json
    import re

    try:
        start, end = raw.index("{"), raw.rindex("}") + 1
        data = json.loads(raw[start:end])
        return Quest.model_validate(data)
    except Exception:
        pass
    rows = [line.strip(" -*\t\r") for line in raw.splitlines() if line.strip()]
    title = next((line.lstrip("# ") for line in rows if len(line) < 90), "A Little Outside Quest")
    categories: list[Category] = ["Look", "Listen", "Move", "Touch-safe", "Look", "Smell-safe", "Photo", "Listen"]
    tasks: list[QuestTask] = []
    for i, row in enumerate([r for r in rows if len(r) > 12][:8]):
        instruction = re.sub(r"^\d+[.)]\s*", "", row)[:180]
        tasks.append(QuestTask(instruction=instruction, category=categories[i], fun_hint="Notice what makes this moment different."))
    defaults = [
        "Notice a shape in the surroundings that catches your eye.", "Pause and listen for a sound that repeats.",
        "Take a gentle stretch while staying in a safe, open spot.", "From the path, notice a texture without touching it.",
        "Find a patch of light and shadow nearby.", "Notice an outdoor scent without touching or tasting anything.",
        "Take a photo of a detail you would like to remember.", "Listen for the quietest sound you can hear.",
    ]
    while len(tasks) < 8:
        i = len(tasks)
        tasks.append(QuestTask(instruction=defaults[i], category=categories[i], fun_hint="A small detail can make an ordinary walk feel new."))
    return Quest(title=title, estimated_time=estimated_time, tasks=tasks)
