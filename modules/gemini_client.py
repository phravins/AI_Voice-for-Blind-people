import google.generativeai as genai
import logging
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-flash-latest')
        logger.info("Gemini client initialized.")

    def _build_prompt(self, intent, context_text, user_question=None, target_language=None, difficulty="medium"):
        """Builds a specific prompt for the Gemini model based on intent."""
        
        system_instruction = "You are an AI Voice Tutor. Your goal is to explain things directly, simply, and briefly. Keep answers short (2-3 sentences max) unless asked otherwise. Use simple vocabulary. Do not use markdown."
        
        if intent == "SUMMARIZE":
            return f"""
            {system_instruction}
            ROLE: Patient Teacher
            CONTEXT:
            {context_text}
            USER REQUEST: Write a single cohesive paragraph summary (6–9 sentences) in simple, clear language. Do not use bullet points or lists.
            """
        elif intent == "EXPLAIN":
            question_part = f" QUESTION: {user_question}" if user_question else ""
            return f"""
            {system_instruction}
            ROLE: Patient Teacher
            CONTEXT:
            {context_text}
            USER REQUEST: Explain the following concept step by step in simple terms, with examples. {question_part}
            """
        elif intent == "TRANSLATE":
            return f"""
            {system_instruction}
            ROLE: Translator
            CONTEXT:
            {context_text}
            USER REQUEST: Translate the text into {target_language}. Keep the meaning accurate but simplify difficult words if necessary.
            """
        elif intent == "QUIZ":
             return f"""
             {system_instruction}
             ROLE: Quiz Master
             CONTEXT:
             {context_text}
             USER REQUEST: Create 3 {difficulty} difficulty quiz questions based on the content. 
             Provide the output in strict JSON format as a list of objects, where each object has 'question', 'options' (list of strings), and 'answer' (correct option string).
             Example format:
             [
                {{"question": "...", "options": ["a", "b", "c", "d"], "answer": "..."}}
             ]
             Do not include any markdown formatting or code blocks, just the raw JSON string.
             """
        else: # Default fallback
             return f"""
             {system_instruction}
             ROLE: Assistant
             CONTEXT:
             {context_text}
             USER REQUEST: The user has a command related to this content: {intent}. Respond appropriately.
             """

    def generate_response(self, intent, context_text, user_question=None, target_language=None, difficulty="medium"):
        """Generates a response from Gemini based on the intent and context."""
        try:
            prompt = self._build_prompt(intent, context_text, user_question, target_language, difficulty)
            logger.debug(f"Sending prompt to Gemini: {prompt[:100]}...") 

            # Relax safety settings to prevent blocking educational content
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]

            # Retry logic for 429 errors
            import time
            max_retries = 3
            base_delay = 2

            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(prompt, safety_settings=safety_settings)
                    
                    # Safe access to text
                    if response.candidates and response.candidates[0].content.parts:
                        generated_text = response.text
                        logger.info(f"Gemini response received for intent '{intent}'.")
                        return generated_text
                    else:
                         # If empty but NO exception, it might be safety blocked. Don't retry this loop.
                         logger.warning(f"Gemini returned no text. Finish reason: {response.candidates[0].finish_reason if response.candidates else 'Unknown'}")
                         return "I couldn't generate a response. The content might be flagged or empty."

                except Exception as e:
                    if "429" in str(e):
                        if attempt < max_retries - 1:
                            wait_time = base_delay * (2 ** attempt)
                            logger.warning(f"Gemini 429 Rate Limit. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                            time.sleep(wait_time)
                            continue
                        else:
                            logger.error("Gemini 429 Rate Limit persisted after retries.")
                            return "I'm currently overwhelmed with requests. Please wait a moment and try again."
                    else:
                        raise e # Re-raise other errors to be caught by outer block or just break

        except Exception as e:
            logger.error(f"Error generating response from Gemini: {e}")
            if "429" in str(e): # Fallback if retry loop failed
                return "I'm currently overwhelmed with requests. Please wait a moment and try again."
            return f"Sorry, I encountered an error: {e}"
