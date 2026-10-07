"""Clearly fictional starter content for a fast local demo."""
from __future__ import annotations
import json
from pathlib import Path
from .db import connect, init_db, save_quest, save_journal, list_quests

def load_sample_data(path: Path | str | None = None) -> None:
    init_db(path)
    if list_quests(path):
        return
    tasks = [
      {"instruction":"Find a patch of light and shadow.","category":"Look","fun_hint":"Notice how the shapes shift."},
      {"instruction":"Listen for a sound that repeats.","category":"Listen","fun_hint":"A tiny rhythm might be hiding nearby."},
      {"instruction":"Stretch gently in a clear, safe spot.","category":"Move","fun_hint":"Give your shoulders a fresh start."},
      {"instruction":"Notice a pattern from the path without touching it.","category":"Look","fun_hint":"Nature rarely uses a ruler."},
      {"instruction":"Pause and hear the quietest sound you can.","category":"Listen","fun_hint":"Stillness turns up the volume."},
      {"instruction":"Notice a fresh outdoor scent without touching anything.","category":"Smell-safe","fun_hint":"The air changes from place to place."},
      {"instruction":"Photograph a color that feels like today.","category":"Photo","fun_hint":"Keep a little color for later."},
      {"instruction":"Walk at an easy pace for two minutes on the path.","category":"Move","fun_hint":"Let the scenery set the tempo."},
    ]
    first = save_quest({"title":"The Little Park Pause","season":"Spring","place":"Park or garden","group":"Solo","minutes":30,"difficulty":"Easy","tasks":tasks}, path)
    second = save_quest({"title":"Balcony Detail Hunt","season":"Spring","place":"Terrace or balcony","group":"Friends","minutes":15,"difficulty":"Easy","tasks":tasks}, path)
    with connect(path) as db:
        db.execute("UPDATE quests SET status='Done',completed_json=? WHERE id=?", (json.dumps(list(range(8))), first))
    save_journal(first, "I slowed down in the park and began noticing the small contrasts around me: light against shadow, a repeating sound, and a color worth remembering. A gentle stretch made the pause feel like a reset. I came back feeling more present than when I arrived.", "Fictional sample entry; replace with your own memories.", [], path)
