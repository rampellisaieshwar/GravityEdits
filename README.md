# Gravity Edits - AI Video Editor 🎬

Gravity Edits is a modern, AI-powered video editing platform designed to streamline the content creation process. It leverages advanced Large Language Models (LLMs) to automatically analyze raw footage, identify viral-worthy moments, and construct a polished edit, all while giving users full creative control through a professional timeline interface.

## 🚀 Key Features

*   **🤖 Agentic AI Editor**: A fully autonomous AI (Gemini 1.5 Pro) that acts as a pair programmer for your video.
    *   **Natural Language Editing**: Command the AI to "Cut the part about bananas," "Add a Subscribe text at 5s," or "Fix the transcript."
    *   **Agentic Tools**: The AI can execute **Cut**, **Keep**, **Split**, **Add Text**, and **Edit Transcript** commands directly on the timeline.
    *   **Intelligent Resolution**: It understands context. "Make it red" means Reject. "Make it Green" means Keep. It finds clips by content automatically.
*   **👻 Ghostbuster Protocol ("Wakullah")**:
    *   **Hallucination Filter**: Automatically removes low-confidence "phantom words" (e.g., random "Thank you" or "Banana" in silence) from the transcript before the AI even sees it.
    *   **Skeptical Mode**: The AI is instructed to actively distrust the transcript if words seem contextually "stupid" or out of place, surgically removing them.
*   **✂️ Smart Timeline**: A non-linear editor (NLE) with magnetic snapping, multi-track audio, and precise drag-and-drop capabilities.
    *   **Draggable Background Music**: Customize the start time and duration of your soundtrack visually.
    *   **Advanced Audio Tools**: Split, trim, and re-arrange secondary audio clips effortlessly.
*   **📱 Viral Shorts Mode**: Instantly generates 9:16 vertical videos optimized for TikTok/Reels/Shorts, complete with smart cropping.
*   **🔑 BYOK Architecture**: **Bring Your Own Key** system. Your API keys (Gemini) are stored locally in your browser for maximum security and privacy. No backend storage of sensitive keys.
*   **🎨 Color & Effects**: Basic color grading (Temperature, Exposure, Contrast) and text overlays.
*   **⚡ Local Rendering**: High-performance rendering pipeline built on **MoviePy** and **OpenCV** to generate MP4s directly on your machine (or server).

## 🛠 Tech Stack

### Frontend
*   **React 19** & **TypeScript**: High-performance UI logic.
*   **Vite**: Blazing fast build tool.
*   **Tailwind CSS**: Modern, responsive styling.
*   **Framer Motion**: Smooth, professional animations and drag-and-drop interactions.
*   **Lucide React**: Beautiful, consistent iconography.

### Backend
*   **Python 3.10+**: Core logic.
*   **FastAPI**: High-performance async web framework.
*   **MoviePy**: Programmatic video editing and rendering.
*   **OpenCV**: Frame processing and analysis.
*   **Google Gemini (GenAI)**: The intelligence behind the scene detection.
*   **LangChain**: Orchestrating complex AI interactions.

## 📦 Installation & Setup

### Prerequisites
*   Node.js (v18+)
*   Python (v3.10+)
*   FFmpeg (Required for MoviePy)

### 1. Clone the Repository
```bash
git clone https://github.com/rampellisaieshwar/GravityEdits.git
cd GravityEdits
```

### 2. Backend Setup
Navigate to the root directory (where `backend/` is located) and set up the Python environment.

```bash
# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi "uvicorn[standard]" python-multipart opencv-python moviepy google-generativeai langchain langchain-google-genai proglog
```

> **Note**: Verify you have `ffmpeg` installed on your system path.

### 3. Frontend Setup
Navigate to the Frontend directory.

```bash
cd Frontend

# Install dependencies
npm install
```

## 🏃‍♂️ Running the Application

You need to run both the Backend (server) and Frontend (client) concurrently.

### Terminal 1: Backend
From the root directory:
```bash
uvicorn backend.main:app --reload
```
*The server will start at `http://127.0.0.1:8000`.*

### Terminal 2: Frontend
From the `Frontend` directory:
```bash
npm run dev
```
*The application will be accessible at `http://localhost:5173`.*

## 📝 Usage Guide

1.  **Welcome**: Open the app. If it's your first time, click the **Profile** icon (top right) to enter your **Gemini API Key** and set your Display Name.
2.  **Upload**: Click "Upload Video" to select a raw file.
3.  **Analyze**: The AI will process the video. Review the summary and suggested "Viral Shorts" clips.
4.  **Edit**:
    *   **Timeline**: Drag clips to reorder.
    *   **Trim**: Use the Razor tool (Scissors icon) to split video or audio tracks.
    *   **Music**: Drag the purple music bar to sync the beat with your video.
    *   **Overlays**: Add text overlays for captions or titles.
5.  **Export**: Click "Export Video" to render the final MP4. You can also "Download Project" to save the state.

## 🤝 Contributing
Contributions are welcome! Please fork the repository and submit a Pull Request.

## 📄 License
[MIT License](LICENSE)
