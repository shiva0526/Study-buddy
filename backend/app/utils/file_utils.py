import os
from fastapi import UploadFile

UPLOAD_DIR = "uploads"

def safe_filename(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in (" ", ".", "_", "-")).rstrip()

def save_upload_file(upload: UploadFile, plan_id: str) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"{plan_id}_{safe_filename(upload.filename)}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(upload.file.read())
    return path
