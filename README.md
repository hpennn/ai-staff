# AI 客服员工系统

轻量级对话式 AI 客服系统。每个"客服员工"是一个独立的 AI Agent，拥有独立角色、知识库和话术风格。管理员通过对话式界面管理客服员工，支持通过通用 Webhook 接入任意平台。

## ✨ 特性

- 🤖 **多 Agent 客服** — 每个客服员工独立配置角色和知识库
- 💬 **对话式管理** — 类似 ChatGPT 的交互界面
- 📱 **PWA 支持** — 可安装到手机和电脑桌面
- 🔗 **Webhook 接入** — 通用 Webhook 接口，支持任意平台接入
- 🚀 **一键部署** — Docker 一键启动，开箱即用
- 🎨 **移动优先** — 响应式设计，完美适配手机和桌面

## 🛠 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | 纯 HTML + Tailwind CDN + 原生 JavaScript |
| 后端 | Python FastAPI + SQLite |
| AI 模型 | 豆包 (DOUBAO) / 兼容 OpenAI API |
| 部署 | Docker + docker-compose |

## 📁 项目结构

```
ai-staff/
├── frontend/
│   ├── index.html          # 主 HTML（含所有页面逻辑）
│   ├── manifest.json       # PWA 配置
│   ├── sw.js               # Service Worker
│   └── icons/
│       ├── icon-192.png
│       └── icon-512.png
├── backend/
│   ├── main.py             # FastAPI 入口 + 静态文件服务
│   ├── database.py         # SQLite 数据库初始化
│   ├── models.py           # Pydantic 数据模型
│   ├── agent_service.py    # AI Agent 调度（调用 DOUBAO）
│   ├── requirements.txt    # Python 依赖
│   └── routers/
│       ├── chat.py         # 聊天 API
│       ├── staff.py        # 员工管理 + 对话 + 设置 API
│       └── webhook.py      # Webhook API
├── data/                   # 运行时数据（SQLite 等）
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🚀 快速开始

### Docker 部署（推荐）

```bash
# 使用 docker-compose
docker-compose up -d

# 或直接用 docker run
docker build -t ai-staff .
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data --name ai-staff ai-staff
```

访问 http://localhost:8000 即可使用。

### 本地开发

```bash
# 安装依赖
cd backend
pip install -r requirements.txt

# 启动服务
python main.py
```

## 📡 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | 发送消息给客服员工 |
| GET | `/api/staff` | 获取所有客服员工列表 |
| POST | `/api/staff` | 创建客服员工 |
| DELETE | `/api/staff/{id}` | 删除客服员工 |
| GET | `/api/conversations` | 获取对话列表 |
| GET | `/api/conversations/{id}` | 获取对话详情 |
| DELETE | `/api/conversations/{id}` | 删除对话 |
| POST | `/api/webhook` | 通用 Webhook 接口 |
| GET | `/api/settings` | 获取系统设置 |
| PUT | `/api/settings` | 更新系统设置 |

### Webhook 接入示例

```bash
curl -X POST http://localhost:8000/api/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "wechat",
    "staff_id": 1,
    "message": "你好，请问产品价格？",
    "session_id": "user-123"
  }'
```

## ⚙️ 配置

系统启动后可在"设置"页面中修改：

- **API Key** — AI 模型的 API 密钥
- **模型 ID** — AI 模型端点 ID
- **API Base URL** — API 服务地址（兼容 OpenAI 格式）

默认使用豆包 (DOUBAO) 模型。

## 📱 PWA 安装

1. 在浏览器中打开系统
2. 点击浏览器菜单中的"安装应用"或"添加到主屏幕"
3. 即可像原生应用一样使用

## 📄 License

MIT
