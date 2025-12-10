# AI Voice Tutor Backend Walkthrough

I have updated the AI Voice Tutor backend to match your detailed system overview. The system now supports enhanced intent recognition, structured Gemini prompts, and a CLI-based workflow.

## Changes Implemented

### 1. Intent Recognition (`modules/intent_recognizer.py`)
- **New Intents**: Added `READ_PARAGRAPH` to read specific paragraphs.
- **Slot Extraction**:
    - Captures `difficulty` for quizzes (e.g., "hard quiz").
    - Captures `target_paragraph` for reading specific sections.
    - Captures `target_language` for translation.

### 2. Gemini Client (`modules/gemini_client.py`)
- **Structured Prompts**: Updated `_build_prompt` to use a clear structure:
    - **System Instructions**: Defines the persona (AI Voice Tutor for visually impaired).
    - **Role**: Changes based on intent (Teacher, Translator, Quiz Master).
    - **Context**: The text from the PDF.
    - **User Request**: The specific command.
- **Quiz Handling**: Requests structured JSON output for quizzes to enable better parsing (currently speaks the questions clearly).

### 3. Dialogue Manager (`modules/dialogue_manager.py`)
- **Logic Update**:
    - Handles `READ_PARAGRAPH` to read specific chunks of text.
    - Passes `difficulty` to the Gemini client.
    - Parses JSON quiz responses to speak them in a user-friendly format.
    - Fixed syntax errors and improved error handling.

### 4. Main Application (`main.py`)
- **CLI Support**: Removed `tkinter` GUI. The app now accepts the PDF path via command line argument or user input.
    - Usage: `python main.py "path/to/document.pdf"`

## How to Run

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: Ensure you have `ffmpeg` or `poppler` installed if needed for audio/PDF processing, though the python deps are covered.*

2.  **Set API Key**:
    Ensure your `.env` file has a valid `GEMINI_API_KEY`.

3.  **Run the App**:
    ```bash
    python main.py "path/to/your/file.pdf"
    ```
    Or simply run `python main.py` and paste the path when prompted.

4.  **Voice Commands**:
    - "Summarize this page"
    - "Give me a hard quiz"
    - "Read paragraph 2"
    - "Translate to Spanish"
    - "Next page"

## Verification Results
- **Static Analysis**: Code structure matches the design.
- **Manual Check**: Verified file contents and logic flow.
