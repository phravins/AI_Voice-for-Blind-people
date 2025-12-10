import logging
import os
import sys
import uuid
import json
from flask import Flask, request, session, jsonify, send_from_directory, make_response
from flask_cors import CORS
from gtts import gTTS
from modules.pdf_parser import extract_text_from_pdf
from modules.intent_recognizer import IntentRecognizer
from modules.gemini_client import GeminiClient
from modules.text_processor import get_text_chunk, combine_doc_text
from modules.doc_store import save as save_doc, load as load_doc
from config import LOGS_DIR, UPLOADS_DIR, TEMP_AUDIO_DIR, TTS_LANGUAGE
from modules.db import init_db, ensure_default_project, list_projects, create_project, get_project, list_project_pdfs, add_pdf, get_pdf, delete_pdf, create_chat, list_chats, add_message, list_messages

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "web_app.log")),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")
CORS(app, supports_credentials=True) # Enable CORS for frontend

ir = IntentRecognizer()
gc = GeminiClient()
init_db()
DEFAULT_PROJECT_ID = ensure_default_project()

# --- Helper Functions ---
def _generate_audio(text):
    """Generates TTS audio and returns the filename."""
    if not text:
        return None
    fname = f"resp_{uuid.uuid4().hex}.mp3"
    fpath = os.path.join(TEMP_AUDIO_DIR, fname)
    try:
        tts = gTTS(text=text, lang=TTS_LANGUAGE)
        tts.save(fpath)
        return fname
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        return None

# --- API Endpoints ---

@app.route("/api/upload", methods=["POST"])
def api_upload():
    """Upload PDF and return metadata."""
    file = request.files.get("pdf")
    if not file or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Invalid file format. Please upload a PDF."}), 400

    fname = f"{uuid.uuid4().hex}.pdf"
    
    # Sequential Naming Logic
    try:
        existing_files = [f for f in os.listdir(UPLOADS_DIR) if f.startswith("PDF_") and f.endswith(".pdf")]
        max_index = 0
        import re
        for f in existing_files:
            match = re.search(r"PDF_(\d+).pdf", f)
            if match:
                idx = int(match.group(1))
                if idx > max_index:
                    max_index = idx
        
        new_index = max_index + 1
        fname = f"PDF_{new_index}.pdf"
    except Exception as e:
        logger.error(f"Naming Error: {e}")
        # Fallback to UUID if something breaks
        fname = f"{uuid.uuid4().hex}.pdf"

    fpath = os.path.join(UPLOADS_DIR, fname)
    file.save(fpath)

    # Save to default project (for now, or pass project_id)
    project_id = request.form.get("project_id", DEFAULT_PROJECT_ID)
    add_pdf(project_id, file.filename, fpath) # Store original name

    doc_structure = extract_text_from_pdf(fpath)
    if not doc_structure:
        return jsonify({"error": "Failed to extract text from PDF."}), 500

    doc_id_name = fname.replace(".pdf", "") # Use PDF_1 as the doc_id
    doc_id = save_doc(doc_structure, custom_id=doc_id_name)
    
    # Store minimal state in session if needed, but client should track this too
    session["doc_id"] = doc_id
    
    # Generate initial welcome audio?
    msg = f"Loaded {file.filename}. {len(doc_structure)} pages."
    audio_file = _generate_audio(msg)

    return jsonify({
        "pdf_id": doc_id, # Using doc_store ID as reference for active session
        "filename": file.filename,
        "page_count": len(doc_structure),
        "message": msg,
        "audio_url": f"/audio/{audio_file}" if audio_file else None
    })

@app.route("/api/library", methods=["GET"])
def api_library():
    """List recently uploaded documents."""
    files = []
    try:
        if os.path.exists(UPLOADS_DIR):
            for f in os.listdir(UPLOADS_DIR):
                if f.endswith(".pdf"):
                    files.append({"filename": f, "id": f.replace(".pdf", "")}) 
        return jsonify({"documents": files})
    except Exception as e:
        logger.error(f"Library Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/library/<doc_id>", methods=["DELETE"])
def api_delete_document(doc_id):
    """Delete a document."""
    try:
        fname = f"{doc_id}.pdf"
        fpath = os.path.join(UPLOADS_DIR, fname)
        
        if os.path.exists(fpath):
            os.remove(fpath)
            return jsonify({"message": "Document deleted"}), 200
        else:
            return jsonify({"error": "File not found"}), 404
            
    except Exception as e:
        logger.error(f"Delete Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/tts", methods=["GET"])
def api_tts():
    """Get audio for generic text."""
    text = request.args.get("text", "")
    if not text:
        return jsonify({"error": "No text provided"}), 400
    fname = _generate_audio(text)
    if not fname:
        return jsonify({"error": "TTS failed"}), 500
    return jsonify({"audio_url": f"/audio/{fname}"})

