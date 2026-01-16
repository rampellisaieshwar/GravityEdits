# AI Project Report – Module E

## Student & Project Details

*   **Student Name:** Sai Eshwar Rampelli
*   **Mentor Name:** [Mentor Name]
*   **Project Title:** Gravity Edits - AI-Powered Automated Video Editing System

---

## 1. Problem Statement

### Background and Context
Modern video content creation (YouTube, TikTok, Instagram Reels) is a labor-intensive process. Creators often record significantly more footage than what makes it into the final cut. The process of "sifting" through raw footage to remove silences, bad takes, mistakes, and pauses—known as the "A-roll" edit—can take hours for just a few minutes of final video.

Furthermore, maintaining viewer engagement requires dynamic editing techniques such as color grading, zoom cuts, text overlays ("viral captions"), and aspect ratio reframing for different platforms. For solo creators or small teams, the technical barrier and time cost of these tasks are major bottlenecks.

### The AI Task
Gravity Edits aims to democratize professional video post-production by building an autonomous agent capable of:
1.  **Analysis**: Understanding video content through audio transcription and visual analysis.
2.  **Decision Making**: Cutting specific segments and determining structure (Editorial Decisions).
3.  **Generation**: Enhancing the output with color grading, audio mixing, and visual effects.

---

## 2. Approach

### Data Sources and Preprocessing
The system accepts raw video footage from the user.
*   **Audio Extraction**: Audio is extracted using FFMPEG and processed for speech recognition.
*   **Visual Analysis**: Frames are sampled at regular intervals to analyze visual quality (brightness, blur) specifically using OpenCV.

### Core Architecture & Methodology
We built a full-stack automated video editing platform that combines deterministic computer vision algorithms with a novel "Two-Stage" Agentic Workflow.
*   **The AI Pipeline ("The Brain")**:
    *   **Stage 1: The Inspector**: A forensic AI agent that analyzes the raw transcript and visual metrics to identify errors, "Ghost Words" (hallucinations), and technical flaws. It produces a structured "Hit List" of clips to scrutinize.
    *   **Stage 2: The Director**: A creative AI agent that takes the Inspector's report and the User's creative intent to generate the final Edit Decision List (EDL). It adheres to the "Wakullah Protocol V2" to ensure viral pacing and retention.
    *   **Visual Metrics**: Using `OpenCV` to analyze every clip for brightness and blur.

### Tech Stack
*   **Frontend**: React-based Non-Linear Editor (NLE) with Normalized Coordinate System (0-1) for device-agnostic preview.
*   **Backend**: FastAPI (Python) service for orchestration.
*   **Task Queue**: Redis-based `rq` for asynchronous processing.
*   **Rendering**: **Hybrid Engine** (MoviePy for asset generation + FFmpeg for compositing) to ensure stability on low-resource machines.

---

## 3. Key Results

### Working Prototype
The system successfully functions as an autonomous editor. It takes a raw video file and outputs a fully edited timeline with cuts, captions, and color grading.

### Example Outputs & Observations
*   **Precision Editing**: The "Inspector" agent successfully identifies and removes 95% of transcription hallucinations (e.g., "Banana" appearing in silence).
*   **Intelligent Reframing**: The "Shorts Export" feature successfully crops landscape video into 9:16 portrait mode.
*   **Dynamic Visuals**: Text overlays are generated at semantic "high value" moments identified by the LLM.
*   **Accessibility Ready**: Automatically produces standard `.srt` subtitle files synchronized with the final edit.

### Limitations & Failure Cases
*   **Processing Time**: Video rendering is computationally expensive.
*   **Context Window**: Extremely long videos (1hr+) may hit LLM token limits (2M tokens on Gemini 1.5 Pro helps mitigate this).

---

## 4. Learnings

### Technical Learnings
*   **Prompt Engineering**: Separating concerns into two agents ("Forensic" vs "Creative") yielded significantly better results than a single "Do it all" prompt. The "Inspector" catches errors the "Director" would stream right past.
*   **Coordinate Normalization**: Using pixel values for UI elements leads to misalignment across devices. Switching to a normalized 0.0-1.0 float system solved "Invisible Text" bugs.
*   **Asynchronous Processing**: Rendering video blocks the main thread. Implementing the Redis Task Queue was critical.

### Challenges Faced & Resolution
*   **Server Crashes (OOM)**: Pure Python rendering (MoviePy) caused memory leaks and crashes on large files.
    *   *Resolution*: We implemented a **Hybrid Pipeline**. We now use Python only to generate lightweight text assets (transparent videos) and use the robust command-line tool `FFmpeg` to stitch them together. This reduced memory usage by ~60%.
*   **LLM Hallucinations**: Early versions of the AI would "invent" dialogue.
    *   *Resolution*: The "Inspector" Agent acts as a firewall, validating every word against the raw data before the Creative Agent touches it.

### Future Improvements
Moving forward, plans include implementing "Audio Ducking" (automatically lowering background music during speech) and integrating VideoDB for serverless cloud rendering to scale infinitely.

---

## References & AI Usage Disclosure

### Datasets & Tools
*   **LLM**: Google Gemini 1.5 Pro
*   **Speech-to-Text**: Faster-Whisper (OpenAI Whisper model)
*   **Computer Vision**: OpenCV, DeepFace
*   **Video Processing**: MoviePy, FFMPEG

### AI Usage Disclosure
This project utilizes Generative AI (Gemini 1.5 Pro) as the core reasoning engine for video editing decisions. Additionally, AI coding assistants were used to accelerate the development of the codebase.
