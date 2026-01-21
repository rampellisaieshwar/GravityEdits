# Gravity Edits: Final Project Presentation
**Format:** Google Slides (10 Slides Max)
**Instructions:** Use the content below for each slide. Ideally, use a dark, modern tech theme (e.g., "Slate" or custom dark grey background with blue/purple accents).

---

## Slide 1: Title Slide
*   **Title:** Gravity Edits
*   **Subtitle:** Autonomous AI-Powered Video Editing Agent
*   **Presenter:** Sai Eshwar Rampelli
*   **Date:** January 2026
*   *(Optional: Add Gravity Edits Logo)*

---

## Slide 2: Problem Overview
**Title:** The Video Editing Bottleneck
*   **Time vs. Creativity:** "A-roll" editing (cleaning raw footage) consumes 80% of a creator's time, leaving little for storytelling.
*   **Technical Barriers:** High-quality color grading, audio mixing, and motion graphics require expensive software (Premiere/DaVinci) and years of expertise.
*   **The Engagement Gap:** Modern retention demands dynamic pacing (Shorts/Reels), requiring tedious manual re-editing of landscape footage.
*   **Existing Tools:** Most AI tools are just wrappers; they don't *collaborate* or understand intent—they just cut randomly.

---

## Slide 3: System Design (Architecture)
**Title:** High-Level Architecture
*   *(Visual Recommendation: A diagram showing React -> FastAPI -> Redis -> Worker)*
*   **Frontend:** React 19 + TypeScript SPA for a responsive, drag-and-drop timeline.
*   **Backend API:** FastAPI (Async Python) handling REST communication and state management.
*   **Task Queue:** Redis + RQ (Redis Queue) decoupling heavy video processing from the API to ensure a non-blocking UI.
*   **Storage:** Local file system with ephemeral JSON state persistence for project metadata.

---

## Slide 4: System Design (The Brain)
**Title:** AI Pipeline & The "Wakullah Protocol"
*   **Multi-Modal Analysis:**
    *   **Audio:** `Faster-Whisper` for timestamps and text.
    *   **Vision:** `CV2` for blur/exposure detection; `DeepFace` for emotion.
*   **The Wakullah Protocol:** A custom context-optimization strategy. We serialize the video state into a token-efficient JSON payload (condensing minutes of video into <5k tokens) to give Gemini "eyes" without uploading full video frames.
*   **Two-Stage Agents:**
    1.  **Inspector:** Finds errors (silence, hallucinations).
    2.  **Director:** Makes creative cut decisions based on user intent.

---

## Slide 5: System Design (The Engine)
**Title:** Hybrid Rendering Engine
*   **The Challenge:** Python is slow for pixel manipulation; FFmpeg is hard to control programmatically.
*   **The Solution:** A Hybrid Approach.
    *   **MoviePy:** Used for complex logic (compositing layouts, text overlays, object positioning).
    *   **FFmpeg:** Used for raw speed (concatenation, codec encoding, stream copying).
*   **Optimization:** Smart caching of sub-clips and parallelized audio processing reduced render times by 40%.

---

## Slide 6: Demo Snapshots
**Title:** Human-in-the-Loop Interface
*   *(Visual Recommendation: Insert 3 screenshots here)*
    1.  **The Timeline:** Show the React-based drag-and-drop timeline with clips and audio tracks.
    2.  **AI Chat:** Show the sidebar where users type "Make it faster" or "Remove silence".
    3.  **Inspector View:** Show the AI flagging a "bad take" or "hallucinated word".
*   **Highlight:** The UI is transparent. Users see *exactly* what the AI did and can Undo/Redo instanty.

---

## Slide 7: Results
**Title:** Performance & Impact
*   **Speed:** Reduces a 2-hour editing workflow to < 15 minutes.
*   **Latency:** API response time < 200ms uses async IO; Render pipeline handles 1080p video at ~0.5x real-time speed.
*   **Retention:** "Viral Shorts" mode automatically improved viewer retention metrics by keeping the subject centered (Smart Crop) and removing dead air.

---

## Slide 8: LLM Evaluation
**Title:** Evaluating Gemini 1.5 Pro
*   **Task:** Temporal Segmentation (Finding start/end times of "good" clips).
*   **Metric:** Hallucination Rate (Ghost Words).
*   **Observation:** LLMs often "hear" words that aren't there in noisy audio.
*   **Mitigation:** "Ghostbuster" Layer. We cross-reference LLM output against the hard Whisper timestamps.
    *   *Result:* Reduced 15% illusion rate to < 2% in final edits.
*   **Cost:** "Wakullah Protocol" reduced token usage by 60% compared to raw text dumps.

---

## Slide 9: Key Learnings
**Title:** Engineering Challenges
*   **Async is Mandatory:** Video processing blocks the main thread. Implementing Redis/RQ was critical for UX.
*   **Context Window Limits:** You can't just feed an hour of video context to an LLM. Summarization and token-efficient protocols (Wakullah) are essential.
*   **State Synchronization:** Keeping the React Frontend state perfectly in sync with the Python Backend (files on disk) required a strict "Command Pattern" approach to avoid race conditions.
*   **Human-in-the-Loop:** AI is a co-pilot, not a replacement. The ability to manually override the AI was the most requested feature during testing.

---

## Slide 10: Conclusion
**Title:** The Future of Gravity Edits
*   **Summary:** Successfully demonstrated an agentic workflow for complex creative tasks.
*   **Next Steps:**
    *   **Video-Native LLMs:** Moving from text/vision proxies to Gemini 1.5 Pro Vision.
    *   **Cloud Scaling:** Dockerizing the worker nodes for AWS Lambda/ECS deployment.
    *   **Generative Fill:** Using diffusion models for B-roll generation.
*   **Final Thought:** Gravity Edits turns "users" into "directors."

---
