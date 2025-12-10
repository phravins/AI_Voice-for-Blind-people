import logging
from modules.speech_processor import SpeechProcessor
from modules.intent_recognizer import IntentRecognizer
from modules.gemini_client import GeminiClient
from modules.text_processor import get_text_chunk
from config import TEMP_AUDIO_DIR
import os
import json

logger = logging.getLogger(__name__)

class DialogueManager:
    def __init__(self, doc_structure):
        self.sp = SpeechProcessor()
        self.ir = IntentRecognizer()
        self.gc = GeminiClient()
        self.doc_structure = doc_structure
        self.current_page = 0
        self.current_chunk = 0
        self.last_response = ""
        self.session_active = True

    def start_conversation(self):
        """Starts the main interaction loop."""
        welcome_msg = "Welcome to the AI Voice Tutor. I have loaded your document. You can ask me to summarize, explain, translate, give a quiz, or navigate pages. What would you like to do?"
        self.sp.speak_text(welcome_msg)
        logger.info("Dialogue manager started.")

        while self.session_active:
            try:
                # Listen for command
                command_text = self.sp.listen_for_command()
                if not command_text:
                    # If no command is heard, prompt again
                    self.sp.speak_text("I didn't catch that. Please repeat your command.")
                    continue

                # Recognize intent
                parsed_intent = self.ir.recognize_intent(command_text)

                # Process the intent
                self._handle_intent(parsed_intent, command_text)

            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received. Stopping session.")
                self.session_active = False
                goodbye_msg = "Goodbye. Thank you for using the AI Voice Tutor."
                self.sp.speak_text(goodbye_msg)
            except Exception as e:
                logger.error(f"An error occurred in the dialogue loop: {e}")
                self.sp.speak_text("An error occurred. Please try again or restart the application.")

    def _handle_intent(self, parsed_intent, command_text=""):
        """Handles the recognized intent and updates the state."""
        intent = parsed_intent["intent"]
        entities = parsed_intent["entities"]

        if intent == "STOP":
            self.session_active = False
            self.sp.speak_text("Stopping the session. Goodbye.")
            return

        # --- Navigation ---
        if intent == "NAVIGATE_NEXT":
            if self.current_page < len(self.doc_structure) - 1:
                self.current_page += 1
                self.current_chunk = 0 # Reset chunk index on new page
                msg = f"Moved to page {self.current_page + 1}. Current chunk index reset to 0."
                self.sp.speak_text(msg)
                logger.info(msg)
            else:
                self.sp.speak_text("You are already on the last page.")
        elif intent == "NAVIGATE_PREV":
            if self.current_page > 0:
                self.current_page -= 1
                self.current_chunk = 0 # Reset chunk index on new page
                msg = f"Moved to page {self.current_page + 1}. Current chunk index reset to 0."
                self.sp.speak_text(msg)
                logger.info(msg)
            else:
                self.sp.speak_text("You are on the first page.")
        elif intent == "NAVIGATE_PAGE":
            target_page = entities.get("target_page")
            if target_page is not None and 0 <= target_page < len(self.doc_structure):
                self.current_page = target_page
                self.current_chunk = 0 # Reset chunk index on new page
                msg = f"Navigated to page {self.current_page + 1}. Current chunk index reset to 0."
                self.sp.speak_text(msg)
                logger.info(msg)
            else:
                self.sp.speak_text("Sorry, that page number is invalid.")

        elif intent == "READ_PARAGRAPH":
            target_para = entities.get("target_paragraph")
            # Assuming chunks map roughly to paragraphs or sections
            if target_para is not None:
                chunks = self.doc_structure.get(self.current_page, [])
                if 0 <= target_para < len(chunks):
                    self.current_chunk = target_para
                    text_to_read = chunks[self.current_chunk]
                    self.sp.speak_text(f"Reading paragraph {target_para + 1}: {text_to_read}")
                else:
                    self.sp.speak_text("Invalid paragraph number for this page.")
            else:
                self.sp.speak_text("Please specify which paragraph to read.")

        # --- Content Actions ---
        elif intent in ["SUMMARIZE", "EXPLAIN", "TRANSLATE", "QUIZ"]:
            context_chunk = get_text_chunk(self.doc_structure, self.current_page, self.current_chunk)
            if not context_chunk:
                self.sp.speak_text("No content available on the current page or chunk to process.")
                return

            response_text = ""
            if intent == "SUMMARIZE":
                response_text = self.gc.generate_response("SUMMARIZE", context_chunk)
            elif intent == "EXPLAIN":
                 # For explanation, we might pass the command_text as the question
                 response_text = self.gc.generate_response("EXPLAIN", context_chunk, user_question=command_text)
            elif intent == "TRANSLATE":
                 target_lang = entities.get("target_language", "English") # Default if not specified in command
                 response_text = self.gc.generate_response("TRANSLATE", context_chunk, target_language=target_lang)
            elif intent == "QUIZ":
                 difficulty = entities.get("difficulty", "medium")
                 response_text = self.gc.generate_response("QUIZ", context_chunk, difficulty=difficulty)
                 try:
                     quiz_data = json.loads(response_text)
                     # Simple interaction: read first question
                     if isinstance(quiz_data, list) and len(quiz_data) > 0:
                         q1 = quiz_data[0]
                         response_text = f"Here is a {difficulty} quiz. Question 1: {q1['question']}. Options are: {', '.join(q1['options'])}."
                     else:
                         response_text = "I couldn't generate a valid quiz."
                 except json.JSONDecodeError:
                     logger.warning("Failed to parse quiz JSON. Speaking raw text.")
                     pass

            if response_text:
                self.last_response = response_text
                self.sp.speak_text(response_text)
                logger.info(f"Processed intent '{intent}' for page {self.current_page}, chunk {self.current_chunk}.")
            else:
                 self.sp.speak_text("Sorry, I couldn't generate a response for that.")

        elif intent == "REPEAT":
            if self.last_response:
                self.sp.speak_text(self.last_response)
            else:
                self.sp.speak_text("Nothing to repeat.")
        elif intent == "UNKNOWN":
            self.sp.speak_text("Sorry, I didn't understand that command. Please try again.")
        else:
            # Handle other potential intents if added later
            self.sp.speak_text("Sorry, that command is not yet implemented.")

# --- Helper function to clean up temporary audio files ---
def cleanup_temp_audio():
    for filename in os.listdir(TEMP_AUDIO_DIR):
        if filename.endswith(".mp3"):
            file_path = os.path.join(TEMP_AUDIO_DIR, filename)
            try:
                os.remove(file_path)
                logger.info(f"Deleted temporary audio file: {filename}")
            except Exception as e:
                logger.error(f"Could not delete temporary file {file_path}: {e}")