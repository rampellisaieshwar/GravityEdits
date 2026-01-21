
import json

path = '/Users/saieshwarrampelli/Downloads/GravityEdits/Submission.ipynb'

with open(path, 'r') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'markdown':
        source_text = "".join(cell['source'])
        if "## 3. Model/System Design" in source_text:
            cell['source'] = [
                "## 3. Model/System Design\n",
                "\n",
                "**Architecture:**\n",
                "*   **Frontend:** React-based timeline editor using a **Normalized Coordinate System (0-1)** for perfect cross-device scaling.\n",
                "*   **Backend:** FastAPI server managing state, uploads, and orchestration.\n",
                "*   **AI Engine:** The 'Two-Stage Brain' (Inspector + Director) that separates forensic analysis from creative editing.\n",
                "*   **Renderer:** A **Hybrid Engine** (MoviePy + FFmpeg) that uses Python for asset generation and FFmpeg for crashing-proof compositing.\n",
                "\n",
                "**ML/LLM Technique:**\n",
                "*   **Dual-Agent Workflow:** We employ an 'Inspector' agent to detect hallucinations and a 'Director' agent to make creative decisions.\n",
                "*   **Wakullah Protocol V2:** A strict 6-step prompt protocol ensuring Zero-Tolerance for empty overlays and mandatory viral short generation.\n",
                "*   **RAG-like Context:** We construct a rich JSON representation of the video timeline (clips, text, visual stats, timestamps) and feed it to the Gemini 1.5 Pro model.\n"
            ]
            print("Updated 'Model/System Design' cell.")
        
        if "## 1. Problem Definition" in source_text:
            # Maybe update objective if needed, but it looks fine.
            pass

with open(path, 'w') as f:
    json.dump(nb, f, indent=1)

print("Submission.ipynb updated successfully.")
