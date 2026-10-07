"""Generate, preview and save an outdoor quest card."""
import streamlit as st
from grassquest.card import html_card, markdown_card
from grassquest.db import init_db, save_quest
from grassquest.llm import DEFAULT_MODEL, LocalModelError, generate_quest
from grassquest.ui import local_error, quest_card, setup

init_db(); setup()
st.title("Make a quest")
with st.form("quest_form"):
    season = st.selectbox("Season", ["Summer", "Monsoon", "Post-monsoon", "Winter", "Spring", "Autumn"])
    place = st.selectbox("Place type", ["Neighbourhood streets", "Park or garden", "Beach or seaside", "Hill or trail", "Campus", "Terrace or balcony"])
    group = st.selectbox("Who's going?", ["Solo", "Friends", "Family with kids"])
    minutes = st.selectbox("Time available", [15, 30, 60, 90], format_func=lambda n: f"{n} minutes")
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium"])
    note = st.text_input("Anything to adapt for? (optional)", placeholder="For example: I use a wheelchair")
    submitted = st.form_submit_button("Generate quest", type="primary")
if submitted:
    with st.spinner("Making a safe, place-aware quest with your local model…"):
        try:
            quest = generate_quest(season=season, place=place, group=group, minutes=minutes, difficulty=difficulty, note=note, model=st.session_state.get("model", DEFAULT_MODEL))
            st.session_state["current_quest"] = quest.model_dump()
            st.session_state["current_meta"] = {"season":season,"place":place,"group":group,"minutes":minutes,"difficulty":difficulty}
        except LocalModelError as exc:
            local_error(exc)
quest_data = st.session_state.get("current_quest")
meta = st.session_state.get("current_meta", {})
if quest_data:
    from grassquest.schemas import Quest
    quest = Quest.model_validate(quest_data)
    st.divider(); quest_card(quest, meta.get("season", season))
    col1, col2, col3 = st.columns(3)
    col1.download_button("Printable HTML", html_card(quest, meta.get("season", "")), file_name="grassquest-card.html", mime="text/html", use_container_width=True)
    col2.download_button("Markdown", markdown_card(quest, meta.get("season", "")), file_name="grassquest-card.md", mime="text/markdown", use_container_width=True)
    if col3.button("Regenerate", use_container_width=True):
        try:
            quest = generate_quest(season=meta["season"], place=meta["place"], group=meta["group"], minutes=meta["minutes"], difficulty=meta["difficulty"], note=note, model=st.session_state.get("model", DEFAULT_MODEL))
            st.session_state["current_quest"] = quest.model_dump(); st.rerun()
        except LocalModelError as exc: local_error(exc)
    if st.button("Save quest", type="primary"):
        try:
            save_quest({**meta, "title":quest.title,"tasks":[t.model_dump() for t in quest.tasks]})
            st.success("Saved to My Quests.")
        except Exception as exc: st.error(f"Couldn't save this quest: {exc}")
