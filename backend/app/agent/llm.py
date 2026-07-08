from functools import lru_cache

from settings import get_settings
from openai import OpenAI


@lru_cache()
def get_llm_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)


def complete(messages: list[dict], *, model: str, thinking: bool = False) -> str:
    # thinking=False 作为默认（查工单状态不需要 reasoning）
    kwargs = {
        'model': model,
        'messages': messages,
        'stream': False,
    }
    if thinking:
        kwargs['reasoning_effort'] = "high"
        kwargs["extra_body"] = {"thinking": {"type": "enabled"}}

    response = get_llm_client().chat.completions.create(**kwargs)
    return response.choices[0].message.content
