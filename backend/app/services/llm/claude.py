import json
from anthropic import AsyncAnthropic

from app.services.llm.base import LLMProvider, LLMMessage


class ClaudeProvider(LLMProvider):
    """Claude (Anthropic) LLM provider."""

    def __init__(self, api_key: str, model: str = None):
        super().__init__(api_key)
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model or "claude-sonnet-4-20250514"

    @property
    def provider_name(self) -> str:
        return "claude"

    async def chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Send messages to Claude and get response."""
        # Extract system message if present
        system_message = None
        chat_messages = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                chat_messages.append({"role": msg.role, "content": msg.content})

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": chat_messages,
        }

        if system_message:
            kwargs["system"] = system_message

        response = await self.client.messages.create(**kwargs)
        return response.content[0].text

    async def chat_json(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> dict:
        """Send messages to Claude and get JSON response."""
        # Add instruction to return JSON
        json_instruction = LLMMessage(
            role="user",
            content="Please respond with valid JSON only. No additional text or markdown."
        )
        messages_with_json = list(messages) + [json_instruction]

        response_text = await self.chat(messages_with_json, temperature, max_tokens)

        # Try to parse JSON from response
        try:
            # Handle potential markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            # Return as wrapped text if JSON parsing fails
            return {"raw_response": response_text}
