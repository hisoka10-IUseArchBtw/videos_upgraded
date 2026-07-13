import pytesseract
from PIL import Image
import os
import re

def clean_ocr_text(text: str) -> str:
    """Removes excessive whitespace and junk from OCR text."""
    # Replace multiple spaces/newlines with a single space
    cleaned = re.sub(r'\s+', ' ', text)
    return cleaned.strip()

def extract_text_from_image(image_path: str) -> str:
    """Runs Tesseract OCR on a single image and returns the cleaned text."""
    if not os.path.exists(image_path):
        return ""
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
        return clean_ocr_text(text)
    except Exception as e:
        print(f"OCR Error on {image_path}: {e}")
        return ""

def process_frames_for_ocr(frame_paths: list) -> list:
    """
    Runs OCR on a list of frames.
    Filters out consecutive duplicates or nearly identical text to avoid spam.
    Returns a list of dicts with 'text', and 'frame_path'.
    """
    results = []
    last_text = ""
    
    for path in frame_paths:
        text = extract_text_from_image(path)
        if len(text) > 20: # ignore very short junk
            # Simple deduplication: if it's the exact same as the last slide, skip it
            # In a real app, you might use text similarity (like Levenshtein)
            if text != last_text:
                results.append({
                    "text": text,
                    "frame_path": path
                })
                last_text = text
                
    return results
