# Gravity Edits: Demonstration Video Script

**Instructions:**
*   **Text in BOLD** is what you `[DO]` (Actions).
*   **Text in Normal font** is what you `"SAY"` (Voiceover).
*   **Text in Italics** is context/tips.

---

### **0:00 - Introduction & Problem Statement**

**[ACTION: Start with your webcam or face looking at camera, or a slide of the Title]**

"Hi, I'm [Your Name], and this is **Gravity Edits**, an autonomous video editing agent built for my AI Minor project.

We all know the problem: capturing video is easy, but *editing* it is painful. Creators spend hours sifting through raw footage—removing silences, bad takes, and fixing lighting—just to get a few minutes of usable content.

My goal was to solve this not with simple filters, but with a multi-modal AI agent that 'watches' and 'listens' to the video just like a human editor would."

---

### **0:45 - The Architecture (How it Works)**

**[ACTION: Switch screen recording to a diagram or the VS Code editor showing `ai_engine.py`]**

"Under the hood, Gravity Edits uses a hybrid AI pipeline built on a fast, asynchronous stack:
1.  **FastAPI & Uvicorn** handle the backend orchestration purely asynchronously.
2.  **Faster-Whisper** handles quantized Speech-to-Text for precise timestamping.
3.  **OpenCV & DeepFace** analyze visual metrics like **Laplacian Variance** for blur and HSV histograms for exposure.
4.  And **Gemini 2.5 Pro** acts as the reasoning engine, processing our dense JSON state via the 'Wakullah Protocol'."

---

### **1:15 - Live Demo: Ingestion & Analysis**

**[ACTION: Switch to the Browser (Gravity Edits Landing Page). Click 'Upload Video' and select a raw file (e.g., a 1-minute vlog with some mistakes/silence).]**

"Let's see it in action. I'm uploading a raw vlog file here.

**[ACTION: While the progress bar moves / 'Analyzing' spinner is shown]**

What's happening right now is heavy processing offloaded to a **Redis Task Queue**. The backend splits the video and effectively 'maps' it. It's transcribing audio, but simultaneously, the CV module is vectorizing frame data to detect sentiment and lighting quality.

It packages this into a context-optimized payload and sends it to Gemini. This isn't just a simple prompt; it's a structured request enforcing a strict **XML Schema** for the output."

---

### **2:00 - The AI Editor Workbench**

**[ACTION: When the Project loads and the Timeline appears]**

"And here is the result. This is the **Gravity Edits Workbench**, a React 19 SPA.

Unlike a 'black box' generator, this interface visualizes the AI's decision tree.

**[ACTION: Mouse over a RED (rejected) clip on the timeline]**

Notice these red blocks? The AI identified these as 'Bad Takes'. My 'Ghostbuster' algorithm cross-referenced the transcript with silence thresholds to ensure these cuts are frame-perfect.

**[ACTION: Mouse over a GREEN (kept) clip]**

Now look at the kept clips. The AI didn't just keep them; it *enhanced* them using specific technical directives.

**[ACTION: Click on a clip that has a 'Text Overlay' (viral caption) above it]**

See this text layer? The LLM tagged this timestamp as a 'Punchline'. The frontend renders this using **Framer Motion**, but the backend will bake it in later using ImageMagick.

**[ACTION: Click on the 'Color Board' or show metadata side panel]**

It also applied Color Grading. It detected the footage was 'Flat' and applied a **NumPy-based Gamma Correction** matrix to boost dynamic range."

---

### **2:45 - The "Collaborative" AI (Chat & Human-in-the-Loop)**

**[ACTION: Open the "AI Chat" sidebar or Window in the editor]**

"But here's the best part: The AI is a collaborator. We know probabilistic models can hallucinate, so I built a **Human-in-the-Loop** workflow enforced by strict Pydantic models.

I can talk to the agent directly. Watch this.

**[ACTION: Type into the chat box: "It feels too slow. Make it punchier and remove the long pause at 0:40"]**

The Agent processes this natural language request and mutates the internal Redux-like state graph in real-time.

**[ACTION: Manually drag the edge of a clip to extend it, or use the 'Razor' tool to split a clip]**

And if I want fine-grained control, I can manually intervene. The system uses a 'Last-Write-Wins' strategy where my manual edits override the AI's suggestions, ensuring the output is always deterministic."

---

### **3:30 - Feature: Shorts Reframing**

**[ACTION: Mention or Show Shorts toggle if available, otherwise skip to Export]**

"One of the coolest features is the **Shorts Adapter**. The system programmatically calculates the 'Center of Action' and crops this 16:9 1080p video into a 9:16 vertical format, handling the aspect ratio conversion automatically."

---

### **4:00 - Rendering & Output**

**[ACTION: Click the 'Export Video' button in the top right]**

"Finally, when I'm happy with the AI's choices, I hit Export.

**[ACTION: Wait for the download or switch to a pre-rendered 'Final Output' video file]**

Instead of me spending 2 hours cutting this, the custom Python rendering engine uses **MoviePy** and **multiprocessing** to stitch it all together. It creates a composite video clip, rendering layers, audio mixing, and subtitles in parallel.

**[ACTION: Play 5-10 seconds of the FINAL Video full screen with sound]**

As you can see, the jump cuts are smooth, the captions are timed perfectly, and the bad takes are gone."

---

### **4:30 - Conclusion**

**[ACTION: Back to Camera or Title Slide]**

"Gravity Edits proves that we can move beyond simple tools to true **Agentic Workflows**. By combining deterministic Computer Vision metrics with the semantic reasoning of Large Language Models, we've created a system that is both technically robust and creatively powerful.

Thank you."
