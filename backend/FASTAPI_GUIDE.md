# SanyMES Backend — FastAPI 知识点详解

> 面向熟悉 Python、初学 FastAPI 的开发者。本文档以本项目的真实代码为例，系统讲解 backend 中用到的所有 FastAPI 相关知识点。

---

## 目录

1. [项目总览](#1-项目总览)
2. [如何启动与访问 API 文档](#2-如何启动与访问-api-文档)
3. [FastAPI 应用实例](#3-fastapi-应用实例)
4. [路由与 HTTP 方法](#4-路由与-http-方法)
5. [路径参数与查询参数](#5-路径参数与查询参数)
6. [请求体与 Pydantic 模型](#6-请求体与-pydantic-模型)
7. [响应模型 response_model](#7-响应模型-response_model)
8. [依赖注入 Depends](#8-依赖注入-depends)
9. [异常处理 HTTPException](#9-异常处理-httpexception)
10. [CORS 跨域中间件](#10-cors-跨域中间件)
11. [启动事件 on_event](#11-启动事件-on_event)
12. [Pydantic 进阶：枚举、校验、ORM 转换](#12-pydantic-进阶枚举校验orm-转换)
13. [项目架构分层](#13-项目架构分层)
14. [完整 API 端点速查](#14-完整-api-端点速查)
15. [一次请求的完整生命周期](#15-一次请求的完整生命周期)
16. [本项目未使用但值得了解的 FastAPI 特性](#16-本项目未使用但值得了解的-fastapi-特性)
17. [学习建议与动手练习](#17-学习建议与动手练习)

---

## 1. 项目总览

### 1.1 目录结构

```
backend/
├── run.py              # 启动入口（Uvicorn ASGI 服务器）
├── requirements.txt    # 依赖
├── sanymes.db          # SQLite 数据库（运行后自动生成）
└── app/
    ├── main.py         # ★ FastAPI 应用 + 所有路由
    ├── schemas.py      # ★ Pydantic 数据模型（请求/响应）
    ├── database.py     # 数据库连接 + get_db 依赖
    ├── models.py       # SQLAlchemy ORM 模型（非 FastAPI，但紧密配合）
    ├── services.py     # 业务逻辑层
    └── seed.py         # 演示数据初始化
```

### 1.2 技术栈关系

```
浏览器 / 前端 (Vue)
        ↓ HTTP JSON
   Uvicorn (ASGI 服务器)
        ↓
   FastAPI (路由、校验、序列化)
        ↓
   SQLAlchemy (数据库 ORM)
        ↓
   SQLite (sanymes.db)
```

**关键理解**：FastAPI 本身不操作数据库。它负责接收 HTTP 请求、校验数据、调用业务逻辑、把结果序列化成 JSON 返回。数据库访问通过 `Depends(get_db)` 注入的 SQLAlchemy Session 完成。

### 1.3 核心依赖

| 包 | 版本 | 作用 |
|---|---|---|
| `fastapi` | 0.115.6 | Web 框架 |
| `uvicorn` | 0.34.0 | ASGI 服务器，运行 FastAPI |
| `pydantic` | 2.10.3 | 数据校验与序列化（FastAPI 内置使用） |
| `sqlalchemy` | 2.0.36 | ORM，配合依赖注入使用 |
| `python-multipart` | 0.0.20 | 表单/文件上传支持（本项目暂未用到） |

---

## 2. 如何启动与访问 API 文档

### 2.1 启动方式

`run.py` 是项目入口：

```python
#!/usr/bin/env python3
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

**知识点解析**：

| 参数 | 含义 |
|---|---|
| `"app.main:app"` | 模块路径字符串。表示加载 `app/main.py` 中的变量 `app` |
| `host="0.0.0.0"` | 监听所有网卡，局域网可访问 |
| `port=8000` | 端口 |
| `reload=True` | 开发模式热重载，改代码自动重启 |

**ASGI 是什么？**  
FastAPI 基于 Starlette，是一个 **ASGI**（异步服务器网关接口）应用。Uvicorn 是 ASGI 服务器，负责把 HTTP 请求交给 FastAPI 处理。开发时你写 `python run.py`，生产环境通常用 `uvicorn app.main:app --host 0.0.0.0 --port 8000`。

### 2.2 自动生成的 API 文档

启动后访问：

- **Swagger UI**：http://localhost:8000/docs
- **ReDoc**：http://localhost:8000/redoc
- **OpenAPI JSON**：http://localhost:8000/openapi.json

这是 FastAPI 的杀手级特性之一：**根据你的类型注解和 Pydantic 模型，自动生成可交互的 API 文档**，无需手写 Swagger。

---

## 3. FastAPI 应用实例

`main.py` 第 41 行：

```python
app = FastAPI(
    title="SanyMES Demo",
    description="三一重工 MES 简化版演示系统",
    version="0.1.0",
)
```

### 3.1 这是什么？

`app` 是整个 Web 应用的**核心对象**，所有路由、中间件、事件都挂载在它上面。

### 3.2 常用构造参数

| 参数 | 本项目 | 作用 |
|---|---|---|
| `title` | `"SanyMES Demo"` | 显示在 `/docs` 页面标题 |
| `description` | 中文描述 | API 文档说明 |
| `version` | `"0.1.0"` | API 版本号 |

其他常见参数（本项目未用）：`docs_url`、`redoc_url`、`openapi_url`（可自定义文档路径）、`lifespan`（替代 `on_event` 的新写法）。

### 3.3 导入来源

```python
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
```

- `FastAPI`：应用类
- `Depends`：依赖注入
- `HTTPException`：主动抛出 HTTP 错误
- `CORSMiddleware`：跨域中间件

---

## 4. 路由与 HTTP 方法

路由 = **URL 路径** + **HTTP 方法** + **处理函数**。

### 4.1 装饰器语法

```python
@app.get("/api/health")
def health():
    return {"status": "ok", "system": "SanyMES Demo"}
```

等价于：

> 当收到 `GET /api/health` 请求时，调用 `health()` 函数，把返回值序列化为 JSON。

### 4.2 本项目用到的 HTTP 方法

| 装饰器 | 语义 | 本项目用途 |
|---|---|---|
| `@app.get(...)` | 查询/读取 | 列表、详情、统计 |
| `@app.post(...)` | 创建/动作 | 创建工单、下达、开工、报完工 |

本项目**没有**使用 `PUT`、`PATCH`、`DELETE`。RESTful 风格中：
- `GET` = 读
- `POST` = 写/触发动作
- `PUT/PATCH` = 更新
- `DELETE` = 删除

### 4.3 路由命名约定

本项目所有 API 以 `/api/` 为前缀，例如：

```
/api/health
/api/dashboard
/api/products
/api/work-orders
/api/work-orders/{order_id}/release
```

`{order_id}` 是**路径参数**（下一节详述）。

### 4.4 函数即路由处理程序（Path Operation Function）

```python
@app.get("/api/products", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()
```

函数名（`list_products`）**不影响** URL，只用于代码可读性。真正决定路由的是装饰器里的路径和方法。

---

## 5. 路径参数与查询参数

FastAPI 通过**函数参数的类型注解**自动识别参数来源。

### 5.1 路径参数 Path Parameters

路径中用 `{name}` 声明，函数参数同名 + 类型注解：

```python
@app.get("/api/work-orders/{order_id}", response_model=WorkOrderOut)
def get_work_order(order_id: int, db: Session = Depends(get_db)):
    ...
```

请求 `GET /api/work-orders/3` → `order_id = 3`（自动转为 `int`）。

**FastAPI 自动完成**：
1. 从 URL 提取 `order_id`
2. 校验是否为合法整数
3. 校验失败返回 `422 Unprocessable Entity`，并附带详细错误信息

本项目中的路径参数：

| 参数 | 出现位置 | 类型 |
|---|---|---|
| `product_id` | `/api/products/{product_id}/bom` | `int` |
| `order_id` | `/api/work-orders/{order_id}` 等 | `int` |
| `task_id` | `/api/station-tasks/{task_id}/start` 等 | `int` |

### 5.2 查询参数 Query Parameters

函数参数**不在路径中出现**，自动视为 URL 查询字符串：

```python
@app.get("/api/station-tasks", response_model=list[StationTaskOut])
def list_station_tasks(station_id: int | None = None, db: Session = Depends(get_db)):
    ...
```

| 请求 URL | `station_id` 值 |
|---|---|
| `/api/station-tasks` | `None`（可选，不过滤） |
| `/api/station-tasks?station_id=4` | `4` |

另一个例子：

```python
def list_quality_records(work_order_id: int | None = None, db: Session = Depends(get_db)):
```

前端调用（见 `frontend/src/api.js`）：

```javascript
api.get('/quality-records', { params: { work_order_id: workOrderId } })
```

→ 实际请求 `GET /api/quality-records?work_order_id=1`

### 5.3 路径参数 vs 查询参数 — 判断规则

```
@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    # item_id → 路径参数（因为在 {} 里）
    # q         → 查询参数（不在路径中）
```

### 5.4 显式声明（本项目未用，但应了解）

需要更多控制时可用 `Path()` 和 `Query()`：

```python
from fastapi import Path, Query

def foo(
    item_id: int = Path(ge=1, description="商品 ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=100),
):
    ...
```

---

## 6. 请求体与 Pydantic 模型

`POST` 请求通常带 JSON 请求体。FastAPI 用 **Pydantic 模型**自动解析和校验。

### 6.1 基本用法

```python
@app.post("/api/work-orders", response_model=WorkOrderOut)
def create_order(data: WorkOrderCreate, db: Session = Depends(get_db)):
    ...
```

当参数类型是 Pydantic `BaseModel` 子类时，FastAPI 自动：
1. 读取请求体 JSON
2. 反序列化为 `WorkOrderCreate` 实例
3. 执行字段校验
4. 校验失败返回 422 + 错误详情

### 6.2 请求体模型一览

**`WorkOrderCreate`** — 创建工单：

```python
class WorkOrderCreate(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)
    customer: str | None = None
    priority: int = Field(default=5, ge=1, le=10)
```

对应 JSON：

```json
{
  "product_id": 1,
  "quantity": 2,
  "customer": "中建三局",
  "priority": 3
}
```

**`TaskStartRequest`** — 开工：

```python
class TaskStartRequest(BaseModel):
    operator: str
```

**`TaskCompleteRequest`** — 报完工：

```python
class TaskCompleteRequest(BaseModel):
    operator: str
    report_note: str | None = None
```

**`QualityRecordCreate`** — 创建质检记录：

```python
class QualityRecordCreate(BaseModel):
    work_order_id: int
    station_id: int
    inspector: str
    check_item: str
    standard: str
    result: QualityResult
    remark: str | None = None
```

### 6.3 model_dump() — 模型转字典

`create_quality_record` 路由中：

```python
record = QualityRecord(**data.model_dump())
```

`model_dump()` 是 Pydantic v2 的方法（v1 叫 `.dict()`），把模型转成普通 Python 字典，方便传给 SQLAlchemy 构造函数。

---

## 7. 响应模型 response_model

### 7.1 作用

```python
@app.get("/api/dashboard", response_model=DashboardStats)
def dashboard(db: Session = Depends(get_db)):
    return get_dashboard_stats(db)
```

`response_model` 告诉 FastAPI：

1. **序列化**：按 `DashboardStats` 的字段过滤/转换返回值
2. **文档**：在 `/docs` 中展示响应结构
3. **校验**：确保返回数据符合模型（开发时很有用）

### 7.2 返回 ORM 对象 + from_attributes

很多路由直接返回 SQLAlchemy 查询结果：

```python
@app.get("/api/products", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()  # 返回 Product ORM 对象列表
```

Pydantic 模型配置了：

```python
class ProductOut(BaseModel):
    id: int
    code: str
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}
```

`from_attributes: True`（Pydantic v2，v1 叫 `orm_mode = True`）允许从**对象属性**（如 SQLAlchemy 模型实例）读取数据，而不只是字典。

**数据流**：

```
SQLAlchemy Product 对象
        ↓ from_attributes
Pydantic ProductOut 模型
        ↓ FastAPI 序列化
JSON {"id": 1, "code": "SY-5288THB", ...}
```

### 7.3 嵌套响应模型

工单响应包含嵌套结构：

```python
class WorkOrderOut(BaseModel):
    id: int
    order_no: str
    product: ProductOut          # 嵌套产品
    station_tasks: list[StationTaskOut] = []  # 嵌套任务列表
    ...
```

这要求查询时**预加载关联数据**（否则嵌套字段可能为空或触发懒加载错误）：

```python
db.query(WorkOrder)
  .options(
      joinedload(WorkOrder.product),
      joinedload(WorkOrder.station_tasks).joinedload(StationTask.station),
  )
```

### 7.4 列表类型注解

```python
response_model=list[ProductOut]
response_model=list[MaterialIssueOut]
```

Python 3.9+ / 3.10+ 可直接写 `list[X]`。旧版本写 `List[X]`（从 `typing` 导入）。

### 7.5 不声明 response_model 的情况

```python
@app.get("/api/health")
def health():
    return {"status": "ok", "system": "SanyMES Demo"}
```

返回普通 `dict`，FastAPI 直接 `json.dumps`。适合简单响应，但缺少文档类型信息和输出过滤。

---

## 8. 依赖注入 Depends

依赖注入（Dependency Injection）是 FastAPI **最核心的设计模式**。

### 8.1 基本语法

```python
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()
```

`Depends(get_db)` 表示：在调用 `list_products` 之前，先调用 `get_db()`，把结果赋给 `db`。

### 8.2 get_db 的实现

`database.py`：

```python
def get_db():
    db = SessionLocal()
    try:
        yield db       # ← 提供给路由函数使用
    finally:
        db.close()     # ← 请求结束后关闭连接
```

这是一个**生成器依赖**：
- `yield` 之前：创建资源（数据库 Session）
- `yield`：把资源交给路由
- `yield` 之后（finally）：清理资源（关闭 Session）

**每个 HTTP 请求**都会获得一个独立的 Session，请求结束自动关闭，避免连接泄漏。

### 8.3 为什么用依赖注入？

| 好处 | 说明 |
|---|---|
| 复用 | 20+ 个路由都写 `db: Session = Depends(get_db)`，不用重复创建/关闭 |
| 可测试 | 测试时可替换 `get_db` 为 mock 数据库 |
| 解耦 | 路由函数不关心 Session 怎么创建 |
| 可组合 | 依赖可以依赖其他依赖（链式注入） |

### 8.4 依赖的其他常见用途（本项目未用）

```python
# 当前登录用户
def get_current_user(token: str = Depends(oauth2_scheme)) -> User: ...

# 分页参数
def pagination(skip: int = 0, limit: int = 20): ...

# 权限检查
def require_admin(user: User = Depends(get_current_user)): ...
```

---

## 9. 异常处理 HTTPException

### 9.1 主动抛出 HTTP 错误

```python
from fastapi import HTTPException

if not order:
    raise HTTPException(status_code=404, detail="工单不存在")
```

FastAPI 会把它转成标准 HTTP 响应：

```json
HTTP 404
{"detail": "工单不存在"}
```

### 9.2 本项目的错误处理模式

业务逻辑层（`services.py`）抛 Python 的 `ValueError`：

```python
def release_work_order(db, order_id):
    if order.status != WorkOrderStatus.PENDING:
        raise ValueError("只有待下达状态的工单可以下达")
```

路由层捕获并转为 HTTP 响应：

```python
@app.post("/api/work-orders/{order_id}/release", response_model=WorkOrderOut)
def release_order(order_id: int, db: Session = Depends(get_db)):
    try:
        release_work_order(db, order_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return get_work_order(order_id, db)
```

**分层职责**：

```
services.py  → 业务规则，抛 ValueError（与 HTTP 无关）
main.py      → HTTP 层，把 ValueError 映射为 400/404 等状态码
```

### 9.3 常见状态码

| 状态码 | 本项目场景 | 含义 |
|---|---|---|
| `200` | 成功（GET/POST 默认） | OK |
| `400` | 业务规则违反（状态不对、产品不存在） | Bad Request |
| `404` | 工单不存在 | Not Found |
| `422` | 请求体/参数校验失败 | FastAPI/Pydantic 自动返回 |

### 9.4 422 校验错误（自动）

如果你 POST 一个 `quantity: 0` 的工单：

```json
{"product_id": 1, "quantity": 0}
```

`WorkOrderCreate` 中 `quantity: int = Field(ge=1)` 会失败，FastAPI 自动返回：

```json
{
  "detail": [
    {
      "type": "greater_than_equal",
      "loc": ["body", "quantity"],
      "msg": "Input should be greater than or equal to 1",
      "input": 0
    }
  ]
}
```

你不需要手写这段逻辑——这是 FastAPI + Pydantic 的核心价值。

---

## 10. CORS 跨域中间件

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 10.1 为什么需要 CORS？

浏览器有**同源策略**：前端 `http://localhost:5173` 请求后端 `http://localhost:8000` 属于跨域。没有 CORS 头，浏览器会拦截响应。

### 10.2 参数说明

| 参数 | 本项目值 | 含义 |
|---|---|---|
| `allow_origins` | `["*"]` | 允许任何来源（开发环境常用） |
| `allow_credentials` | `True` | 允许携带 Cookie |
| `allow_methods` | `["*"]` | 允许所有 HTTP 方法 |
| `allow_headers` | `["*"]` | 允许所有请求头 |

> 生产环境应把 `allow_origins` 改为具体前端域名，如 `["https://mes.example.com"]`。

### 10.3 中间件执行顺序

中间件在路由**之前/之后**包裹请求，像洋葱模型：

```
请求 → CORS 中间件 → 路由处理 → CORS 中间件 → 响应
```

---

## 11. 启动事件 on_event

```python
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    seed_demo_data(db)
```

### 11.1 作用

应用启动时执行一次：
1. `create_all` — 根据 SQLAlchemy 模型创建数据库表
2. `seed_demo_data` — 插入演示数据（若已有数据则跳过）

### 11.2 注意点

- `next(get_db())` 手动取生成器的第一个值，这里可用是因为 `seed_demo_data` 在启动阶段运行，不会与请求生命周期冲突
- 还有 `@app.on_event("shutdown")` 用于关闭连接池等清理工作（本项目未用）

### 11.3 新写法 lifespan（了解即可）

FastAPI 新版本推荐用 `lifespan` 上下文管理器替代 `on_event`：

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown

app = FastAPI(lifespan=lifespan)
```

---

## 12. Pydantic 进阶：枚举、校验、ORM 转换

`schemas.py` 集中定义了所有 API 数据形状。

### 12.1 BaseModel 基础

```python
from pydantic import BaseModel, Field

class ProductOut(BaseModel):
    id: int
    code: str
    name: str
    description: str | None = None
```

每个字段都有类型注解，Pydantic 据此校验。

### 12.2 可选类型 `X | None`

```python
customer: str | None = None
```

表示字段可省略或为 `null`。等同于 `Optional[str] = None`。

### 12.3 Field 校验约束

```python
quantity: int = Field(default=1, ge=1)
priority: int = Field(default=5, ge=1, le=10)
```

| 约束 | 含义 |
|---|---|
| `default=1` | 默认值 |
| `ge=1` | greater or equal，≥ 1 |
| `le=10` | less or equal，≤ 10 |

### 12.4 枚举 Enum

```python
class WorkOrderStatus(str, Enum):
    PENDING = "pending"
    RELEASED = "released"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CLOSED = "closed"
```

继承 `str, Enum` 使枚举值在 JSON 中序列化为字符串（`"pending"` 而不是枚举对象）。

用于：
- 响应字段：`status: WorkOrderStatus`
- 请求字段：`result: QualityResult`

API 文档会自动显示可选枚举值。

### 12.5 输入模型 vs 输出模型

| 类型 | 命名 | 用途 | 示例 |
|---|---|---|---|
| 输入 / 创建 | `*Create`、`*Request` | 接收客户端提交的数据 | `WorkOrderCreate` |
| 输出 | `*Out` | 返回给客户端的数据 | `WorkOrderOut` |

**为什么分开？**

- 创建工单不需要 `id`、`order_no`、`created_at`（服务端生成）
- 输出工单需要嵌套 `product`、`station_tasks` 等关联数据
- 避免客户端篡改只读字段

### 12.6 model_config = {"from_attributes": True}

见 [第 7.2 节](#72-返回-orm-对象--from_attributes)。这是 SQLAlchemy + FastAPI 集成的关键配置。

---

## 13. 项目架构分层

本项目采用了 FastAPI 社区推荐的**分层架构**：

```
┌─────────────────────────────────────────────┐
│  main.py          路由层（HTTP 入口）         │
│  - 定义 URL、方法                             │
│  - 注入 db 依赖                               │
│  - 调用 services                              │
│  - 处理 HTTPException                        │
├─────────────────────────────────────────────┤
│  schemas.py       契约层（API 数据形状）       │
│  - 请求/响应 Pydantic 模型                    │
│  - 与数据库模型解耦                           │
├─────────────────────────────────────────────┤
│  services.py      业务逻辑层                  │
│  - 创建工单、下达、开工、报工                  │
│  - 抛 ValueError，不感知 HTTP                 │
├─────────────────────────────────────────────┤
│  models.py        数据层（SQLAlchemy ORM）    │
│  - 表结构、关系映射                           │
├─────────────────────────────────────────────┤
│  database.py      基础设施层                  │
│  - 引擎、Session、get_db                      │
├─────────────────────────────────────────────┤
│  seed.py          数据初始化                  │
└─────────────────────────────────────────────┘
```

### 13.1 路由层应保持轻薄

好的做法（本项目大部分遵循）：

```python
def create_order(data: WorkOrderCreate, db: Session = Depends(get_db)):
    try:
        order = create_work_order(db, data)   # 业务逻辑在 services
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return get_work_order(order.id, db)       # 查询完整对象返回
```

路由函数理想情况下只有 3～5 行。

### 13.2 schemas 与 models 的区别

| | `models.py` (SQLAlchemy) | `schemas.py` (Pydantic) |
|---|---|---|
| 目的 | 数据库表映射 | API 输入输出 |
| 使用位置 | services、seed | 路由函数签名 |
| 关系 | `relationship()` | 嵌套 Pydantic 模型 |
| 生命周期 | 持久化到 DB | 请求/响应瞬间存在 |

两者字段相似但**不必相同**。例如 `WorkOrder` ORM 有 `product_id` 外键，而 `WorkOrderOut` 暴露嵌套的 `product: ProductOut`。

---

## 14. 完整 API 端点速查

### 14.1 系统

| 方法 | 路径 | 说明 | 响应模型 |
|---|---|---|---|
| GET | `/api/health` | 健康检查 | `dict` |

### 14.2 仪表盘

| 方法 | 路径 | 说明 | 响应模型 |
|---|---|---|---|
| GET | `/api/dashboard` | 生产概览统计 | `DashboardStats` |

### 14.3 产品 & BOM

| 方法 | 路径 | 路径参数 | 响应模型 |
|---|---|---|---|
| GET | `/api/products` | — | `list[ProductOut]` |
| GET | `/api/products/{product_id}/bom` | `product_id` | `list[BomItemOut]` |

### 14.4 物料 & 工位

| 方法 | 路径 | 响应模型 |
|---|---|---|
| GET | `/api/materials` | `list[MaterialOut]` |
| GET | `/api/stations` | `list[WorkStationOut]` |

### 14.5 工单

| 方法 | 路径 | 参数 | 请求体 | 响应模型 |
|---|---|---|---|---|
| GET | `/api/work-orders` | — | — | `list[WorkOrderOut]` |
| GET | `/api/work-orders/{order_id}` | `order_id` | — | `WorkOrderOut` |
| POST | `/api/work-orders` | — | `WorkOrderCreate` | `WorkOrderOut` |
| POST | `/api/work-orders/{order_id}/release` | `order_id` | — | `WorkOrderOut` |
| POST | `/api/work-orders/{order_id}/issue-materials` | `order_id` | — | `list[MaterialIssueOut]` |
| GET | `/api/work-orders/{order_id}/materials` | `order_id` | — | `list[MaterialIssueOut]` |

### 14.6 工位任务

| 方法 | 路径 | 参数 | 请求体 | 响应模型 |
|---|---|---|---|---|
| GET | `/api/station-tasks` | `?station_id=` | — | `list[StationTaskOut]` |
| POST | `/api/station-tasks/{task_id}/start` | `task_id` | `TaskStartRequest` | `StationTaskOut` |
| POST | `/api/station-tasks/{task_id}/complete` | `task_id` | `TaskCompleteRequest` | `StationTaskOut` |

### 14.7 质检

| 方法 | 路径 | 参数 | 请求体 | 响应模型 |
|---|---|---|---|---|
| GET | `/api/quality-records` | `?work_order_id=` | — | `list[QualityRecordOut]` |
| POST | `/api/quality-records` | — | `QualityRecordCreate` | `QualityRecordOut` |

---

## 15. 一次请求的完整生命周期

以 **创建工单** `POST /api/work-orders` 为例：

```
1. 客户端发送 HTTP 请求
   POST /api/work-orders
   Content-Type: application/json
   Body: {"product_id": 1, "quantity": 1, "customer": "中建三局"}

2. Uvicorn 接收请求，交给 FastAPI

3. CORS 中间件处理（添加跨域头）

4. FastAPI 路由匹配
   → 找到 create_order 函数

5. 依赖注入执行
   → get_db() 创建 SQLAlchemy Session

6. 请求体解析与校验
   → JSON → WorkOrderCreate 实例
   → 校验 product_id 是 int、quantity >= 1 等

7. 路由函数执行
   → create_work_order(db, data)  # services 层
     → 查产品、查工艺路线
     → 生成工单号 WO-20250706-001
     → 创建 StationTask、MaterialIssue
     → db.commit()
   → get_work_order(order.id, db)  # 查完整嵌套数据

8. 响应序列化
   → ORM WorkOrder → Pydantic WorkOrderOut（from_attributes）
   → JSON

9. 依赖清理
   → get_db() finally 块关闭 Session

10. 返回 HTTP 200 + JSON 给客户端
```

若以 **开工** 为例，业务校验失败时：

```
start_task() 抛出 ValueError("上一道工序尚未完成")
    ↓
路由捕获 → HTTPException(400, "上一道工序尚未完成")
    ↓
客户端收到 HTTP 400
```

---

## 16. 本项目未使用但值得了解的 FastAPI 特性

随着项目变大，你可能会用到以下特性：

### 16.1 APIRouter — 路由模块化

当 `main.py` 变大时，可按模块拆分：

```python
# app/routers/work_orders.py
from fastapi import APIRouter
router = APIRouter(prefix="/api/work-orders", tags=["工单"])

@router.get("")
def list_work_orders(...): ...

# main.py
from app.routers import work_orders
app.include_router(work_orders.router)
```

### 16.2 路由标签 tags 与分组

```python
@app.get("/api/products", tags=["产品"], summary="获取产品列表")
```

让 `/docs` 按模块分组，更易浏览。

### 16.3 BackgroundTasks — 后台任务

```python
from fastapi import BackgroundTasks

@app.post("/api/notify")
def notify(background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, "user@example.com")
    return {"ok": True}
```

适合发送邮件、写日志等不需要阻塞响应的操作。

### 16.4 文件上传

`requirements.txt` 已包含 `python-multipart`：

```python
from fastapi import UploadFile, File

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    contents = await file.read()
    ...
```

### 16.5 安全认证

```python
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/api/me")
def read_users_me(token: str = Depends(oauth2_scheme)):
    ...
```

### 16.6 自定义异常处理器

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})
```

可以替代每个路由里的 `try/except ValueError`。

### 16.7 异步路由 async def

```python
@app.get("/api/products")
async def list_products(db: Session = Depends(get_db)):
    ...
```

本项目全部使用同步 `def`。当需要 `await` 调用异步库（如 `httpx`、`asyncpg`）时改用 `async def`。  
注意：同步 `def` 路由在线程池中运行，异步 `def` 在主事件循环中运行；混用 SQLAlchemy 同步 Session 时用 `def` 更简单。

### 16.8 状态码显式声明

```python
from fastapi import status

@app.post("/api/work-orders", status_code=status.HTTP_201_CREATED)
def create_order(...): ...
```

创建资源时通常返回 `201 Created` 而非默认 `200`。

### 16.9 lifespan 替代 on_event

见 [第 11.3 节](#113-新写法-lifespan了解即可)。FastAPI 0.93+ 引入，0.115 仍支持 `on_event` 但文档标注为 deprecated。

---

## 17. 学习建议与动手练习

### 17.1 建议阅读顺序

1. `database.py` — 理解 `get_db` 依赖
2. `schemas.py` — 理解 API 数据契约
3. `main.py` — 对照 `/docs` 看每个端点
4. `services.py` — 理解业务逻辑（非 FastAPI，但是路由调用的核心）
5. `models.py` — 理解数据库表结构（配合理解嵌套响应）

### 17.2 动手实验

**实验 1：用 Swagger UI 调 API**

1. `python run.py`
2. 打开 http://localhost:8000/docs
3. 展开 `GET /api/work-orders` → Try it out → Execute
4. 观察响应结构和状态码

**实验 2：触发 422 校验错误**

在 Swagger 中 POST 工单，`quantity` 填 `0`，观察 422 响应结构。

**实验 3：触发 400 业务错误**

对一个「已下达」的工单再次调用 `release`，观察 400 响应。

**实验 4：添加一个简单端点**

在 `main.py` 添加：

```python
@app.get("/api/materials/low-stock", response_model=list[MaterialOut])
def low_stock_materials(db: Session = Depends(get_db)):
    return db.query(Material).filter(Material.stock_qty < 10).all()
```

刷新 `/docs`，确认新端点出现并可调用。

**实验 5：添加 DELETE 端点**

练习 RESTful 风格，为工单添加删除（需同时在 services 层实现逻辑）。

### 17.3 关键概念速记卡

| 概念 | 一句话记忆 |
|---|---|
| `FastAPI()` | 应用入口，挂载路由和中间件 |
| `@app.get/post` | 把函数绑定到 URL + HTTP 方法 |
| 路径参数 | 写在 URL `{}` 里，函数同名参数 |
| 查询参数 | 函数普通参数，不在路径中出现 |
| Pydantic 模型 | POST 请求体自动解析校验 |
| `response_model` | 控制输出形状 + 生成文档 |
| `Depends` | 依赖注入，复用 db、认证等 |
| `HTTPException` | 主动返回 4xx/5xx 错误 |
| `from_attributes` | 让 Pydantic 读取 ORM 对象属性 |
| `CORSMiddleware` | 解决浏览器跨域问题 |

---

## 附录：文件与 FastAPI 知识点对照表

| 文件 | 涉及的 FastAPI 知识点 |
|---|---|
| `run.py` | Uvicorn ASGI 服务器、热重载 |
| `app/main.py` | FastAPI 实例、路由、依赖注入、中间件、启动事件、HTTPException、response_model |
| `app/schemas.py` | Pydantic BaseModel、Field 校验、Enum、from_attributes、输入/输出模型分离 |
| `app/database.py` | 生成器依赖（yield）、Session 生命周期 |
| `app/services.py` | 业务逻辑（非 FastAPI，被路由调用） |
| `app/models.py` | SQLAlchemy ORM（非 FastAPI，配合 from_attributes 输出） |
| `app/seed.py` | 启动时数据初始化（非 FastAPI） |

---

*文档基于项目代码生成，FastAPI 版本 0.115.6，Pydantic 版本 2.10.3。*
