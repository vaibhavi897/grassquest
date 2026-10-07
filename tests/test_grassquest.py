from __future__ import annotations
import json
from io import BytesIO

import pytest
from PIL import Image
from pydantic import ValidationError

from grassquest import db
from grassquest.card import html_card, markdown_card
from grassquest.images import prepare_image
from grassquest.prompts import SAFETY, HONESTY, quest_prompt
from grassquest.schemas import Quest, QuestTask, parse_quest_text
from streamlit.testing.v1 import AppTest


def sample_quest(title="Small & Safe"):
    return Quest(title=title, estimated_time=30, tasks=[
        QuestTask(instruction=f"Notice a safe detail number {i}.",category=category,fun_hint="Enjoy the moment.")
        for i,category in enumerate(["Look","Listen","Move","Touch-safe","Look","Smell-safe","Photo","Listen"])
    ])


def test_quest_category_constraints():
    with pytest.raises(ValidationError):
        Quest(title="Invalid",estimated_time=30,tasks=[QuestTask(instruction="Observe a small detail",category="Photo",fun_hint="Notice") for _ in range(8)])


def test_tolerant_parser_produces_eight_tasks():
    parsed=parse_quest_text("A Garden Pause\n1. Notice a color in the distance\n2. Listen for a repeated sound",30)
    assert len(parsed.tasks)==8
    assert parsed.tasks[2].category=="Move"


def test_prompts_include_safety_accessibility_and_honesty():
    prompt=quest_prompt(season="Winter",place="Park",group="Family with kids",minutes=30,difficulty="Easy",note="wheelchair")
    assert "wheelchair" in prompt and "never ask anyone to taste" in prompt.lower()
    assert "do not invent species" in SAFETY.lower()
    assert "I can't tell" in HONESTY


def test_printable_card_is_self_contained_and_escaped():
    quest=sample_quest("A <Quest>")
    page=html_card(quest,"Spring")
    assert "A &lt;Quest&gt;" in page and "@page" in page and "https://" not in page
    assert "Stay on paths" in page and "[ ]" in markdown_card(quest)


def test_image_resizes_and_rejects_corrupt_data():
    out=BytesIO(); Image.new("RGB",(1800,900),(30,100,40)).save(out,"PNG")
    data,_=prepare_image(out.getvalue())
    with Image.open(BytesIO(data)) as image:
        assert image.size==(1024,512)
    with pytest.raises(ValueError): prepare_image(b"not an image")


def test_sqlite_quest_and_journal_crud(tmp_path):
    path=tmp_path/"test.db"
    qid=db.save_quest({"title":"Test","season":"Spring","place":"Park","group":"Solo","minutes":15,"difficulty":"Easy","tasks":[{"instruction":"Listen","category":"Listen","fun_hint":"Hear it"}]},path)
    assert db.get_quest(qid,path)["title"]=="Test"
    db.update_completed(qid,[0],path); db.mark_done(qid,path)
    assert json.loads(db.get_quest(qid,path)["completed_json"])==[0]
    jid=db.save_journal(qid,"A short test memory",path=path)
    db.update_journal(jid,"An edited memory",path)
    assert db.list_journals(path)[0]["body"]=="An edited memory"
    db.delete_quest(qid,path)
    assert db.list_quests(path)==[]


def test_mocked_ollama_structured_generation(monkeypatch):
    from grassquest import llm
    class Message: content="Small & Safe"
    class Response: message=Message()
    class Fake:
        def chat(self,**kwargs):
            assert kwargs["options"]["num_predict"] <= 100
            return Response()
    monkeypatch.setattr(llm,"_client",lambda:Fake())
    result=llm.generate_quest(season="Spring",place="Park",group="Solo",minutes=30,difficulty="Easy")
    assert result.title=="Small & Safe" and len(result.tasks)==8


def test_fast_builder_is_safe_place_aware_and_accessible():
    from grassquest.llm import build_quest
    q=build_quest("Monsoon","Terrace or balcony","Family with kids",15,"Easy","wheelchair user","Rainy Day Spotting")
    assert q.title=="Rainy Day Spotting" and len(q.tasks)==8
    assert "stable position" in q.tasks[2].instruction.lower()
    assert q.tasks[2].category=="Move"
    assert sum(t.category=="Photo" for t in q.tasks)<=2


def test_generation_falls_back_to_fast_builder_if_model_fails(monkeypatch):
    from grassquest import llm
    monkeypatch.setattr(llm,"_chat",lambda *a,**k: (_ for _ in ()).throw(llm.LocalModelError("slow")))
    q=llm.generate_quest(season="Spring",place="Park or garden",group="Solo",minutes=15,difficulty="Easy")
    assert q.title=="A Little Outside Quest" and len(q.tasks)==8


def test_grassquest_home_and_generator_pages_render(monkeypatch):
    from grassquest import ui
    monkeypatch.setattr(ui,"health",lambda model:{"connected":False,"installed":False,"models":[]})
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    app=AppTest.from_file(root/"grassquest_app.py",default_timeout=10).run()
    assert not app.exception
    page=app.switch_page("grassquest_pages/1_Quest_Generator.py").run()
    assert not page.exception
