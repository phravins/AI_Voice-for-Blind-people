# AI Voice Tutor

An intelligent, voice-controlled educational assistant that reads, summarizes, and explains PDF documents. Built with React, Flask, and the Google Gemini API, it offers a hands-free learning experience.

## Features

*   **Hands-Free Voice Control**:
    *   **Wake Word**: Say "Wake" to activate the assistant ("Hi, how can I help?").
    *   **Continuous Conversation**: The tutor listens automatically after speaking, creating a natural dialogue loop.
    *   **Barge-In**: Say "Stop" or "Quiet" to interrupt audio playback immediately.
*   **PDF Analysis**:
    *   **Summarize**: Get a concise summary of the current page.
    *   **Explain**: Ask for deep explanations of specific sentences or concepts (e.g., "Explain line 5").
    *   **Translate**: Real-time translation of content into languages like Tamil, Hindi, Spanish, French, etc.
    *   **Quiz**: Generate interactive quizzes from the content to test your knowledge.
    *   **Navigation**: Go to next/previous pages via voice ("Next page", "Go to page 5").
*   **Visual Interface**:
    *   Glassmorphism UI design.
    *   Real-time transcription of your voice commands.
    *   Context-aware insights.

## Tech Stack

### Frontend
*   **React (Vite)**: Fast, modern UI framework.
*   **Web Speech API**: Native browser speech recognition for low-latency voice control.
*   **CSS3**: Custom glassmorphism styles and responsive layout.

### Backend
*   **Python (Flask)**: REST API server.
*   **Google Gemini 1.5 Flash**: LLM for summarization, explanation, and translation.
*   **PDF Processing**: `pdfplumber`, `PyPDF2` for text extraction.
*   **TTS (Text-to-Speech)**: `gTTS` (Google Text-to-Speech) for generating audio responses.
*   **Database**: SQLite/JSON (for session and logical document mapping).

## Prerequisites

*   **Node.js** (v16+)
*   **Python** (v3.10+)
*   **Google Gemini API Key**

## Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone <repository_url>
    cd ai_voice_tutor
    ```

2.  **Backend Setup**
    *   Navigate to the root directory.
    *   Create a virtual environment (optional but recommended):
        ```bash
        python -m venv venv
        # Windows:
        venv\Scripts\activate
        # Mac/Linux:
        source venv/bin/activate
        ```
    *   Install dependencies:
        ```bash
        pip install -r requirements.txt
        ```
    *   **Environment Variables**:
        Create a `.env` file in the root directory and add your API Key:
        ```env
        GEMINI_API_KEY=your_actual_api_key_here
        FLASK_SECRET_KEY=some_random_secret_string
        ```
    *   Start the Server:
        ```bash
        python web_app.py
        ```
        *Server runs on `http://127.0.0.1:5000`*

3.  **Frontend Setup**
    *   Open a new terminal.
    *   Navigate to the frontend folder:
        ```bash
        cd frontend
        ```
    *   Install dependencies:
        ```bash
        npm install
        ```
    *   Start the Application:
        ```bash
        npm run dev
        ```
    *   Open your browser to `http://localhost:5173`.

## Voice Commands Cheat Sheet

| Intent | Commands | Action |
| :--- | :--- | :--- |
| **Wake** | "Wake", "Wake up" | Activates the AI conversation loop. |
| **Summarize** | "Summarize", "Summary of this" | Summarizes the current page. |
| **Explain** | "Explain", "What does this mean" | Explains the content in simple terms. |
| **Specifics** | "Explain line 5", "Explain sentence 3" | Explains a specific part of the text. |
| **Translate** | "Translate to Hindi", "Speak in Spanish" | Translates the page content. |
| **Navigation** | "Next page", "Previous", "Go to page 2" | Navigates the document. |
| **Stop** | "Stop", "Quiet", "Exit" | Stops audio and deactivates listening loop. |
| **Quiz** | "Quiz me", "Ask me a question" | Generates a quiz question from the page. |

## Project Structure

```
ai_voice_tutor/
├── web_app.py              # Main Flask Backend Entry Point
├── config.py               # Configuration (Paths, Constants)
├── modules/                # Python Modules
│   ├── gemini_client.py    # AI Integration
│   ├── intent_recognizer.py# Regex-based Intent Logic
│   ├── pdf_parser.py       # PDF Text Extraction
│   └── ...
├── frontend/               # React Frontend
│   ├── index.html
│   ├── vite.config.js      # Proxy configuration
│   └── src/
│       ├── pages/          # Home.jsx, Tutor.jsx
│       ├── components/     # VoiceBar, ContextCard, etc.
│       ├── utils/          # api.js, voice.js (Speech Logic)
│       └── ...
└── uploads/                # Storage for uploaded PDFs
```
