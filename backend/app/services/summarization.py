from __future__ import annotations

import json

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.errors import user_error

SUMMARY_PROMPT = """You are a structured research assistant.
Return JSON with the following keys:
- summary: string
- key_points: string[]
- timeline: array of {time: string, label: string, description: string}
- title_suggestion: string
- tags: string[]
Keep the output concise and factual."""


class SummarizationService:
    def summarize(self, transcript_text: str, segments: list[dict]) -> dict:
        settings = get_settings()
        if not settings.openai_api_key:
            raise user_error(status.HTTP_503_SERVICE_UNAVAILABLE, "DeepSeek API Key 未配置，请先在环境变量中设置。")

        snippet = transcript_text[:20000]
        segment_hint = json.dumps(segments[:20], ensure_ascii=False)
        headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
        payload = {
            "model": settings.openai_model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SUMMARY_PROMPT},
                {
                    "role": "user",
                    "content": f"Transcript:\n{snippet}\n\nSegments:\n{segment_hint}",
                },
            ],
        }
        response = httpx.post(
            f"{settings.openai_base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
            timeout=180,
        )
        if response.status_code >= 400:
            raise user_error(status.HTTP_502_BAD_GATEWAY, "摘要生成失败，请稍后重试或检查 DeepSeek 配置。")
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return {
            "summary": parsed.get("summary", ""),
            "key_points": parsed.get("key_points", []),
            "timeline": parsed.get("timeline", []),
            "title_suggestion": parsed.get("title_suggestion"),
            "tags": parsed.get("tags", []),
        }
