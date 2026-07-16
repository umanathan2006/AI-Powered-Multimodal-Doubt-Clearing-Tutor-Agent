import base64
import requests


def caption_image(image_path: str) -> str:
    """Caption an image using a local Ollama vision model."""
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "model": "llava",
        "prompt": (
            "Describe the contents of this image in detail, focusing on labels, structure, "
            "and any diagram or object relationships that would help explain the subject matter. "
            "Keep the description factual and suitable for retrieval in a study assistant."
        ),
        "images": [image_base64],
        "stream": False,
    }

    response = requests.post(
        "http://127.0.0.1:11434/api/generate", json=payload, timeout=120
    )
    response.raise_for_status()
    data = response.json()

    return data.get("response", "")
