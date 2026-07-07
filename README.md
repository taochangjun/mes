# SanyMES Demo — 三一重工 MES 简化版演示系统

基于三一重工 SanyMES 核心流程搭建的学习用 Demo，模拟 18 号工厂泵车总装线的制造执行场景。

## 系统架构

```
ERP / CRM / PLM          ← 计划层（模拟数据）
       ↓
  SanyMES Demo           ← 本系统（MES 执行层）
       ↓
  LES / WMS / AGV        ← 物流层（物料配送模拟）
       ↓
  DNC / IoT / 设备       ← 控制层（未实现）
```

## 功能模块

| 模块 | 路径 | 说明 |
|------|------|------|
| PCC 控制中心 | `/dashboard` | 生产概览、在制工单、工位状态 |
| 工单管理 | `/work-orders` | 创建工单、下达、物料配送 |
| MES 终端机 | `/terminal` | 工位 SOP 指导、开工、报完工 |
| 物料管理 | `/materials` | BOM 物料库存、关重件预警 |
| 质量管理 | `/quality` | 质检记录录入与追溯 |

## 核心业务流程

```
创建工单 → 自动生成工位任务 + 物料清单
    ↓
下达工单 → 状态变为「已下达」
    ↓
配送物料 → LES 模拟扣减库存
    ↓
MES 终端机 → 按工序顺序：开工 → 报完工
    ↓
质检录入 → 全生命周期质量追溯
    ↓
全部工序完成 → 工单自动完工
```

## 快速启动

### 方式一：一键启动

```bash
chmod +x start.sh
./start.sh
```

### 方式二：分别启动

**后端：**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

**前端：**
```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

**新人学习：** 先看原生 JS 对照 Demo → http://localhost:5173/native-demo.html（详见 `docs/frontend-guide.md` 第 0.11 节）

## 技术栈

- **后端**: Python 3.11+ / FastAPI / SQLAlchemy / SQLite
- **前端**: Vue 3 / Vite / Element Plus
- **数据**: 内置种子数据（52米泵车产线）

## 预置演示数据

- **产品**: 52米混凝土泵车、62米泵车、拖式混凝土泵
- **产线**: 18号工厂总装线A，7个工位
- **工单**: 1条生产中、1条已下达、1条待下达
- **场景**: 模拟「中建三局」订单正在液压系统工位作业

## 推荐体验路径

1. 打开 **PCC 控制中心** — 查看全局生产状态
2. 进入 **工单管理** — 查看 WO-20250706-001 的生产进度
3. 打开 **MES 终端机** — 选择「液压系统工位」，体验 SOP + 报工
4. 进入 **质量管理** — 查看已有质检记录
5. 创建新工单 — 完整走一遍流程

## API 文档

启动后端后访问: http://localhost:8000/docs

## 与真实 SanyMES 的差异

本 Demo 仅覆盖 MES 核心流程的学习演示，未包含：

- 真实 ERP/PLM 对接
- RFID/条码硬件集成
- AGV/立体库实时调度
- DNC 设备数据采集
- APS 高级排程算法
- 多工厂/多产线权限体系

## 项目结构

```
mes/
├── backend/
│   ├── app/
│   │   ├── main.py        # API 路由
│   │   ├── models.py      # 数据模型
│   │   ├── schemas.py     # Pydantic 模型
│   │   ├── services.py    # 业务逻辑
│   │   └── seed.py        # 演示数据
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── views/         # 页面组件
│       └── api.js         # API 封装
└── start.sh
```
