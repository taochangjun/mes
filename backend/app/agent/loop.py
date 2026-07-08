# coding=utf-8
"""阶段 2：Agent 主循环。"""

import json

from sqlalchemy.orm import Session

# PyCharm 直接运行本文件时，先切到 backend/ 再 import
if __name__ == "__main__" and __package__ is None:
    import os
    import sys
    from pathlib import Path

    _backend_dir = Path(__file__).resolve().parent.parent.parent
    os.chdir(_backend_dir)
    sys.path.insert(0, str(_backend_dir))

try:
    from ..settings import get_settings
    from .llm import chat, chat_with_tools
    from .prompts import AGENT_SYSTEM_PROMPT
    from .tools import TOOLS, execute_tool
except ImportError:
    from app.settings import get_settings
    from app.agent.llm import chat, chat_with_tools
    from app.agent.prompts import AGENT_SYSTEM_PROMPT
    from app.agent.tools import TOOLS, execute_tool

MAX_TURNS = 5


def assistant_message_to_dict(message) -> dict:
    d = {"role": "assistant", "content": message.content or ""}
    if message.tool_calls:
        d["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in message.tool_calls
        ]
    return d


def run_agent(question: str, db: Session) -> tuple[str, list[dict]]:
    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    tool_trace = []
    settings = get_settings()
    model = settings.deepseek_model_flash

    for _ in range(MAX_TURNS):
        # 工具结果已就绪 → 最后一轮不传 tools，加快生成
        if messages[-1].get("role") == "tool":
            message = chat(messages, model=model)
        else:
            message = chat_with_tools(messages, model=model, tools=TOOLS)

        if message.tool_calls:
            messages.append(assistant_message_to_dict(message))

            for call in message.tool_calls:
                args = json.loads(call.function.arguments)
                result = execute_tool(call.function.name, args, db)
                tool_trace.append({"tool": call.function.name, "args": args})
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": result,
                    }
                )
            continue

        return message.content or "", tool_trace

    return "处理超时，请简化问题。", tool_trace


if __name__ == "__main__":
    from app.database import Base, SessionLocal, engine
    from app.seed import seed_demo_data

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_demo_data(db)

    answer, trace = run_agent("WO-20250706-001 进度怎么样？", db)
    print("答案:", answer)
    print("工具链:", trace)
    db.close()
