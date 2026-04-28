import base64
import io
import requests
from config import Config

VISION_URL = "https://vision.googleapis.com/v1/images:annotate"


def _call_google_vision(image_bytes):
    if not Config.GOOGLE_API_KEY:
        return None

    payload = {
        "requests": [
            {
                "image": {"content": base64.b64encode(image_bytes).decode("utf-8")},
                "features": [{"type": "TEXT_DETECTION", "maxResults": 1}],
            }
        ]
    }

    try:
        response = requests.post(f"{VISION_URL}?key={Config.GOOGLE_API_KEY}", json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        annotations = result.get("responses", [{}])[0]
        full_text = annotations.get("fullTextAnnotation")
        if full_text and full_text.get("text"):
            return full_text["text"].strip()
        text_annotations = annotations.get("textAnnotations")
        if text_annotations and len(text_annotations) > 0:
            return text_annotations[0].get("description", "").strip()
    except Exception:
        return None

    return None


def extract_text_from_image_bytes(image_bytes):
    if Config.GOOGLE_API_KEY:
        google_text = _call_google_vision(image_bytes)
        if google_text:
            return google_text
    return ""


def extract_text_from_pdf(file_bytes):
    text_pages = []

    try:
        import PyPDF2

        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_pages.append(page_text)
        if text_pages:
            return "\n".join(text_pages)
    except Exception:
        pass

    return ""


def extract_text_from_upload(uploaded_file):
    filename = uploaded_file.filename.lower() if hasattr(uploaded_file, "filename") else ""
    try:
        file_bytes = uploaded_file.read()
    except Exception:
        return ""

    if filename.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)

    return extract_text_from_image_bytes(file_bytes)
