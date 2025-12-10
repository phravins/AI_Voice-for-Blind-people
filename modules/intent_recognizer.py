import re
import logging

logger = logging.getLogger(__name__)

class IntentRecognizer:
    def __init__(self):
        self.intents = {
            "SUMMARIZE": [r"summarize", r"summary of", r"what is the summary"],
            "EXPLAIN": [r"explain", r"what is", r"what does", r"define", r"describe", r"tell me about", r"meaning of"],
            "TRANSLATE": [r"translate", r"translation", r"change language", r"speak in", r"convert to"],
            "EXPLAIN_LINE": [r"explain line (\d+)", r"explain sentence (\d+)", r"detail line (\d+)"],
            "QUIZ": [r"quiz", r"question", r"test me", r"ask me"],
            "NAVIGATE_NEXT": [r"next page", r"go to next", r"next"],
            "NAVIGATE_PREV": [r"previous page", r"go to previous", r"back", r"previous"],
            "NAVIGATE_PAGE": [r"go to page (\d+)", r"read page (\d+)", r"page (\d+)"],
            "READ_PARAGRAPH": [r"read paragraph (\d+)", r"paragraph (\d+)"],
            "REPEAT": [r"repeat", r"say again", r"repeat that"],
            "STOP": [r"stop", r"exit", r"quit", r"end session"],
            "HELP": [r"help", r"what can you do", r"capabilities", r"commands"]
        }

    def recognize_intent(self, command_text):
        """Recognizes the intent and extracts entities from the command text."""
        command_text_lower = command_text.lower().strip()
        if not command_text_lower:
            return {"intent": "UNKNOWN", "entities": {}}
        
        logger.info(f"Recognizing intent for: '{command_text_lower}'")

        for intent, patterns in self.intents.items():
            for pattern in patterns:
                match = re.search(pattern, command_text_lower)
                if match:
                    entities = {}
                    
                    if intent == "NAVIGATE_PAGE":
                        try:
                            page_num = int(match.group(1))
                            entities["target_page"] = page_num - 1 # Convert to 0-indexed
                        except (IndexError, ValueError):
                            pass # Or fallback
                    
                    elif intent == "EXPLAIN_LINE":
                         try:
                            line_num = int(match.group(1))
                            entities["target_line"] = line_num - 1
                         except:
                             pass

                    elif intent == "TRANSLATE":
                        # Dynamic language extraction using regex from the original command
                        lang_match = re.search(r"(?:to|in|into)\s+(\w+)", command_text_lower)
                        if lang_match:
                            entities["target_language"] = lang_match.group(1).capitalize()
                        else:
                            entities["target_language"] = "English"

                    elif intent == "OPEN_DOCUMENT":
                        # Capture filename: "open phravin", "load phravin pdf"
                        # Regex to capture everything after open/load/switch to
                        name_match = re.search(r"(?:open|load|switch to|read)\s+(?:the\s+)?(.+)", command_text_lower)
                        if name_match:
                            raw_name = name_match.group(1).replace("pdf", "").strip()
                            entities["filename"] = raw_name

                    elif intent == "READ_PARAGRAPH":
                        try:
                            para_num = int(match.group(1))
                            entities["target_paragraph"] = para_num - 1 # Convert to 0-indexed
                        except:
                            pass
                            
                    elif intent == "QUIZ":
                        if "hard" in command_text_lower:
                            entities["difficulty"] = "hard"
                        elif "easy" in command_text_lower:
                            entities["difficulty"] = "easy"
                        else:
                            entities["difficulty"] = "medium"

                    logger.info(f"Recognized intent: {intent}, Entities: {entities}")
                    return {"intent": intent, "entities": entities}

        logger.info("Intent not recognized, defaulting to UNKNOWN.")
        return {"intent": "UNKNOWN", "entities": {}}