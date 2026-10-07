"""Photo check, task reflection and local trail journal."""
import json
import streamlit as st
from pathlib import Path
from grassquest import db
from grassquest.images import prepare_image, save_photo
from grassquest.llm import DEFAULT_MODEL, LocalModelError, check_photo, write_journal
from grassquest.schemas import Quest
from grassquest.ui import local_error, setup

setup(); db.init_db(); st.title("After the walk")
quests = db.list_quests()
if not quests:
    st.info("Save a quest first, then come back here after your walk.")
else:
    row = st.selectbox("Choose a quest", quests, format_func=lambda q: f"{q['title']} · {q['status']}")
    quest = Quest.model_validate({"title":row["title"],"estimated_time":row["minutes"],"tasks":json.loads(row["tasks_json"])})
    current = set(json.loads(row["completed_json"]))
    st.subheader("What did you do?")
    completed=[]
    for i,t in enumerate(quest.tasks):
        if st.checkbox(f"{t.instruction}", value=i in current, key=f"after-{row['id']}-{i}"): completed.append(i)
    note=st.text_area("How did it feel? (optional)")
    uploads=st.file_uploader("Add up to 6 photos (JPG, PNG or WEBP)", type=["jpg","jpeg","png","webp"], accept_multiple_files=True)
    if uploads and len(uploads)>6: st.warning("Choose up to six photos.")
    photo_records=st.session_state.setdefault(f"photo_records_{row['id']}",[])
    descriptions=[record["description"] for record in photo_records if record.get("description")]
    for index, upload in enumerate((uploads or [])[:6]):
        try:
            safe_preview,_=prepare_image(upload.getvalue())
            st.image(safe_preview, caption=upload.name, width=280)
        except ValueError as exc:
            st.warning(f"{upload.name}: {exc}")
            continue
        task_names=["No task attached"]+[f"{i+1}. {task.instruction}" for i,task in enumerate(quest.tasks)]
        selected=st.selectbox("Attach to task (optional)", task_names, key=f"photo-task-{index}")
        if st.button(f"Check photo {index+1}", key=f"photo-check-{index}"):
            try:
                content, _=prepare_image(upload.getvalue())
                task_text=None if selected==task_names[0] else quest.tasks[task_names.index(selected)-1].instruction
                with st.spinner("Checking locally with the vision model…"):
                    result=check_photo(content, task_text, st.session_state.get("model",DEFAULT_MODEL))
                st.info(f"**AI guess, may be wrong** · {result.match} match · {result.confidence} confidence\n\n{result.description}")
                folder=Path("data/photos")
                saved=save_photo(upload.getvalue(),folder,f"quest-{row['id']}-{index}-{upload.name[:30]}")
                record={"path":str(saved),"task":task_text,"description":result.description,"match":result.match,"confidence":result.confidence}
                photo_records=[r for r in photo_records if r.get("path")!=str(saved)]+[record]
                st.session_state[f"photo_records_{row['id']}"]=photo_records
            except (ValueError, LocalModelError) as exc: local_error(exc)
    db.update_completed(row["id"],completed)
    if st.button("Write trail journal", type="primary"):
        try:
            completed_names=[quest.tasks[i].instruction for i in completed]
            with st.spinner("Writing your journal locally…"):
                body=write_journal(quest.title,completed_names,note,descriptions,st.session_state.get("model",DEFAULT_MODEL))
            st.session_state["journal_draft"]={"quest_id":row["id"],"body":body,"note":note,"photos":photo_records}
        except LocalModelError as exc: local_error(exc)
    draft=st.session_state.get("journal_draft")
    if draft and draft["quest_id"]==row["id"]:
        edited=st.text_area("Edit your journal",draft["body"],height=220)
        if st.button("Save journal"):
            db.save_journal(row["id"],edited,draft["note"],draft["photos"]); db.mark_done(row["id"]); st.success("Journal saved on this device.")
st.divider(); st.subheader("Saved journal entries")
for journal in db.list_journals():
    with st.expander(f"{journal['quest_title']} · {journal['created_at'][:10]}"):
        body=st.text_area("Journal entry",journal["body"],key=f"journal-{journal['id']}")
        if st.button("Save edits",key=f"journal-save-{journal['id']}"):
            db.update_journal(journal["id"],body); st.success("Saved.")
entries=db.list_journals()
if entries:
    markdown="\n\n---\n\n".join(f"# {e['quest_title']}\n\n{e['body']}" for e in entries)
    st.download_button("Export all journals to Markdown",markdown,"grassquest-journals.md",mime="text/markdown")
