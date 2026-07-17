import pytesseract
from PIL import Image, ImageFilter, ImageOps
import os
import re
from difflib import SequenceMatcher

# ---------------------------------------------------------------------------
# Tesseract configuration
# --oem 3  → use both legacy + LSTM engines (best accuracy)
# --psm 6  → assume a single uniform block of text (good for slides/screens)
# ---------------------------------------------------------------------------
TESSERACT_CONFIG = "--oem 3 --psm 6"

# Minimum ratio of identical chars to consider two OCR results "duplicates"
DEDUP_SIMILARITY_THRESHOLD = 0.85

# Minimum average confidence (0-100) for an OCR result to be kept
MIN_CONFIDENCE = 40

# Minimum character count after cleaning
MIN_TEXT_LENGTH = 20


# ---------------------------------------------------------------------------
# Image pre-processing
# ---------------------------------------------------------------------------

def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Enhance an image for better Tesseract accuracy:
      1. Convert to grayscale
      2. Upscale small images (Tesseract works best at ~300 DPI / 1500px+ wide)
      3. Apply a mild sharpening filter
      4. Apply Otsu-style auto-threshold via point() to binarise the image
    """
    # 1. Grayscale
    image = image.convert("L")

    # 2. Upscale if too small (Tesseract accuracy degrades below ~600px width)
    min_width = 1200
    if image.width < min_width:
        scale = min_width / image.width
        new_size = (int(image.width * scale), int(image.height * scale))
        image = image.resize(new_size, Image.LANCZOS)

    # 3. Sharpen edges to help with thin fonts
    image = image.filter(ImageFilter.SHARPEN)

    # 4. Binarise: pixels below the midpoint become black, above become white.
    #    This dramatically cuts noise on slides and screen recordings.
    threshold = 140
    image = image.point(lambda p: 255 if p > threshold else 0)

    return image


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

def clean_ocr_text(text: str) -> str:
    """
    Clean raw Tesseract output:
      - Strip leading/trailing whitespace per line
      - Remove lines that are purely punctuation/symbols (OCR artefacts)
      - Collapse runs of blank lines to a single blank line
      - Strip overall leading/trailing whitespace
    """
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Drop lines that are nothing but non-alphanumeric noise
        if stripped and re.search(r'[A-Za-z0-9]', stripped):
            cleaned_lines.append(stripped)
        elif not stripped:
            # Keep blank lines as paragraph separators (but collapse later)
            cleaned_lines.append("")

    # Collapse consecutive blank lines
    result_lines = []
    prev_blank = False
    for line in cleaned_lines:
        if line == "":
            if not prev_blank:
                result_lines.append(line)
            prev_blank = True
        else:
            result_lines.append(line)
            prev_blank = False

    return "\n".join(result_lines).strip()


# ---------------------------------------------------------------------------
# Confidence filtering
# ---------------------------------------------------------------------------

def _get_ocr_confidence(image: Image.Image) -> float:
    """
    Returns the mean word-level confidence reported by Tesseract (0-100).
    Words with confidence == -1 (layout noise) are excluded.
    Returns 0.0 if Tesseract produces no usable data.
    """
    try:
        data = pytesseract.image_to_data(
            image,
            config=TESSERACT_CONFIG,
            output_type=pytesseract.Output.DICT,
        )
        confidences = [c for c in data["conf"] if c != -1]
        return sum(confidences) / len(confidences) if confidences else 0.0
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_text_from_image(image_path: str) -> dict:
    """
    Runs Tesseract OCR on a single image.

    Returns a dict:
        {
            "text": str,          # cleaned OCR text (empty string if unusable)
            "confidence": float,  # mean Tesseract word confidence (0-100)
        }
    """
    if not os.path.exists(image_path):
        return {"text": "", "confidence": 0.0}

    try:
        raw_image = Image.open(image_path)
        processed = preprocess_image(raw_image)

        confidence = _get_ocr_confidence(processed)

        if confidence < MIN_CONFIDENCE:
            return {"text": "", "confidence": confidence}

        raw_text = pytesseract.image_to_string(processed, config=TESSERACT_CONFIG)
        cleaned = clean_ocr_text(raw_text)
        return {"text": cleaned, "confidence": confidence}

    except Exception as e:
        print(f"OCR Error on {image_path}: {e}")
        return {"text": "", "confidence": 0.0}


def _is_duplicate(text_a: str, text_b: str) -> bool:
    """
    Returns True if two OCR strings are considered duplicates via fuzzy matching.
    Uses SequenceMatcher (stdlib difflib) — no extra dependencies required.
    """
    if not text_a or not text_b:
        return False
    ratio = SequenceMatcher(None, text_a, text_b).ratio()
    return ratio >= DEDUP_SIMILARITY_THRESHOLD


def process_frames_for_ocr(frame_paths: list) -> list:
    """
    Runs OCR on a list of frame image paths.

    Improvements over the original:
      - Image preprocessing before Tesseract
      - Confidence-based filtering (drops low-quality reads)
      - Fuzzy deduplication (catches near-identical consecutive slides)
      - Preserves confidence score in output for downstream ranking

    Returns a list of dicts:
        [{"text": str, "frame_path": str, "confidence": float}, ...]
    """
    results = []
    last_text = ""

    for path in frame_paths:
        result = extract_text_from_image(path)
        text = result["text"]
        confidence = result["confidence"]

        if len(text) < MIN_TEXT_LENGTH:
            continue  # Too short — likely noise or an empty frame

        if _is_duplicate(text, last_text):
            continue  # Near-identical to previous slide — skip

        results.append({
            "text": text,
            "frame_path": path,
            "confidence": round(confidence, 1),
        })
        last_text = text

    return results
