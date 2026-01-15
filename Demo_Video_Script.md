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

"Under the hood, Gravity Edits uses a hybrid AI pipeline:
1.  **Faster-Whisper** handles Speech-to-Text for precise timestamping.
2.  **OpenCV & DeepFace** analyze visual metrics like brightness and emotion.
3.  And **Gemini 2.5 Pro** acts as the high-level reasoning engine, making the final editorial decisions based on the data."

---

### **1:15 - Live Demo: Ingestion & Analysis**

**[ACTION: Switch to the Browser (Gravity Edits Landing Page). Click 'Upload Video' and select a raw file (e.g., a 1-minute vlog with some mistakes/silence).]**

"Let's see it in action. I'm uploading a raw vlog file here.

**[ACTION: While the progress bar moves / 'Analyzing' spinner is shown]**

What's happening right now is complex. The backend is splitting the video. It's transcribing the audio to find words. But simultaneously, the computer vision module is scanning every frame to check if it's too dark or if the subject is happy or neutral.

It then packages all this data into a JSON prompt and sends it to the LLM with the 'Wakullah Protocol'—my custom prompt engineering technique that teaches the AI how to edit."

---

### **2:00 - The AI Editor Workbench**

**[ACTION: When the Project loads and the Timeline appears]**

"And here is the result. This is the **Gravity Edits Workbench**.

Unlike a 'black box' generator, this interface lets me see exactly what the AI did.

**[ACTION: Mouse over a RED (rejected) clip on the timeline]**

Notice these red blocks? The AI automatically identified these as 'Bad Takes' or 'Silence'. If I hover over this one... see the reason? It says **'Redundant / Non-verbal'**. The AI decided to cut this to keep the video fast-paced.

**[ACTION: Mouse over a GREEN (kept) clip]**

Now look at the kept clips. The AI didn't just keep them; it *enhanced* them.

**[ACTION: Click on a clip that has a 'Text Overlay' (viral caption) above it]**

See this text layer? The LLM identified this moment as a 'Punchline' or 'High Value Moment' and automatically generated a viral-style caption for it. I didn't type this—the AI did.

**[ACTION: Click on the 'Color Board' or show metadata side panel]**

It also applied Color Grading. It detected that the original footage was slightly 'Flat', so it applied a **Saturation Boost** and **Contrast Correction** automatically."

---

### **2:45 - The "Collaborative" AI (Chat & Human-in-the-Loop)**

**[ACTION: Open the "AI Chat" sidebar or Window in the editor]**

"But here's the best part: The AI is a collaborator, not a dictator. We know AI isn't right 100% of the time, so I built a **Human-in-the-Loop** workflow.

I can talk to the agent directly. Watch this.

**[ACTION: Type into the chat box: "It feels too slow. Make it punchier and remove the long pause at 0:40"]**

The Agent processes this natural language request and updates the edit decision list in real-time.

**[ACTION: Manually drag the edge of a clip to extend it, or use the 'Razor' tool to split a clip]**

And if I want fine-grained control, I can manually intervene. I can use the Razor tool to split this clip here, or drag the timeline to bring back a section the AI removed. The system respects my manual overrides as the final truth, ensuring the perfect blend of automation and human creativity."

---

### **3:30 - Feature: Shorts Reframing**

**[ACTION: Mention or Show Shorts toggle if available, otherwise skip to Export]**

"One of the coolest features is the **Shorts Adapter**. The system can programmatically crop this 16:9 landscape video into a 9:16 vertical video by centering the subject, making it ready for TikTok or Reels instantly."

---

### **4:00 - Rendering & Output**

**[ACTION: Click the 'Export Video' button in the top right]**

"Finally, when I'm happy with the AI's choices, I hit Export.

**[ACTION: Wait for the download or switch to a pre-rendered 'Final Output' video file]**

Instead of me spending 2 hours cutting this, the custom Python rendering engine stitches it all together in minutes. It even gives me the **.srt subtitle file** automatically so I can upload it straight to YouTube.

**[ACTION: Play 5-10 seconds of the FINAL Video full screen with sound]**

As you can see, the jump cuts are smooth, the captions are timed perfectly, and the bad takes are gone."

---

### **4:30 - Conclusion**

**[ACTION: Back to Camera or Title Slide]**

"Gravity Edits proves that we can move beyond simple tools to true **Agentic Workflows**. By combining deterministic Computer Vision with the semantic reasoning of Large Language Models, we've created an editor that doesn't just process pixels—it understands content.

Thank you."