@app.route("/audio/<fname>")
def audio(fname):
    return send_from_directory(TEMP_AUDIO_DIR, fname)

@app.route("/api/doc/<doc_id>/page/<int:page_num>", methods=["GET"])
def get_page_content(doc_id, page_num):
    """Get text content for a specific page."""
    doc = load_doc(doc_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404
    if page_num < 0 or page_num >= len(doc):
        return jsonify({"error": "Page out of range"}), 400
    
    # Combine chunks for the page (simplified)
    # The doc structure is list of pages, each page is list of chunks? 
    # Let's check pdf_parser.py extract_text_from_pdf output structure.
    # Assuming doc[page_num] is the text or a list of chunks.
    # Based on text_processor.py: doc_structure is a list of pages.
    
    # JSON keys are always strings
    page_key = str(page_num)
    if page_key not in doc:
         return jsonify({"error": "Page not found"}), 404
         
    page_content = doc[page_key]
    text = page_content if isinstance(page_content, str) else "\n".join(page_content)
    
    return jsonify({
        "page": page_num,
        "text": text,
        "total_pages": len(doc)
    })

@app.route("/api/assistant/action", methods=["POST"])
def assistant_action():
    """Handle voice commands and interactions."""
    data = request.json
    doc_id = data.get("doc_id")
    page = data.get("page", 0)
    user_utterance = data.get("user_utterance", "")

    if not doc_id:
        return jsonify({"error": "No document active"}), 400
    
    doc_structure = load_doc(doc_id)
    if not doc_structure:
        return jsonify({"error": "Document expired"}), 404

    # Recognition
    intent = "UNKNOWN"
    entities = {}
    if user_utterance:
        parsed = ir.recognize_intent(user_utterance)
        intent = parsed["intent"]
        entities = parsed["entities"]
    else:
        # Direct intent invocation (e.g. button click)
        intent = data.get("intent", "UNKNOWN")
        # Ensure entities are passed from request data for direct actions
        entities = {k: v for k, v in data.items() if k not in ["doc_id", "page", "user_utterance", "intent"]}
    
    response_text = ""
    response_type = "message"
    next_page = page
    payload = {}

    # Extract text content for the current page (available for any intent)
    current_text = ""
    if str(page) in doc_structure:
        chunk = doc_structure[str(page)]
        if isinstance(chunk, list):
            current_text = " ".join(chunk)
        else:
            current_text = chunk
    
    # --- Handlers ---
    if intent == "STOP":
        response_text = "Stopping."
    
    elif intent in ["NAVIGATE_NEXT", "NEXT_PAGE"]: # Add alias
        if page < len(doc_structure) - 1:
            next_page += 1
            response_text = f"Page {next_page + 1}."
            response_type = "navigation"
        else:
            response_text = "Last page."
            
    elif intent in ["NAVIGATE_PREV", "PREVIOUS_PAGE"]:
        if page > 0:
            next_page -= 1
            response_text = f"Page {next_page + 1}."
            response_type = "navigation"
        else:
            response_text = "First page."

    elif intent == "NAVIGATE_PAGE":
        target = entities.get("target_page")
        if target is not None and 0 <= target < len(doc_structure):
            next_page = target
            response_text = f"Page {next_page + 1}."
            response_type = "navigation"
        else:
            response_text = "Page not found."

    elif intent in ["SUMMARIZE", "EXPLAIN", "TRANSLATE", "QUIZ"]:
        # current_text is already extracted above


        # Guard Clause: Empty Text
        if not current_text or not current_text.strip():
            response_text = "I cannot read any text on this page. It might be scanned or empty."
            response_type = "error"
        
        elif intent == "SUMMARIZE":
            # Check if user wants FULL document summary
            wants_full_doc = False
            if user_utterance:
                u_lower = user_utterance.lower()
                if "pdf" in u_lower or "document" in u_lower or "book" in u_lower or "whole" in u_lower or "entire" in u_lower:
                    wants_full_doc = True
            
            if wants_full_doc:
                # Aggregate summary: Optimized for 2-second response
                # Limit to first 5 pages only for maximum speed
                full_text = ""
                max_pages = 5  # Ultra-fast: only 5 pages for 2-second target
                count = 0
                for p_num in sorted(doc_structure.keys(), key=lambda x: int(x)):
                    if count >= max_pages: break
                    chunk = doc_structure[p_num]
                    page_content = " ".join(chunk) if isinstance(chunk, list) else chunk
                    full_text += f"Page {int(p_num)+1}: {page_content[:300]}...\n"
                    count += 1
                
                response_text = gc.generate_response("SUMMARIZE", full_text, user_question="Summarize this entire document based on these excerpts.")
            else:
                # Default: Page Summary
                response_text = gc.generate_response("SUMMARIZE", current_text)
            
            response_type = "summary"
        elif intent == "EXPLAIN":
             # Use user utterance as context/question if available
             # Force using utterance to capture details like "11th sentence"
            question = user_utterance if user_utterance else "Explain this page."
            response_text = gc.generate_response("EXPLAIN", current_text, user_question=question)
            response_type = "explanation"
        elif intent == "TRANSLATE":
            lang = entities.get("target_language", "English")
            response_text = gc.generate_response("TRANSLATE", current_text, target_language=lang)
            response_type = "translation"
        elif intent == "QUIZ":
            raw_response = gc.generate_response("QUIZ", current_text)
            try:
                # Attempt to clean potential markdown formatting
                json_str = raw_response
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0]
                
                quiz_data = json.loads(json_str.strip())
                payload = {"quiz": quiz_data}
                
                # Format text for TTS (Reading only the first question to avoid overwhelming)
                response_text = "Here is a quiz question. "
                if quiz_data and isinstance(quiz_data, list):
                    q = quiz_data[0]
                    response_text += f"{q.get('question')} "
                    opts = q.get('options', [])
                    response_text += "Options are: " + ", ".join(opts) + "."
                else:
                    response_text = "I generated a quiz but it looks empty."

            except Exception as e:
                logger.error(f"Failed to parse Quiz JSON: {e}. Raw: {raw_response}")
                response_text = "I had trouble generating the quiz. Please try again."
            
            response_type = "quiz"

    elif intent == "EXPLAIN_LINE":
        target = entities.get("target_line")
        current_text = get_text_chunk(doc_structure, page, 0)
        if isinstance(doc_structure[str(page)], list):
             current_text = " ".join(doc_structure[str(page)])
        else:
             current_text = doc_structure[str(page)]
        
        # Split by newlines (assuming PDF text has line breaks)
        # Attempt to be robust to empty lines
        lines = [l.strip() for l in current_text.split('\n') if l.strip()]
        
        if target is not None and 0 <= target < len(lines):
            line_content = lines[target]
            prompt = f"Explain this specific sentence contextually: '{line_content}'"
            response_text = gc.generate_response("EXPLAIN", current_text, user_question=prompt)
            response_type = "explanation"
        else:
            response_text = f"I couldn't find line {target + 1}."
            response_type = "error"
    
    elif intent == "READ_PAGE": # Helper for "Read this page"
        if isinstance(doc_structure[str(page)], list):
             text_to_read = " ".join(doc_structure[str(page)])
        else:
             text_to_read = doc_structure[str(page)]
        
        # Limit length?
        response_text = text_to_read[:500] + "..." if len(text_to_read) > 500 else text_to_read
        response_type = "read"

        response_text = text_to_read[:500] + "..." if len(text_to_read) > 500 else text_to_read
        response_type = "read"

    elif intent == "HELP":
        response_text = "I can Summarize the page, Explain specific details, Translate to other languages like Tamil or Hindi, Take a Quiz, or simply Read the text. Just say 'Wake' to start."
        response_type = "help"

    elif intent == "OPEN_DOCUMENT":
        target_name = entities.get("filename", "").lower()
        # Search library for matching file
        found_id = None
        if os.path.exists(UPLOADS_DIR):
            for f in os.listdir(UPLOADS_DIR):
                if f.endswith(".pdf"):
                    # Fuzzy match: "phravin" in "phravin.pdf"
                    f_clean = f.lower().replace(".pdf", "")
                    if target_name in f_clean:
                        found_id = f.replace(".pdf", "") # ID is sanitized filename
                        break
        
        if found_id:
            response_text = f"Opening {found_id}."
            response_type = "open_document"
            payload = {"doc_id": found_id} # Tell frontend to switch
        else:
            response_text = f"I couldn't find a document named {target_name}."
            response_type = "error"

    else:

         if user_utterance:
             # Fallback: Ask Gemini to handle it as a general question/explanation
             if user_utterance.lower().strip() in ["hi", "hello", "wake", "wake up"]:
                 response_text = "Hi there! I'm ready to help you learn. What would you like to do?"
                 response_type = "conversation"
             else:
                 response_text = gc.generate_response("EXPLAIN", current_text, user_question=user_utterance)
                 response_type = "explanation"
         else:
             response_text = ""

    # Generate Audio
    audio_url = None
    if response_text:
        fname = _generate_audio(response_text)
        if fname:
            audio_url = f"/audio/{fname}"

    return jsonify({
        "intent": intent,
        "type": response_type,
        "payload": payload, # Can populate with JSON for Quiz later
        "text_response": response_text,
        "audio_url": audio_url,
        "new_page": next_page
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
