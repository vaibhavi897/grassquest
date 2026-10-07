"""Local Ollama integration with actionable errors and a conservative fallback."""
from __future__ import annotations

import os
from typing import Any

from ollama import Client
from pydantic import ValidationError

from .prompts import journal_prompt, photo_prompt, quest_prompt
from .schemas import PhotoCheck, Quest, QuestTask, parse_quest_text

DEFAULT_MODEL = os.getenv("GRASSQUEST_MODEL", "gemma3:4b")
HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


class LocalModelError(RuntimeError):
    """Friendly, user-displayable local model error."""


def _client() -> Client:
    return Client(host=HOST, timeout=35)


def health(model: str = DEFAULT_MODEL) -> dict[str, Any]:
    try:
        client = _client()
        models = client.list().models
        names = [getattr(m, "model", "") or getattr(m, "name", "") for m in models]
        return {"connected": True, "installed": any(n == model or n.startswith(model + ":") for n in names), "models": names}
    except Exception as exc:
        return {"connected": False, "installed": False, "models": [], "error": str(exc)}


def _chat(messages: list[dict[str, Any]], model: str, fmt: Any = None) -> str:
    try:
        kwargs: dict[str, Any] = {"model": model, "messages": messages, "stream": False}
        if fmt is not None:
            kwargs["format"] = fmt
        kwargs["options"] = {"num_predict": 96}
        response = _client().chat(**kwargs)
        message = response.message
        return message.content or ""
    except Exception as exc:
        message = str(exc).lower()
        if "connect" in message or "refused" in message or "timed out" in message:
            raise LocalModelError("Can't reach Ollama. Start it with `ollama serve`, then retry.") from exc
        if "not found" in message or "pull" in message:
            raise LocalModelError(f"Model not installed. Run `ollama pull {model}` and retry.") from exc
        if "image" in message or "vision" in message or "unsupported" in message:
            raise LocalModelError(f"This model may not support images. Select a vision-capable model such as gemma3:4b in Settings. ({exc})") from exc
        raise LocalModelError(f"Local model request failed: {exc}") from exc


def generate_quest(*, season: str, place: str, group: str, minutes: int, difficulty: str, note: str = "", model: str = DEFAULT_MODEL) -> Quest:
    # Keep model output deliberately tiny: on CPU a 4B model can take minutes
    # to emit a fully structured eight-task card. The model personalizes a short
    # theme; vetted task templates ensure the complete card is immediate and safe.
    context = f"Season: {season}. Place: {place}. Group: {group}. Time: {minutes} minutes. Difficulty: {difficulty}. Access note: {note or 'none'}."
    try:
        theme = _chat([{"role": "user", "content": f"{context} In at most 8 words, suggest a cheerful, generic theme for a safe outdoor scavenger hunt. No species names, no explanation."}], model)
        theme = " ".join(theme.replace("\n", " ").strip(" #\"'`.*") .split())[:70]
    except LocalModelError:
        # A useful card remains available if local inference is slow or unavailable.
        theme = "A Little Outside Quest"
    return build_quest(season, place, group, minutes, difficulty, note, theme)


def build_quest(season: str, place: str, group: str, minutes: int, difficulty: str, note: str = "", theme: str = "") -> Quest:
    """Build a complete, safe, place-aware quest without another model call."""
    accessibility = (note or "").lower()
    mobility_limited = any(word in accessibility for word in ("wheelchair", "limited mobility", "can't walk", "cannot walk", "balcony", "terrace"))
    family = group == "Family with kids"
    indoors_edge = place == "Terrace or balcony"
    move_task = "From a comfortable spot, slowly turn your head and notice three different views." if mobility_limited else "Walk at an easy pace for two minutes on a clear path, staying well away from roads and edges."
    templates = [
        ("Look", "Find a patch where sunlight and shade meet, from a safe public spot.", "The contrast makes a tiny outdoor scene feel like a picture."),
        ("Listen", "Pause and notice one sound that repeats, then listen for a different sound.", "You may discover a small rhythm in the everyday background."),
        ("Move", move_task, "A gentle change of position helps you notice the place anew."),
        ("Look", "Notice a shape or pattern in the surroundings without leaving the path.", "Repeating lines and unexpected shapes are satisfying to spot."),
        ("Touch-safe", "If you like, feel the texture of your own sleeve, then compare it visually with a nearby surface without touching it.", "A safe texture comparison turns observation into a small puzzle."),
        ("Smell-safe", "Notice a scent in the air from where you are; do not touch or taste anything.", "The air can make one moment feel distinct from the last."),
        ("Photo", "Photograph a color or pattern you would like to remember, without approaching plants or wildlife.", "A close-up of an ordinary detail can become a favorite memory."),
        ("Listen", "Take ten quiet seconds and notice the softest sound you can hear.", "A short pause can reveal sounds hidden by the louder ones."),
    ]
    if indoors_edge:
        templates[2] = ("Move", "From a safe place well back from the edge, stretch your hands gently or roll your shoulders.", "A tiny movement can make a balcony break feel restorative.")
        templates[6] = ("Photo", "Photograph a color, shadow, or pattern visible from your terrace or balcony.", "Framing a familiar view helps you see it in a new way.")
    if family:
        templates[2] = ("Move", "With your adult, do five gentle toe taps or arm reaches in a clear safe spot.", "A little movement makes the hunt playful for everyone.")
    if difficulty == "Medium":
        templates[0] = ("Look", "Find two safe public-view details with the same shape but different sizes.", "Spotting a pair makes the search feel like a mini challenge.")
        templates[7] = ("Listen", "Notice two different sounds, then decide which one seems farther away.", "Comparing sounds turns careful listening into a guessing game.")
    if season.lower() == "monsoon":
        templates[5] = ("Look", "From a dry, safe spot, notice a reflection or a darker patch after rain; avoid puddles and water edges.", "Rain can redraw familiar colors and shapes.")
    elif season.lower() == "winter":
        templates[5] = ("Look", "Notice a place where the sunlight feels brighter, without stepping into a risky or restricted area.", "Low winter light can make ordinary corners glow.")
    elif season.lower() in {"summer", "spring"}:
        templates[5] = ("Look", "Notice a breeze by watching a loose, non-living object or your clothing; stay in the shade if hot.", "A small movement can help you spot the air itself.")
    if mobility_limited:
        templates[2] = ("Move", "From a comfortable, stable position, gently stretch your fingers or roll your shoulders.", "A small movement keeps the quest adaptable to you.")
    if family:
        templates[4] = ("Look", "Find a color you and your grown-up both like, without touching anything unfamiliar.", "Sharing a favorite color makes the search a team effort.")
    # Keep notes in mind without forwarding sensitive details beyond localhost.
    title = theme or f"{season} {place.split()[0]} Quest"
    return Quest(title=title[:90], estimated_time=minutes, tasks=[QuestTask(instruction=i, category=c, fun_hint=h) for c,i,h in templates])


def check_photo(data: bytes, task: str | None = None, model: str = DEFAULT_MODEL) -> PhotoCheck:
    prompt = photo_prompt(task)
    last = _chat([{"role": "user", "content": prompt, "images": [data]}], model, "json")
    try:
        return PhotoCheck.model_validate_json(last)
    except (ValidationError, ValueError) as exc:
        raise LocalModelError("The vision model returned an unreadable response. Try a vision-capable model and retry.") from exc


def write_journal(quest_title: str, completed: list[str], note: str, descriptions: list[str], model: str = DEFAULT_MODEL) -> str:
    result = _chat([{"role": "user", "content": journal_prompt(quest_title, completed, note, descriptions)}], model)
    return result.strip()
