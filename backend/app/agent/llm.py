from functools import lru_cache

from openai import OpenAI

from ..settings import get_settings


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


def chat(messages: list[dict], *, model: str, max_tokens: int = 300):
    """最终回答：不传 tools，限制输出长度。"""
    response = get_llm_client().chat.completions.create(
        model=model,
        messages=messages,
        stream=False,
        max_tokens=max_tokens,
    )
    return response.choices[0].message


def chat_with_tools(messages: list[dict], *, model: str, tools: list[dict]):
    """决策轮：让 LLM 选择是否调用工具。"""
    response = get_llm_client().chat.completions.create(
        model=model,
        messages=messages,
        stream=False,
        tools=tools,
    )
    return response.choices[0].message
