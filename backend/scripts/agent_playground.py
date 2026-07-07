"""阶段 0：LLM 调用实验脚本。

用法：
  python scripts/agent_playground.py
  python scripts/agent_playground.py "为什么要有 system prompt？"
  python scripts/agent_playground.py --stream "MES 里工单下达和物料配送是什么关系？"
  python scripts/agent_playground.py --model flash "简要说明 MES 是什么"
"""

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

MES_SYSTEM_PROMPT = """你是三一重工 SanyMES 制造执行系统的技术顾问。
你熟悉工单管理、工位任务、物料配送、质检等业务流程。
用简洁的中文回答，必要时分点说明。"""

DEFAULT_QUESTION = "MES 里工单下达和物料配送是什么关系？"


def load_config() -> dict[str, str]:
    root_dir = Path(__file__).resolve().parent.parent
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


def chat(client: OpenAI, model: str, question: str, stream: bool, thinking: bool) -> None:
    kwargs: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": MES_SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        "stream": stream,
    }
    if thinking:
        kwargs["reasoning_effort"] = "high"
        kwargs["extra_body"] = {"thinking": {"type": "enabled"}}

    if stream:
        response = client.chat.completions.create(**kwargs)
        print("回答：", end="", flush=True)
        for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                print(delta, end="", flush=True)
        print()
        return

    response = client.chat.completions.create(**kwargs)
    print(response.choices[0].message.content)

    usage = response.usage
    if usage:
        print(
            f"\n--- token 用量: prompt={usage.prompt_tokens}, "
            f"completion={usage.completion_tokens}, total={usage.total_tokens} ---"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="MES Agent 阶段 0：LLM 调用实验")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION, help="要问 LLM 的问题")
    parser.add_argument("--stream", action="store_true", help="流式输出")
    parser.add_argument(
        "--model",
        choices=["pro", "flash"],
        default="pro",
        help="模型档位（默认 pro）",
    )
    parser.add_argument(
        "--thinking",
        action="store_true",
        help="开启 DeepSeek thinking 模式（更慢，适合复杂推理）",
    )
    args = parser.parse_args()

    config = load_config()
    model = config["model_pro"] if args.model == "pro" else config["model_flash"]
    client = create_client(config)

    print(f"问题：{args.question}\n")
    chat(client, model, args.question, args.stream, args.thinking)


if __name__ == "__main__":
    main()
