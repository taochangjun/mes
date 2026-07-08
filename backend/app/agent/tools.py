# coding=utf-8
"""阶段 2：Agent 工具定义与执行。"""

import json

# 允许 PyCharm 直接运行本文件（python tools.py）
if __name__ == "__main__" and __package__ is None:
    import os
    import sys
    from pathlib import Path

    _backend_dir = Path(__file__).resolve().parent.parent.parent
    os.chdir(_backend_dir)
    sys.path.insert(0, str(_backend_dir))

try:
    from .service import _load_order, build_order_context, build_orders_summary
except ImportError:
    from app.agent.service import _load_order, build_order_context, build_orders_summary

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_work_order",
            "description": "按工单号查询单条工单详情，含状态、客户、工序进度。用户提供具体工单号时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_no": {
                        "type": "string",
                        "description": "工单号，如 WO-20250706-001",
                    }
                },
                "required": ["order_no"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_work_orders",
            "description": "列出所有工单的摘要。用户问「有哪些工单」「生产中的订单」等没有指定工单号时使用。",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]


def tool_get_work_order(db, order_no: str) -> dict:
    try:
        order = _load_order(db, order_no)
        return {"ok": True, "data": build_order_context(order)}
    except ValueError:
        return {"ok": False, "error": f"工单 {order_no} 不存在"}


def tool_list_work_orders(db) -> dict:
    return {"ok": True, "data": build_orders_summary(db)}


def execute_tool(name: str, arguments: dict, db) -> str:
    if name == "get_work_order":
        result = tool_get_work_order(db, arguments["order_no"])
    elif name == "list_work_orders":
        result = tool_list_work_orders(db)
    else:
        result = {"ok": False, "error": f"未知工具：{name}"}
    return json.dumps(result, ensure_ascii=False, default=str)


if __name__ == "__main__":
    from app.database import Base, SessionLocal, engine
    from app.seed import seed_demo_data

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_demo_data(db)

    print(execute_tool("get_work_order", {"order_no": "WO-20250706-001"}, db))
    print(execute_tool("get_work_order", {"order_no": "WO-99999999-999"}, db))
    print(execute_tool("list_work_orders", {}, db))
    db.close()
