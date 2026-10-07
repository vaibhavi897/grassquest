"""Local model setup, demo data, and data deletion controls."""
from pathlib import Path
import streamlit as st
from grassquest.db import clear_all, init_db
from grassquest.llm import DEFAULT_MODEL, health
from grassquest.sample_data import load_sample_data
from grassquest.ui import setup

setup(); init_db(); st.title("Settings and privacy")
current=st.session_state.get("model",DEFAULT_MODEL)
model=st.text_input("Ollama model",current,help="Choose an installed vision-capable model for photo checking.")
if st.button("Save model choice"):
    st.session_state["model"]=model.strip() or DEFAULT_MODEL; st.success("Model choice saved for this session.")
status=health(model or DEFAULT_MODEL)
if status["connected"]:
    st.success("Ollama is running on this device.")
    if status["installed"]: st.success(f"{model} is installed.")
    else: st.warning(f"{model} is not installed. Run `ollama pull {model}`.")
else:
    st.warning("Ollama is not reachable. Start it with `ollama serve`.")
st.info("gemma3:4b is the recommended vision-capable model. gemma3:1b is a lower-RAM, text-only fallback; photo checking needs a vision-capable model.")
st.markdown("**100% local · Works offline after model download**\n\nQuests, journals, and photos stay in local SQLite/files. No GPS, location APIs, accounts, cloud APIs, or telemetry.")
if st.button("Load fictional sample data"):
    load_sample_data(); st.success("Added two fictional quests and one example journal (no photos).")
st.divider(); st.subheader("Delete local data")
if st.button("Delete all quests and journals", type="secondary"):
    clear_all()
    folder=Path("data/photos")
    if folder.exists():
        for file in folder.iterdir():
            if file.is_file(): file.unlink()
    st.success("Local quests, journals and photos deleted.")
