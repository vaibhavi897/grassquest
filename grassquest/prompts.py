"""All short, editable model prompts for GrassQuest."""
from __future__ import annotations

from .schemas import Quest

SAFETY = """Safety: stay on paths and public land; respect private property; avoid roads, water edges, cliffs and trespassing; go in daylight. Never ask anyone to taste, pick, or handle unknown plants, mushrooms, berries, or animals. Never approach or feed wildlife. Make tasks child-appropriate for families. Do not invent species or local nature facts. Keep observations generic. Respect accessibility notes. Never require buying equipment."""
HONESTY = """Describe only what is visibly present. Say 'I can't tell' when unsure. Never name a plant, bird, or animal species with certainty; if useful, hedge clearly (for example, 'possibly ...'). Do not invent events or facts."""


def quest_prompt(*, season: str, place: str, group: str, minutes: int, difficulty: str, note: str = "") -> str:
    return f"""Create one friendly outdoor scavenger quest as JSON matching this schema exactly: {Quest.model_json_schema()}.
Inputs: season={season}; place={place}; group={group}; time={minutes} minutes; difficulty={difficulty}; access/interest note={note or 'none'}.
Return exactly 8 short tasks. Each has instruction, category (Look, Listen, Touch-safe, Smell-safe, Move, Photo), and one-line fun_hint. Include at least 2 Look or Listen tasks, at least 1 Move, at most 2 Photo. Make tasks fit the place, group, time, and access note. Title should be catchy; estimated_time must be the requested minutes. {SAFETY}"""


def photo_prompt(task: str | None) -> str:
    return f"""Look at this outdoor photo. Return JSON with description (brief visible description), match (Yes, Maybe, or No) and confidence (Low, Medium, or High). Attached task: {task or 'No task attached'}. Be conservative: use Maybe when uncertain. {HONESTY}"""


def journal_prompt(quest_title: str, completed: list[str], note: str, descriptions: list[str]) -> str:
    return f"""Write a warm, specific first-person trail journal entry of 100 to 160 words. Use only these facts; do not invent events. Quest: {quest_title}. Completed tasks: {completed}. Walker's note: {note or 'none'}. Visible photo descriptions: {descriptions or 'none'}. Avoid claiming species identity. {HONESTY}"""
