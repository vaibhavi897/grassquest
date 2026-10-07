"""Review saved quests, update checklists, mark done or delete."""
import json
import streamlit as st
from grassquest.db import delete_quest, get_quest, list_quests, mark_done, update_completed
from grassquest.schemas import Quest
from grassquest.ui import setup

setup(); st.title("My quests")
quests = list_quests()
if not quests:
    st.info("No saved quests yet. Make a quest and save it here.")
for row in quests:
    with st.expander(f"{row['title']} · {row['status']} · {row['minutes']} min · {row['created_at'][:10]}", expanded=False):
        quest = Quest.model_validate({"title":row["title"],"estimated_time":row["minutes"],"tasks":json.loads(row["tasks_json"])})
        checked = set(json.loads(row["completed_json"]))
        updated = []
        for i, task in enumerate(quest.tasks):
            if st.checkbox(f"{task.category}: {task.instruction}", value=i in checked, key=f"quest-{row['id']}-{i}"):
                updated.append(i)
        update_completed(row["id"], updated)
        st.caption(f"{row['season']} · {row['place']} · {row['group_name']}")
        a,b=st.columns(2)
        if a.button("Mark done", key=f"done-{row['id']}"):
            mark_done(row["id"]); st.rerun()
        if b.button("Delete quest", key=f"delete-{row['id']}"):
            delete_quest(row["id"]); st.rerun()
