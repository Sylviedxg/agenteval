# AgentEval

> AI Agent evaluation platform for PMs — trace viewer, badcase management, and subjective scoring for multi-agent pipelines.

AgentEval 是一个面向 AI 产品经理的多 Agent 链路评测平台。核心场景：PM 接入 AI Agent 产品，通过管理评测集、跑实验、收集全链路 Trace、分析 BadCase、记录变更，形成**发现问题 → 推动修改 → 验证修复**的完整质检闭环。

![screenshot](./docs/screenshot.png)

---

## Features

- **实验管理** — 创建评测实验，关联评测集 × 产品版本 × 评测方案
- **Trace 详情** — 可视化 Agent 执行链路，展示 MainAgent/CardAgent 节点、事件流（llm_call / tool_call / delegate / bubble）
- **评分面板** — 客观指标自动展示 + 主观指标滑动条打分，松开自动保存
- **BadCase 管理** — 列表筛选、严重程度标注、根因分析、修复建议
- **变更记录** — 时间轴追踪每次 Prompt/模型/工具变更
- **总览看板** — 实验数、BadCase 数、处理进度一览

---

## Tech Stack

**Frontend**
- React 18 + TypeScript + Vite
- Ant Design 5.x + Tailwind CSS
- TanStack Query v5 + Zustand
- React Router v6 + Axios

**Backend**
- FastAPI + Python 3.11
- SQLAlchemy 2.0 (async) + asyncpg
- PostgreSQL 15 + Redis
- Alembic (migrations) + Pydantic v2

---

## Getting Started

### Prerequisites

- Node.js 18+ / pnpm
- Python 3.11+
- PostgreSQL 15
- Redis

### 1. 数据库初始化

```bash
# 安装 PostgreSQL & Redis（Mac）
brew install postgresql@15 redis
brew services start postgresql@15
brew services start redis

# 创建数据库
psql postgres
CREATE USER agenteval WITH PASSWORD 'agenteval123';
CREATE DATABASE agenteval OWNER agenteval;
GRANT ALL PRIVILEGES ON DATABASE agenteval TO agenteval;
\q
```

### 2. 启动后端

```bash
cd agenteval-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env

# 数据库迁移
alembic upgrade head

# 启动服务
uvicorn app.main:app --reload --port 8000
```

访问 http://localhost:8000/docs 查看 API 文档。

### 3. 启动前端

```bash
cd agenteval-frontend
pnpm install
pnpm dev
```

访问 http://localhost:5173

### 4. 注入 Mock 数据

进入任意实验详情页，点击右上角「注入 Mock Trace」，即可体验完整的 Trace 链路查看和评分功能。

---

## Project Structure

```
agenteval/
├── agenteval-frontend/          # React 前端
│   └── src/
│       ├── pages/               # 页面组件
│       │   ├── Dashboard/       # 总览看板
│       │   ├── Experiments/     # 实验列表 + 详情 + Trace 详情
│       │   ├── BadCases/        # BadCase 管理
│       │   ├── Config/          # 产品配置 / 指标库 / 评测集
│       │   └── Changelog/       # 变更记录
│       ├── components/          # 公共组件
│       ├── api/                 # API 请求层
│       ├── stores/              # Zustand 状态
│       └── types/               # TypeScript 类型定义
│
└── agenteval-backend/           # FastAPI 后端
    └── app/
        ├── api/v1/              # REST API 路由
        ├── models/              # SQLAlchemy 数据模型
        ├── schemas/             # Pydantic 请求/响应模型
        ├── services/            # 业务逻辑层
        └── core/                # 配置 + 数据库连接
```

---

## Roadmap

- [ ] 真实 Agent 数据上报接口（Trace Ingestion API）
- [ ] 客观指标自动计算引擎
- [ ] 实验对比视图（两个版本并排 diff）
- [ ] 指标库完整 CRUD
- [ ] 导出评测报告（PDF）
- [ ] 多用户权限系统

---

## License

MIT
