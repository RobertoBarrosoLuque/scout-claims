import json
from typing import Literal

from fireworks.llm import LLM
from src.configs.load_config import PROMPT_LIBRARY, APP_STEPS_CONFIGS
from pydantic import BaseModel
from pathlib import Path
from PIL import Image
import io
import base64


class IncidentAnalysis(BaseModel):
    description: str
    location: Literal["front-left", "front-right", "back-left", "back-right"]
    severity: Literal["minor", "moderate", "major"]


def get_llm(api_key: str, model: str, temperature: float) -> LLM:
    return LLM(
        model=model,
        temperature=temperature,
        deployment_type="serverless",
        api_key=api_key,
    )


def load_image_from_path(file_path: str | Path) -> dict:
    """
    Load an image from the given path.

    Returns:
        dict: Dictionary mapping filename to image data
            {
                "filename.jpg": {
                    "image": PIL Image object,
                    "path": full path,
                    "base64": base64 encoded string (for API calls)
                }
            }
    """
    supported_formats = {
        ".jpg": "JPEG",
        ".jpeg": "JPEG",
        ".png": "PNG",
    }
    if file_path.suffix not in supported_formats:
        raise ValueError(f"Unsupported image format: {file_path.suffix}")

    img = Image.open(file_path)

    # Convert to base64 for API calls
    buffered = io.BytesIO()
    img.save(buffered, format=img.format)
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return {"image": img, "path": str(file_path), "base64": img_base64}


def pil_to_base64_dict(pil_image):
    """Convert PIL image to the format expected by analyze_damage_image"""
    if pil_image is None:
        return None

    buffered = io.BytesIO()
    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")

    pil_image.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return {"image": pil_image, "path": "uploaded_image.jpg", "base64": img_base64}


def analyze_damage_image(image, api_key: str, prompt: str = "advanced"):
    """
    Analyze the damage in an image using the Fireworks VLM model.
    """
    assert (
        prompt in PROMPT_LIBRARY["vision_damage_analysis"].keys()
    ), f"Invalid prompt choose from {list(PROMPT_LIBRARY['vision_damage_analysis'].keys())}"

    prompt_text = PROMPT_LIBRARY["vision_damage_analysis"][prompt]

    llm = get_llm(
        api_key=api_key,
        model=APP_STEPS_CONFIGS.analyze_damage_image.model,
        temperature=APP_STEPS_CONFIGS.analyze_damage_image.temperature,
    )
    response = llm.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image['base64']}"
                        },
                    },
                    {"type": "text", "text": prompt_text},
                ],
            }
        ],
        response_format={
            "type": "json_object",
            "schema": IncidentAnalysis.model_json_schema(),
        },
    )

    result = json.loads(response.choices[0].message.content)
    return result
