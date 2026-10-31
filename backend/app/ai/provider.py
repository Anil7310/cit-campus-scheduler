import os
import json
import logging
import httpx
from typing import Dict, Any, Optional
from app.config import settings
from app.ai.safety import sanitize_user_input, enforce_server_authority
from app.ai.parser_fallback import parse_booking_intent_fallback, parse_schedule_intent_fallback

logger = logging.getLogger("cit_scheduler.ai")

class LLMProvider:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL
        self.prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")

    def _load_prompt(self, filename: str) -> str:
        path = os.path.join(self.prompts_dir, filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    async def parse_booking_request(self, user_message: str, user_role: str = "club") -> Dict[str, Any]:
        # If LLM disabled or key missing, use fallback parser immediately
        if self.provider == "none" or not self.api_key:
            parsed = parse_booking_intent_fallback(user_message)
            return enforce_server_authority(parsed, user_role)

        sanitized_msg = sanitize_user_input(user_message)
        system_prompt = self._load_prompt("booking_parser.txt")

        try:
            raw_response = await self._call_llm_api(system_prompt, sanitized_msg)
            json_text = self._extract_json_block(raw_response)
            parsed = json.loads(json_text)
            parsed["llm_used"] = True
            parsed["parser"] = self.provider
            return enforce_server_authority(parsed, user_role)
        except Exception as e:
            logger.warning(f"LLM API call failed ({e}); switching to fallback parser.")
            parsed = parse_booking_intent_fallback(user_message)
            return enforce_server_authority(parsed, user_role)

    async def parse_schedule_request(self, user_message: str, faculty_id: str, user_role: str = "faculty") -> Dict[str, Any]:
        if self.provider == "none" or not self.api_key:
            parsed = parse_schedule_intent_fallback(user_message, faculty_id)
            return enforce_server_authority(parsed, user_role, faculty_id)

        sanitized_msg = sanitize_user_input(user_message)
        system_prompt = self._load_prompt("reschedule_parser.txt")

        try:
            raw_response = await self._call_llm_api(system_prompt, sanitized_msg)
            json_text = self._extract_json_block(raw_response)
            parsed = json.loads(json_text)
            parsed["faculty_id"] = faculty_id
            parsed["llm_used"] = True
            parsed["parser"] = self.provider
            return enforce_server_authority(parsed, user_role, faculty_id)
        except Exception as e:
            logger.warning(f"LLM API call failed ({e}); switching to fallback parser.")
            parsed = parse_schedule_intent_fallback(user_message, faculty_id)
            return enforce_server_authority(parsed, user_role, faculty_id)

    async def _call_llm_api(self, system_prompt: str, user_prompt: str) -> str:
        timeout = 20.0
        async with httpx.AsyncClient(timeout=timeout) as client:
            if self.provider == "gemini":
                # Google Gemini API
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
                payload = {
                    "contents": [
                        {"role": "user", "parts": [{"text": f"{system_prompt}\n\nUser Request: {user_prompt}"}]}
                    ],
                    "generationConfig": {"temperature": 0.1, "response_mime_type": "application/json"}
                }
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]

            elif self.provider == "openai":
                url = "https://api.openai.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {self.api_key}"}
                payload = {
                    "model": self.model or "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1
                }
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]

            elif self.provider == "anthropic":
                url = "https://api.anthropic.com/v1/messages"
                headers = {
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01"
                }
                payload = {
                    "model": self.model or "claude-3-haiku-20240307",
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_prompt}],
                    "temperature": 0.1,
                    "max_tokens": 1000
                }
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["content"][0]["text"]
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _extract_json_block(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

llm_provider = LLMProvider()
