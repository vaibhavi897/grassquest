"""GrassQuest app entry point. Run with: streamlit run grassquest_app.py"""
import streamlit as st
from grassquest.db import init_db
from grassquest.ui import setup

def home() -> None:
    init_db()
    setup()
    st.title("A little quest to get you outside")
    st.write("Plan for a minute. Print your card. Put your phone away until you get back.")
    st.success("🌱 100% local. Your notes, photos and model stay on this device.")
    st.markdown("### Three small steps\n1. **Make a quest** for your season, place and group.\n2. **Print the card** and enjoy the walk without your phone.\n3. **Come back** to check in, add photos and save a trail journal.")

st.set_page_config(page_title="GrassQuest", page_icon="🌿", layout="centered")
navigation = st.navigation([
    st.Page(home, title="Home", icon="🏡", default=True),
    st.Page("grassquest_pages/1_Quest_Generator.py", title="Quest Generator", icon="🗺️"),
    st.Page("grassquest_pages/2_My_Quests.py", title="My Quests", icon="📋"),
    st.Page("grassquest_pages/3_After_the_Walk.py", title="After the Walk", icon="📔"),
    st.Page("grassquest_pages/4_Settings.py", title="Settings", icon="⚙️"),
])
navigation.run()
