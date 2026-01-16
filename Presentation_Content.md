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
**Title:** High-Level Technical Design
**Visual:** (Create a block diagram with these components)
*   **Frontend (React 19):** Single Page Application (SPA) managing state via React Hooks and communicating via RESTful APIs.
*   **Backend (FastAPI):** Asynchronous Python web server using `Uvicorn` and `Pydantic` for strict data validation.
*   **Decoupled Worker (Redis + RQ):** Background job processing system to offload blocking video rendering tasks from the main event loop.
*   **Data Layer:** Local file system storage for raw/processed assets, orchestrated via ephemeral JSON state files.

---

### Slide 5: The "Brain" (AI Pipeline)
**Title:** Multi-Modal Analysis Pipeline
**Bullet Points:**
*   **1. Transcription Engine:** integrated `Faster-Whisper` (CS2-based implementation) for quantized, highly accurate speech-to-text generation.
*   **2. Computer Vision Metrics:** 
    *   **Blur Detection:** Laplacian Variance method (`cv2.Laplacian`).
    *   **Exposure Analysis:** Histogram analysis in HSV color space.
    *   **Sentiment:** `DeepFace` (ResNet-50) for frame-by-frame emotion classification.
*   **3. The "Wakullah Protocol":** A context-optimization strategy where video state is serialized into a dense JSON payload, minimizing token usage while providing "visual context" (e.g., *avg_brightness: 45*) to the LLM.
*   **4. Inference:** Google Gemini 1.5 Pro processes this multi-modal prompt to generate a structured XML Edit Decision List (EDL).

---

### Slide 6: The "Hands" (Rendering Engine)
**Title:** Programmatic Video Synthesis
**Bullet Points:**
*   **Engine:** `MoviePy` (FFmpeg wrapper) for non-linear editing.
*   **Vectorized Processing:** Uses `NumPy` for high-performance pixel manipulations (Color Grading) to mitigate Python's Global Interpreter Lock (GIL).
*   **Compositing:** Uses `CompositeVideoClip` to stack video, audio, and transparent text layers (`TextClip`) into a single render pipeline.
*   **Optimization:** Smart caching of sub-clips and multi-threaded audio writing to reduce export times.

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
*   **Smart Reframing:** Converts Landscape (16:9) to Shorts (9:16) automatically using center-crop logic.
*   **Context-Aware Overlays:** "pop" and "typewriter" animations added only at high-impact moments.
*   **Visual Repair:** Automatically fixed under-exposed (dark) footage via Gamma correction.
*   **Auto-Subtitles:** Generates `.srt` files for instant accessibility/SEO.

---

### Slide 9: Results & Performance
**Title:** Performance Analysis
**Bullet Points:**
*   **Inference Efficiency:** Full video analysis + edit decision generation in < 45 seconds for 5-minute 1080p footage.
*   **Accuracy:** "Ghostbuster" sanitation layer reduced hallucination rate to < 2% by cross-referencing hard timestamps.
*   **System Latency:** Async architecture maintains < 200ms API response time even during heavy rendering load.
*   **Resource Management:** Redis Queue ensures non-blocking UI interactions, allowing parallel job submission.

---

### Slide 10: Conclusion
**Title:** Future Scope
**Bullet Points:**
*   **Multi-Modal AI:** transitioning to Video-Native LLMs (Gemini 1.5 Pro Vision) for native pixel understanding without intermediate CV metrics.
*   **Audio Ducking:** Implementation of envelope-based audio mixing for background music.
*   **Style Transfer:** GAN-based generative visual filters.
*   **Summary:** Gravity Edits demonstrates a scalable, agentic architecture for automating complex creative workflows.

---
