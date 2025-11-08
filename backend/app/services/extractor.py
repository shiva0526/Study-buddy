import os

def extract_text(filepath: str) -> str:
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext in [".txt", ".md"]:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        if ext == ".pdf":
            import fitz  # PyMuPDF
            doc = fitz.open(filepath)
            text = ""
            for page in doc:
                text += page.get_text()
            return text
        if ext in [".jpg", ".jpeg", ".png"]:
            try:
                from PIL import Image
            except Exception as e:
                print("PIL import error:", e)
                return ""
            try:
                try:
                    import pytesseract
                except Exception:
                    try:
                        import subprocess, sys, importlib
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "pytesseract"])
                        pytesseract = importlib.import_module("pytesseract")
                    except Exception as e:
                        print("pytesseract import/install failed:", e)
                        raise
            except Exception:
                # pytesseract may not be installed in the environment; provide a clear message and skip OCR
                print("pytesseract is not installed; install with 'pip install pytesseract' and the Tesseract OCR engine.")
                return ""
            try:
                text = pytesseract.image_to_string(Image.open(filepath))
                return text
            except Exception as e:
                print("OCR extraction error:", e)
                return ""
    except Exception as e:
        print("Extraction error:", e)
    return ""
