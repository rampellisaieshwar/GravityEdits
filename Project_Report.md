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
We built a full-stack automated video editing platform that combines deterministic computer vision algorithms with probabilistic Large Language Models (LLMs).
*   **The AI Pipeline ("The Brain")**:
    *   **Ingestion & Transcription**: Utilizing `faster-whisper` to generate highly accurate, timestamped transcripts of the raw footage.
    *   **Visual Metrics**: Using `OpenCV` and `DeepFace` to analyze every clip for visual quality and emotional sentiment.
    *   **The "Wakullah Protocol"**: This is our custom prompt engineering framework for the LLM (Gemini 1.5 Pro). We feed the video's JSON representation (text + visual stats) to the LLM, which acts as a "Senior Editor" to return an Edit Decision List (XML).

### Tech Stack
*   **Frontend**: React-based Non-Linear Editor (NLE) for visualization and human-in-the-loop collaboration.
*   **Backend**: FastAPI (Python) service for orchestration.
*   **Task Queue**: Redis-based `rq` for asynchronous processing of heavy rendering jobs.
*   **Rendering**: `MoviePy` and `FFMPEG` for physical video manipulation.

---

## 3. Key Results

### Working Prototype
The system successfully functions as an autonomous editor. It takes a raw video file and outputs a fully edited timeline with cuts, captions, and color grading.

### Example Outputs & Observations
*   **Automated "Rough Cuts"**: The AI consistently identifies and removes silence and non-speech noise, reducing raw footage duration by 30-50% while maintaining narrative flow.
*   **Intelligent Reframing**: The "Shorts Export" feature successfully crops landscape video into 9:16 portrait mode.
*   **Dynamic Visuals**: Text overlays are generated at semantic "high value" moments identified by the LLM.
*   **Accessibility Ready**: Automatically produces standard `.srt` subtitle files synchronized with the final edit, ready for YouTube upload.

### Limitations & Failure Cases
*   **Processing Time**: Video rendering is computationally expensive and not yet real-time.
*   **Context Window**: Extremely long videos (1hr+) may hit LLM token limits, requiring chunking strategies.

---

## 4. Learnings

### Technical Learnings
*   **Prompt Engineering**: Context is King. Providing the LLM with *visual* metadata (e.g., "This shot is dark") significantly improved its ability to make "technical" decisions rather than just semantic ones.
*   **Asynchronous Processing**: Rendering video blocks the main thread. Implementing the Redis Task Queue was critical to allow users to continue using the interface.

### Challenges Faced & Resolution
*   **LLM Hallucinations**: Early versions of the AI would "invent" dialogue or misinterpret timestamps.
    *   *Resolution*: We implemented strict "Sanitization" steps (The "Ghostbuster" filter) that cross-reference LLM outputs with the original hard timestamps.
*   **Hybrid Workflow**: Users generally distrust "black box" automation.
    *   *Resolution*: Providing a UI where they could see *why* the AI made a cut (via the "reason" field in our XML) built trust.

### Future Improvements
Moving forward, plans include implementing "Audio Ducking" (automatically lowering background music during speech) and exploring Multimodal Video-to-Video models for even deeper visual understanding.

---

## References & AI Usage Disclosure

### Datasets & Tools
*   **LLM**: Google Gemini 1.5 Pro
*   **Speech-to-Text**: Faster-Whisper (OpenAI Whisper model)
*   **Computer Vision**: OpenCV, DeepFace
*   **Video Processing**: MoviePy, FFMPEG

### AI Usage Disclosure
This project utilizes Generative AI (Gemini 1.5 Pro) as the core reasoning engine for video editing decisions. Additionally, AI coding assistants were used to accelerate the development of the codebase.
