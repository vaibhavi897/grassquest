# DEV.to post notes — GrassQuest

- **What it is / who it is for:** a local-first outdoor scavenger quest maker and trail journal for people who spend the day working or studying at a screen.
- **How it gets people off-screen:** one short planning session before the walk; a printed card during the walk; optional reflection and photo check after returning. No in-walk phone feature.
- **Technical decisions:** Streamlit; Ollama with Gemma 3; Pydantic validation; SQLite; Pillow resizing to 1024 px; prompts and photos remain local. Gemma suggests a brief theme, while safe local task templates produce the full card quickly.
- **Real model test results:** Ollama listed `gemma3:4b` (3.3 GB installed). After shortening the model task to a brief theme and locally composing validated tasks, one real quest returned eight tasks in about 5 seconds. Four-way quality/safety evaluation and photo evaluation remain to be done; do not overstate these results.
- **Vision evaluation:** Not run: no personal photo was available (only package assets were found). Use personal photos with `python scripts/eval_vision.py <folder>`; report what the model got right and wrong.
- **Build problems and fixes:**
  - Full structured task generation was too slow on CPU; changed Gemma's role to suggesting a brief theme and assembled safe tasks locally, reducing one observed generation to about five seconds.
  - Streamlit's default page discovery collided with another app's pages in the development checkout; registered GrassQuest pages explicitly so this release runs independently.
- **What local open AI made possible:** private employer/personal photos and notes stay on-device; works offline once weights are installed; no API key, account, quota or per-call cost; prompts are editable.
- **Honest vision limitations:** a 4B model can misread the scene; labels are guesses, not species identification or proof that a task happened.
- **Gemma category justification:** Gemma is the core of quest and journal generation and provides local multimodal photo checking, enabling the privacy/offline constraint that makes this product viable.
- **My outdoor test story:** _Add your real walk, place type and what surprised you._
- **Walker quote:** _Add a real quote with permission._
