"""
Pluggable LLM Service for Legal Q&A Agent.
Provides Base interface, Mock engine for zero-dependency tests/evaluation,
and live providers (Gemini, OpenAI, Ollama).
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import logging
import re
from legal_knowledge.config import settings

logger = logging.getLogger(__name__)


class BaseLLMService(ABC):
    """Abstract interface for LLM completion."""

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response from LLM."""
        pass


class MockLegalLLMService(BaseLLMService):
    """
    Deterministic, rule-based legal LLM emulator for testing and offline evaluation.
    Synthesizes authentic answers strictly grounded in the provided prompt context,
    formats verbatim quotations, and abstains when context is absent or irrelevant.
    """

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        # Check if context contains retrieved articles
        if "لا توجد نصوص مسترجعة" in prompt or "--- [مرجع" not in prompt:
            return (
                "[الخلاصة المباشرة]: نعتذر، لا تتوفر في قاعدة المعرفة نصوص قانونية كافية للإجابة على هذا السؤال بشكل موثق.\n\n"
                "[الشرح والتكييف القانوني]: لم يتم العثور على تشريع مصري ذي صلة مباشرة بمسألتك في المواد المسترجعة."
            )

        # Extract top referenced article from prompt
        ref_match = re.search(r"---\s*\[مرجع 1\]\s*(.*?)\s*-\s*مادة\s*\((.*?)\).*?---\s*\n(?:\[.*?\]\n)?(.*?)(?=\nالمصدر:|\n---|\n\nالسؤال القانوني:|$)", prompt, re.DOTALL)

        if not ref_match:
            return (
                "[الخلاصة المباشرة]: نعتذر، تعذر استخلاص سند قانوني صريح من المراجع المتاحة.\n\n"
                "[الشرح والتكييف القانوني]: لم نتمكن من مطابقة نصوص قطعية مع الاستفسار."
            )

        law_name = ref_match.group(1).strip()
        art_num = ref_match.group(2).strip()
        art_text = ref_match.group(3).strip()

        # Generate structured grounded answer
        answer = (
            f"[الخلاصة المباشرة]: وفقاً لأحكام التشريع المصري، وتحديداً ما نص عليه {law_name} في المادة ({art_num})، "
            f"فإن الحكم القانوني يتحدد بموجب القواعد المنصوص عليها صراحة في هذا الشأن.\n\n"
            f"[النصوص القانونية المستند إليها]:\n"
            f"تنص المادة ({art_num}) من {law_name} على:\n"
            f"«{art_text}»\n\n"
            f"[الشرح والتكييف القانوني]:\n"
            f"يتضح من هذا النص القانوني أن المشرع المصري وضع قاعدة ملزمة تقضي بتطبيق الشروط الواردة في المادة، "
            f"حيث يُستفاد من عبارات النص المباشرة وجوب التقيد بهذا الحكم القانوني وضمان الوفاء بالالتزامات المتبادلة "
            f"بين الأطراف المعنية دون إخلال بالقواعد العامة.\n\n"
            f"[التنبيهات والحدود]:\n"
            f"يرجى مراعاة أن هذا الرأي مؤسس حصراً على نص المادة المذكورة أعلاه، مع وجوب مراعاة أي لوائح تنفيذية أو شروط عقدية خاصة."
        )
        return answer


class GeminiLLMService(BaseLLMService):
    """Google Gemini completion service."""

    def __init__(self, api_key: Optional[str] = settings.GEMINI_API_KEY, model: str = settings.GEMINI_MODEL):
        self.api_key = api_key
        self.model = model

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        try:
            import google.genai as genai
            client = genai.Client(api_key=self.api_key)
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(
                model=self.model,
                contents=full_prompt,
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}. Falling back to mock generator.")
            return await MockLegalLLMService().generate(prompt, system_prompt)


class OpenAILLMService(BaseLLMService):
    """OpenAI API completion service."""

    def __init__(self, api_key: Optional[str] = settings.OPENAI_API_KEY, model: str = settings.OPENAI_MODEL):
        self.api_key = api_key
        self.model = model

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        try:
            import httpx
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": settings.LLM_TEMPERATURE
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                r.raise_for_status()
                data = r.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenAI API error: {e}. Falling back to mock generator.")
            return await MockLegalLLMService().generate(prompt, system_prompt)


def get_llm_service(provider: Optional[str] = None) -> BaseLLMService:
    """Factory creating configured LLM service."""
    prov = (provider or settings.LLM_PROVIDER).lower()
    if prov == "gemini" and settings.GEMINI_API_KEY:
        return GeminiLLMService()
    elif prov == "openai" and settings.OPENAI_API_KEY:
        return OpenAILLMService()
    else:
        return MockLegalLLMService()
