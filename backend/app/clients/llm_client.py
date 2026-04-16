import json
from typing import Any

from openai import OpenAI


class LLMClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate_dataset_interpretation(self, prompt_payload: dict[str, Any]) -> dict[str, Any]:
        system_prompt = (
            "You are a data quality analyst. Return valid JSON only with keys: "
            "dataset_representation, likely_ml_problem, key_concerns, recommended_next_steps. "
            "Ground claims in provided computed statistics and avoid generic advice."
        )

        user_prompt = json.dumps(prompt_payload, ensure_ascii=True)
        response = self._client.chat.completions.create(
            model=self._model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise RuntimeError("OpenAI returned an empty response.")

        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise RuntimeError("OpenAI response JSON was not an object.")

        return parsed
