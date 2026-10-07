"""Shared Streamlit presentation helpers."""
from __future__ import annotations
import streamlit as st
from .llm import DEFAULT_MODEL, health

def setup() -> None:
    st.set_page_config(page_title="GrassQuest", page_icon="🌿", layout="centered")
    st.sidebar.title("🌿 GrassQuest")
    st.sidebar.caption("100% local · Works offline")
    st.sidebar.markdown("Generate → Print → Go outside → Reflect")
    status = health(st.session_state.get("model", DEFAULT_MODEL))
    st.sidebar.caption("Ollama connected" if status["connected"] else "Ollama offline · quests need Ollama")

def local_error(exc: Exception) -> None:
    st.error(str(exc))

def quest_card(quest, season: str = "") -> None:
    st.markdown(f"## {quest.title}")
    st.caption(f"About {quest.estimated_time} minutes · {season}")
    for index, task in enumerate(quest.tasks, 1):
        st.markdown(f"**{index}. ☐ {task.category}** — {task.instruction}\n\n_{task.fun_hint}_")

