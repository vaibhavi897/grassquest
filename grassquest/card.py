"""Offline printable card renderers."""
from __future__ import annotations

import html
from .schemas import Quest

SAFETY_FOOTER = "Stay on paths. Don't taste or pick unknown plants. Don't approach wildlife."


def markdown_card(quest: Quest, season: str = "") -> str:
    rows = [f"# {quest.title}", f"**Time:** {quest.estimated_time} minutes" + (f" · {season}" if season else ""), ""]
    rows.extend(f"- [ ] **{task.category}:** {task.instruction}  \n  _{task.fun_hint}_" for task in quest.tasks)
    rows.extend(["", "Notes: ____________________________________________________", "", SAFETY_FOOTER])
    return "\n".join(rows)


def html_card(quest: Quest, season: str = "") -> str:
    tasks = "".join(f'<li><span class="box"></span><div><b>{html.escape(task.category)}</b> · {html.escape(task.instruction)}<small>{html.escape(task.fun_hint)}</small></div></li>' for task in quest.tasks)
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{html.escape(quest.title)}</title><style>
@page{{size:A5 portrait;margin:12mm}}*{{box-sizing:border-box}}body{{font:15px/1.4 system-ui,Arial,sans-serif;color:#20322a;max-width:700px;margin:24px auto;padding:0 16px}}h1{{font-size:27px;margin-bottom:4px}}.meta{{color:#52665a;margin:0 0 14px}}ol{{list-style:none;padding:0;display:grid;gap:9px}}li{{display:flex;gap:10px;align-items:flex-start;border:1px solid #cad7ce;border-radius:9px;padding:9px}}.box{{width:22px;height:22px;border:2px solid #385e45;border-radius:4px;flex:none}}small{{display:block;color:#5a7062;margin-top:2px}}.notes{{margin:14px 0 8px}}.safety{{border-top:1px solid #aab8ae;padding-top:9px;font-size:12px}}@media print{{body{{margin:0;max-width:none}}}}
</style><body><h1>{html.escape(quest.title)}</h1><p class="meta">{quest.estimated_time} minutes{f' · {html.escape(season)}' if season else ''}</p><ol>{tasks}</ol><p class="notes">Notes: ___________________________________________<br><br>__________________________________________________</p><footer class="safety">{SAFETY_FOOTER}</footer></body></html>'''
