import json
from openai import AsyncOpenAI

from app.services.llm.base import LLMProvider, LLMMessage


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self, api_key: str, model: str = None):
        super().__init__(api_key)
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model or "gpt-4o"

    @property
    def provider_name(self) -> str:
        return "openai"

    async def chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Send messages to OpenAI and get response."""
        chat_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=chat_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content

    async def chat_json(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> dict:
        """Send messages to OpenAI and get JSON response."""
        chat_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=chat_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

        response_text = response.choices[0].message.content

        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {"raw_response": response_text}
