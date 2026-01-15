# Gravity Edits: Project Presentation Content
**Instructions:** Create a Google Slides presentation using the content below. Stick to a clean, modern dark theme.

---

### Slide 1: Title Slide
**Title:** Gravity Edits
**Subtitle:** Autonomous AI-Powered Video Editing Agent
**Footer:** Sai Eshwar Rampelli | January 2026

---

### Slide 2: The Problem
**Title:** The Editing Bottleneck
**Bullet Points:**
*   **Time Intensive:** "A-roll" editing (removing unplanned silence, mistakes) consumes 80% of a creator's time.
*   **Technical Barrier:** Color grading, audio mixing, and aspect ratio adaptation require professional software expertise.
*   **Engagement Demands:** Modern content needs dynamic captions ("Viral Overlays") and fast pacing to retain attention.
*   **Goal:** Automate the tedious mechanical parts of editing so creators can focus on storytelling.

---

### Slide 3: The Solution: Gravity Edits
**Title:** What is Gravity Edits?
**Bullet Points:**
*   **An AI Agent as a "Pair Programmer":** A collaborative video editing system.
*   **Inputs:** Raw Video + User Intent (e.g., "Make it fast-paced").
*   **Process:** Transcribes, Watches, Thinks, and Edits.
*   **Outputs:** A fully edited timeline, color-graded and captioned, ready for export or further manual tweaking.

---

### Slide 4: System Architecture
**Title:** High-Level Design
**Visual:** (Create a block diagram with these components)
*   **Frontend (React):** Timeline UI for human verification.
*   **Backend (FastAPI):** API Gateway & Orchestrator.
*   **Worker (Redis Queue):** Handles long-running renders.
*   **AI Engine:** Integrates Whisper (Audio), OpenCV (Vision), and Gemini (Logic).

---

### Slide 5: The "Brain" (AI Pipeline)
**Title:** Intelligent Processing
**Bullet Points:**
*   **1. Transcription:** `Faster-Whisper` creates a text map of the video.
*   **2. Vision:** `OpenCV` + `DeepFace` analyze brightness, contrast, and emotion per second.
*   **3. The "Wakullah Protocol":** Our custom RAG-based Prompt Engineering technique.
    *   *Input:* Text + Visual Stats.
    *   *Output:* XML Edit Decision List (Cuts, Corrections, Viral Moments).

---

### Slide 6: The "Hands" (Rendering Engine)
**Title:** Programmatic Video Generation
**Bullet Points:**
*   **No FFMPEG Scripting:** Uses Python's `MoviePy` for object-oriented video manipulation.
*   **Capabilities:**
    *   **Smart Scissors:** Cuts milliseconds based on timestamp data.
    *   **Color Matrix:** Applies brightness/contrast corrections via NumPy arrays.
    *   **Dynamic Overlays:** Generates text layers for "Punchlines" identified by the LLM.

---

### Slide 7: User Interface
**Title:** Human-in-the-Loop Workflow
**Visual:** (Take a screenshot of your active Frontend Timeline)
**Bullet Points:**
*   **Transparent Decision Making:** The UI shows *why* a clip was kept or cut.
*   **Full Control:** Users can undo AI actions, drag clips, or adjust overlay text.
*   **Real-time Preview:** Browser-based player syncs with backend state.

---

### Slide 8: Key Features
**Title:** Feature Highlights
**Bullet Points:**
*   **Automated "Rough Cut":** Removes 30-50% of raw footage (silence/bad takes).
*   **Smart Reframing:** Converts Landscape (16:9) to Shorts (9:16) automatically.
*   **Context-Aware Overlays:** "pop" and "typewriter" animations added only at high-impact moments.
*   **Visual Repair:** Automatically fixed under-exposed (dark) footage.
*   **Auto-Subtitles:** Generates `.srt` files for instant accessibility/SEO.

---

### Slide 9: Results & Impact
**Title:** Performance Analysis
**Bullet Points:**
*   **Efficiency:** Reduced editing time for a 5-minute vlog from 2 hours to ~15 minutes.
*   **Accuracy:** "Ghostbuster" filter successfully removed 95% of phantom words and hallucinations.
*   **Quality:** Rendered videos maintain sync and high resolution (1080p).
*   **Scalability:** Async Task Queue allows multiple edits to process simultaneously.

---

### Slide 10: Conclusion
**Title:** Future Scope
**Bullet Points:**
*   **Multi-Modal AI:** Moving to Video-Native LLMs (Gemini 1.5 Pro Vision) for deeper scene understanding.
*   **Audio Ducking:** AI-controlled background music mixing.
*   **Style Transfer:** Generative visual filters.
*   **Summary:** Gravity Edits proves that AI can be a powerful creative partner, not just a tool.

---
