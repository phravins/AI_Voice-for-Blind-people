import logging
import pdfplumber
import pytesseract
from PIL import Image
import io
import PyPDF2
from config import CHUNK_SIZE, TESSERACT_CMD, POPPLER_PATH

logger = logging.getLogger(__name__)

def _split_text_chunks(text, chunk_size=CHUNK_SIZE):
    """Splits text into smaller chunks."""
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        chunks.append(chunk)
    return chunks

def _is_scanned_pdf(pdf_path):
    """Attempts to determine if a PDF is scanned by checking for text on first few pages."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i in range(min(3, len(pdf.pages))): # Check first 3 pages or fewer
                page = pdf.pages[i]
                text = page.extract_text()
                if text and len(text.strip()) > 10: # Arbitrary check for substantial text
                    return False # Found text, likely not scanned
        logger.info(f"PDF {pdf_path} appears to be scanned based on text extraction.")
        return True
    except Exception as e:
        logger.error(f"Error checking if PDF is scanned: {e}")
        return True # Assume scanned if check fails

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF, preferring native extraction and falling back to OCR.
    Returns a dict: {page_num: [chunks]} and never returns None.
    """
    logger.info(f"Starting PDF processing for: {pdf_path}")
    native = _extract_text_native(pdf_path)
    has_text = any(chunks and any(c.strip() for c in chunks) for chunks in native.values())
    if has_text:
        logger.info("Using native text extraction.")
        return native
    logger.info("Native extraction yielded little/no text, attempting OCR...")
    ocr = _extract_text_scanned(pdf_path)
    if ocr and any(chunks and any(c.strip() for c in chunks) for chunks in ocr.values()):
        logger.info("Using OCR extraction.")
        return ocr
    logger.warning("OCR also yielded little/no text; returning native structure as fallback.")
    return native if native else {0: [""]}

def _extract_text_native(pdf_path):
    """Extracts text from a native PDF using pdfplumber."""
    doc_structure = {}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    clean_text = page_text.strip()
                    chunks = _split_text_chunks(clean_text)
                    doc_structure[i] = chunks
                else:
                    doc_structure[i] = [""] # Handle empty pages
    except Exception as e:
        logger.error(f"Error extracting text from native PDF: {e}")
    return doc_structure

def _extract_text_scanned(pdf_path):
    """Extracts text from a scanned PDF using OCR."""
    doc_structure = {}
    try:
        if TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
        # Use PyPDF2 to get the number of pages and convert pages to images
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)

        # Use pdf2image if available, otherwise, we'll need to install it or find an alternative
        # For this implementation, we'll assume pdf2image is available or handled separately
        # A common way is to use pdf2image with Pillow for conversion
        # pip install pdf2image # This requires poppler on the system
        from pdf2image import convert_from_path
        kwargs = {"dpi": 200}
        if POPPLER_PATH:
            # Accept both root and bin path; if root, append common bin subfolder
            poppler_candidate = POPPLER_PATH
            if os.path.isdir(poppler_candidate):
                bin_path = os.path.join(poppler_candidate, "Library", "bin")
                if os.path.isdir(bin_path):
                    poppler_candidate = bin_path
                else:
                    alt_bin = os.path.join(poppler_candidate, "bin")
                    if os.path.isdir(alt_bin):
                        poppler_candidate = alt_bin
            kwargs["poppler_path"] = poppler_candidate
        pages = convert_from_path(pdf_path, **kwargs)

        for i, page_image in enumerate(pages):
            # Convert PIL image to bytes for pytesseract if needed, or pass directly
            text = pytesseract.image_to_string(page_image)
            if text.strip():
                clean_text = text.strip()
                chunks = _split_text_chunks(clean_text)
                doc_structure[i] = chunks
            else:
                doc_structure[i] = [""] # Handle pages where OCR finds no text
    except ImportError:
        logger.error("pdf2image not found. Please install it: pip install pdf2image")
        logger.error("Also ensure poppler is installed on your system.")
        return {}
    except Exception as e:
        logger.error(f"Error extracting text from scanned PDF: {e}")
    return doc_structure
