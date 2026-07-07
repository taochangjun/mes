import json
import os
from pathlib import Path
from typing import Iterator

from .prompts import DEFAULT_MES_SYSTEM_PROMPT, MES_SYSTEM_PROMPT
from dotenv import load_dotenv
from openai import OpenAI


def load_config() -> dict[str, str]:
    root_dir = Path(__file__).resolve().parent.parent.parent
    load_dotenv(root_dir / "config" / ".env")

    config = {
        "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
        "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        "model_pro": os.getenv("DEEPSEEK_MODEL_PRO", "deepseek-v4-pro"),
        "model_flash": os.getenv("DEEPSEEK_MODEL_FLASH", "deepseek-v4-flash"),
    }
    if not config["api_key"]:
        raise SystemExit(
            "缺少 DEEPSEEK_API_KEY。请复制 backend/config/.env.example 为 .env 并填入 Key。"
        )
    return config


def create_client(config: dict[str, str]) -> OpenAI:
    return OpenAI(api_key=config["api_key"], base_url=config["base_url"])


def chat(client: OpenAI,  model: str, question: str, order_list:list, stream: bool, thinking: bool) ->str | Iterator[str | None]:
    print("question:", question)
    if order_list:
        order_str = json.dumps(order_list, ensure_ascii=False, default=str)
        system_prompt = MES_SYSTEM_PROMPT.replace("{OrderList}", order_str)
    else:
        system_prompt = DEFAULT_MES_SYSTEM_PROMPT

    kwargs: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "stream": stream,
    }
    if thinking:
        kwargs["reasoning_effort"] = "high"
        kwargs["extra_body"] = {"thinking": {"type": "enabled"}}

    print("kwargs:", kwargs)
    # if stream:
    #     response = client.chat.completions.create(**kwargs)
    #     for chunk in response:
    #         yield chunk.choices[0].delta.content
    #     return None

    response = client.chat.completions.create(**kwargs)
    usage = response.usage
    if usage:
        print(
            f"\n--- token 用量: prompt={usage.prompt_tokens}, "
            f"completion={usage.completion_tokens}, total={usage.total_tokens} ---"
        )
    print("Output:", response.choices[0].message.content)
    return response.choices[0].message.content


config = load_config()
llm_client = create_client(config)
print(config)

if __name__ == '__main__':
    print(llm_client, config["model_pro"])
    chat(llm_client, config["model_pro"], "请用中文回答：1+1是多少？", [], False, True)