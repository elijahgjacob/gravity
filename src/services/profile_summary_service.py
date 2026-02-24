"""Service for generating LLM-powered user profile summaries and ad campaign suggestions."""

import json
import re
from typing import Any, Dict, List, Optional

from src.api.models.profiles import UserProfile
from src.core.logging_config import get_logger

logger = get_logger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class ProfileSummaryService:
    """
    Generates a narrative summary and suggested ad campaigns for a user profile
    using an LLM via OpenRouter.
    """

    def __init__(self, api_key: str, model: str, verify_ssl: bool = True):
        """
        Initialize the profile summary service.

        Args:
            api_key: OpenRouter API key
            model: Model identifier (e.g. openai/gpt-3.5-turbo, anthropic/claude-3.5-sonnet)
            verify_ssl: If False, disable SSL verification (use only for local cert issues).
        """
        self.api_key = api_key
        self.model = model
        self.verify_ssl = verify_ssl

    def _build_prompt(self, profile: UserProfile) -> str:
        """Build the LLM prompt from profile data."""
        # Serialize for prompt (compact)
        queries = [item.query for item in profile.query_history]
        intents_data = []
        for intent in profile.get_active_intents():
            intents_data.append({
                "intent_type": intent.intent_type,
                "confidence": intent.confidence,
                "evidence": intent.evidence,
                "inferred_categories": intent.inferred_categories,
                "metadata": intent.metadata,
            })
        prompt_data = {
            "recent_queries": queries[-20:],  # last 20
            "inferred_intents": intents_data,
            "inferred_categories": profile.inferred_categories,
            "aggregated_interests": profile.aggregated_interests,
        }
        profile_text = json.dumps(prompt_data, indent=2)

        return f"""You are an ad campaign strategist. From the user profile below (queries + inferred intents), produce:
1. A short narrative (2-4 sentences) on what we know and their likely goals or next steps (e.g. preparing for Boston Marathon, searching running gear and Boston weather).
2. 3-6 specific, actionable ad campaign suggestions. Derive from intent_type, inferred_categories, and metadata (e.g. location): e.g. marathon_planning + Boston → "Flights to Boston", "Car rental Boston", "Running/race gear".

User profile data:
{profile_text}

Respond with a single JSON object only, no markdown or extra text:
{{"narrative_summary": "<2-4 sentences>", "suggested_campaigns": ["<suggestion 1>", "<suggestion 2>", ...]}}
"""

    def _parse_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse LLM response into narrative_summary and suggested_campaigns."""
        if not content or not content.strip():
            return None
        text = content.strip()
        # Remove markdown code block if present
        if "```json" in text:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
            if match:
                text = match.group(1).strip()
        elif "```" in text:
            match = re.search(r"```\s*([\s\S]*?)```", text)
            if match:
                text = match.group(1).strip()
        try:
            data = json.loads(text)
            narrative = data.get("narrative_summary")
            campaigns = data.get("suggested_campaigns")
            if isinstance(narrative, str) and isinstance(campaigns, list):
                return {"narrative_summary": narrative, "suggested_campaigns": campaigns}
            return None
        except json.JSONDecodeError:
            logger.warning("Profile summary LLM response was not valid JSON: %s", text[:200])
            return None

    async def generate_summary(self, profile: UserProfile) -> Optional[Dict[str, Any]]:
        """
        Generate narrative summary and suggested campaigns for a user profile.

        Args:
            profile: UserProfile with query_history, inferred_intents, etc.

        Returns:
            Dict with "narrative_summary" and "suggested_campaigns", or None on failure.
        """
        try:
            import httpx
        except ImportError:
            logger.error("httpx not installed; cannot call OpenRouter for profile summary")
            return None

        prompt = self._build_prompt(profile)
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 600,
            "temperature": 0.3,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0, verify=self.verify_ssl) as client:
                response = await client.post(OPENROUTER_URL, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                choices = data.get("choices")
                if not choices or not choices[0].get("message", {}).get("content"):
                    logger.warning("OpenRouter response had no content")
                    return None
                content = choices[0]["message"]["content"]
                return self._parse_response(content)
        except httpx.HTTPStatusError as e:
            logger.error("OpenRouter API error: %s %s", e.response.status_code, e.response.text[:200])
            return None
        except Exception as e:
            logger.error("Profile summary generation failed: %s", e, exc_info=True)
            return None
