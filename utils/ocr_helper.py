import os
import shutil
import pytesseract
from PIL import Image, ImageFilter, ImageOps, ImageEnhance
import pdfplumber
import tempfile

# easyocr is an optional fallback OCR engine (installed via requirements.txt)
try:
    import easyocr
except Exception:
    easyocr = None


def _find_tesseract_executable() -> str:
    """Locate the Tesseract executable from PATH, environment, or common install locations."""
    env_path = os.getenv("TESSERACT_CMD")
    if env_path and os.path.exists(env_path):
        return env_path

    # Use shutil.which to find tesseract on PATH
    executable = shutil.which("tesseract")
    if executable:
        return executable

    # Common Windows install locations
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    raise FileNotFoundError(
        "Tesseract OCR executable not found. Please install Tesseract and ensure it is on your PATH, "
        "or set the TESSERACT_CMD environment variable to the tesseract executable path."
    )


def extract_text_from_file(filepath: str) -> str:
    """Extract text from an image (PNG, JPG, JPEG) or a PDF file."""
    ext = os.path.splitext(filepath)[1].lower()
    extracted_text = ""

    try:
        if ext in ['.png', '.jpg', '.jpeg']:
            image = Image.open(filepath).convert('RGB')
            # Basic preprocessing to improve OCR accuracy
            try:
                image = ImageOps.grayscale(image)
                image = image.filter(ImageFilter.SHARPEN)
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.5)
            except Exception:
                pass

            try:
                pytesseract.pytesseract.tesseract_cmd = _find_tesseract_executable()
                extracted_text = pytesseract.image_to_string(image)
                if not extracted_text.strip():
                    raise ValueError("Empty OCR from Tesseract")
            except Exception:
                # Fallback to easyocr if available
                if easyocr is None:
                    raise
                reader = easyocr.Reader(["en"], gpu=False)
                try:
                    results = reader.readtext(filepath, detail=0)
                    extracted_text = "\n".join(results)
                except Exception:
                    # As a last resort, try running easyocr on PIL image bytes
                    try:
                        import numpy as np
                        img_arr = np.array(image)
                        results = reader.readtext(img_arr, detail=0)
                        extracted_text = "\n".join(results)
                    except Exception as e:
                        print(f"[ERROR] EasyOCR fallback failed: {e}")
                        raise

        elif ext == '.pdf':
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    if text.strip():
                        extracted_text += text + "\n"
                    else:
                        # Try OCR on the page image if text extraction failed
                        try:
                            pytesseract.pytesseract.tesseract_cmd = _find_tesseract_executable()
                            pil_image = page.to_image(resolution=300).original
                            pil_image = pil_image.convert('RGB')
                            pil_image = ImageOps.grayscale(pil_image)
                            pil_image = pil_image.filter(ImageFilter.SHARPEN)
                            page_text = pytesseract.image_to_string(pil_image)
                            if page_text and page_text.strip():
                                extracted_text += page_text + "\n"
                            else:
                                raise ValueError("Empty OCR from Tesseract on PDF page")
                        except Exception:
                            if easyocr is None:
                                # Render page to temp PNG and re-raise
                                pil_image = page.to_image(resolution=300).original
                                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                                    tmp_path = tmp.name
                                    pil_image.save(tmp_path)
                                try:
                                    reader = easyocr.Reader(["en"], gpu=False)
                                    results = reader.readtext(tmp_path, detail=0)
                                    extracted_text += "\n".join(results) + "\n"
                                finally:
                                    try:
                                        os.remove(tmp_path)
                                    except Exception:
                                        pass
                            else:
                                # Use easyocr directly on page image
                                pil_image = page.to_image(resolution=300).original
                                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                                    tmp_path = tmp.name
                                    pil_image.save(tmp_path)
                                try:
                                    reader = easyocr.Reader(["en"], gpu=False)
                                    results = reader.readtext(tmp_path, detail=0)
                                    extracted_text += "\n".join(results) + "\n"
                                finally:
                                    try:
                                        os.remove(tmp_path)
                                    except Exception:
                                        pass
    except FileNotFoundError as exc:
        print(f"[ERROR] Tesseract OCR not found: {exc}")
        # Don't raise; return empty string to allow parsers to fallback gracefully
        return ""
    except Exception as exc:
        print(f"[ERROR] Failed to extract text from {filepath}: {exc}")
        return ""

    return extracted_text.strip()


