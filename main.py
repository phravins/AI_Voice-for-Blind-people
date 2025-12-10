import logging
from modules.pdf_parser import extract_text_from_pdf
from modules.dialogue_manager import DialogueManager, cleanup_temp_audio
import sys
import os

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler(sys.stdout) # Also print to console
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting AI Voice Tutor Application...")
    
    # Simple CLI input for PDF path
    if len(sys.argv) > 1:
        selected_pdf_path = sys.argv[1]
    else:
        print("Please enter the path to the PDF file:")
        selected_pdf_path = input().strip()
        # Remove quotes if user added them
        if selected_pdf_path.startswith('"') and selected_pdf_path.endswith('"'):
            selected_pdf_path = selected_pdf_path[1:-1]

    if not os.path.exists(selected_pdf_path) or not selected_pdf_path.lower().endswith(".pdf"):
        logger.error("Invalid PDF path provided.")
        print("Error: Please provide a valid PDF file path.")
        return

    logger.info(f"Selected PDF: {selected_pdf_path}")

    # --- 2. Extract Text from PDF ---
    doc_structure = extract_text_from_pdf(selected_pdf_path)
    if not doc_structure:
        logger.error("Failed to extract text from the selected PDF.")
        print("Error: Failed to extract text from the PDF.")
        return

    # --- 3. Initialize and Start Dialogue Manager ---
    try:
        dm = DialogueManager(doc_structure)
        dm.start_conversation()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user.")
    except Exception as e:
        logger.error(f"An error occurred during execution: {e}")
        print(f"An error occurred: {e}")
    finally:
        # --- 4. Cleanup ---
        cleanup_temp_audio()
        logger.info("Application finished.")

if __name__ == "__main__":
    main()
