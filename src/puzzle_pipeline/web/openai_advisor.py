"""Optional OpenAI image advisor; credentials stay on the server."""

from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path
from typing import Any

from puzzle_pipeline.ai.schema import ArtworkAnalysis

_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "orientation": {"type": "string", "enum": ["portrait", "landscape", "square"]},
        "crop_mode": {"type": "string", "enum": ["preserve", "cover", "contain"]},
        "recommended_grid": {
            "type": ["object", "null"],
            "properties": {"columns": {"type": "integer"}, "rows": {"type": "integer"}},
            "required": ["columns", "rows"],
            "additionalProperties": False,
        },
        "decorative_border": {"type": "boolean"},
        "notes": {"type": ["string", "null"]},
        "display_name": {"type": ["string", "null"]},
        "artist": {"type": ["string", "null"]},
        "year": {"type": ["string", "null"]},
        "frame_label": {"type": ["string", "null"]},
    },
    "required": [
        "orientation",
        "crop_mode",
        "recommended_grid",
        "decorative_border",
        "notes",
        "display_name",
        "artist",
        "year",
        "frame_label",
    ],
    "additionalProperties": False,
}


class OpenAIArtworkAdvisor:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", client: Any | None = None) -> None:
        if not api_key:
            raise ValueError("OpenAI API key is required")
        if client is None:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
        self._client: Any = client
        self._model = model

    def analyze(self, image: Path) -> ArtworkAnalysis:
        mime = mimetypes.guess_type(image.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(image.read_bytes()).decode("ascii")
        response = self._client.responses.create(
            model=self._model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Analyze this artwork for a Roblox jigsaw puzzle. Recommend a safe grid and "
                                f"The original uploaded filename is {image.name}. Use it as a clue when useful. "
                                "Identify the artwork title, artist, year, frame label, and concise curator notes. "
                                "Preserve the full artwork when possible. Return only the requested JSON schema; "
                                "do not generate geometry. For unknown fields, use JSON null, never the string "
                                "'null'. Do not use 'Untitled' when the filename or image provides a better title."
                            ),
                        },
                        {"type": "input_image", "image_url": f"data:{mime};base64,{encoded}"},
                    ],
                }
            ],
            text={"format": {"type": "json_schema", "name": "artwork_analysis", "strict": True, "schema": _SCHEMA}},
        )
        try:
            return ArtworkAnalysis.model_validate(json.loads(response.output_text))
        except (AttributeError, TypeError, json.JSONDecodeError, ValueError) as exc:
            raise ValueError("invalid artwork analysis from OpenAI provider") from exc
