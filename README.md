# AI智能体工作台

一站式智能体框架，预置6大办公技能 + 知识库RAG + 任务编排 + 电脑控制。

## 功能特性

- 🎯 **6大预置技能**：文档生成、表格处理、图片处理、OCR识别、数据提取、文案生成
- 🧠 **知识库RAG**：上传企业文档，语义检索，让智能体懂业务
- 🔗 **智能编排**：LLM自动规划任务，多技能串联执行
- 🖥️ **电脑控制**：截图、点击、输入、自然语言操控桌面（需本地部署）
- 📱 **多端支持**：PWA + Capacitor App
- 🔌 **可扩展**：自定义技能槽，统一接口即插即用

## 快速部署

### 方式一：Cloudflare Pages（仅前端）

1. Fork 本仓库到 GitHub
2. Cloudflare Dashboard → Workers & Pages → Create → Pages → Connect Git
3. 构建设置：
   - Build command: 留空
   - Output directory: `frontend`
4. 部署

> 注意：纯前端部署仅展示UI，技能执行需要后端支持

### 方式二：Docker 部署（推荐，完整功能）

```bash
# 1. 克隆仓库
git clone https://github.com/hpennn/ai-staff.git
cd ai-staff

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填写 LLM_API_KEY

# 3. 启动
docker-compose up -d

# 4. 访问
open http://localhost:8080
```

### 方式三：直接部署到服务器

```bash
# 1. 安装 Python 3.10+
python3 --version

# 2. 安装依赖
cd ai-staff
pip install -r backend/requirements.txt

# 3. 配置环境变量
export LLM_API_KEY="your_key"
export LLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"

# 4. 启动后端
cd backend
uvicorn main:app --host 0.0.0.0 --port 8080

# 5. 访问 http://your-server:8080
```

### 方式四：Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 环境变量

| 变量 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| LLM_API_KEY | 大模型 API Key | ✅ | - |
| LLM_BASE_URL | API 地址 | ❌ | 阿里通义 |
| LLM_MODEL | 文本模型 | ❌ | qwen-plus |
| LLM_VL_MODEL | 多模态模型 | ❌ | qwen-vl-plus |
| KNOWLEDGE_DIR | 知识库目录 | ❌ | ./data/knowledge_base |
| COMPUTER_CONTROL_ENABLED | 电脑控制 | ❌ | false |

## 技能开发

自定义技能只需实现统一接口：

```python
# backend/skills/preset/my_skill.py
SKILL_META = {
    "id": "my_skill",
    "name": "我的技能",
    "icon": "🔧",
    "description": "技能描述",
    "keywords": ["关键词"],
    "input_type": "text",
    "output_type": "text",
}

async def execute(input_data: dict) -> dict:
    # 你的技能逻辑
    return {"result": "处理结果"}
```

然后在 `registry.py` 中注册即可。

## 项目结构

```
ai-staff/
├── frontend/          # PWA前端
│   ├── index.html     # 智能体工作台
│   ├── manifest.json
│   └── icons/
├── backend/
│   ├── main.py        # FastAPI入口
│   ├── skills/        # 技能引擎
│   │   ├── registry.py    # 技能注册中心
│   │   ├── engine.py      # 执行引擎
│   │   ├── llm_client.py  # LLM客户端
│   │   └── preset/        # 预置技能
│   ├── knowledge/     # 知识库RAG
│   │   ├── vector_store.py
│   │   ├── document_parser.py
│   │   └── embedder.py
│   ├── orchestration/ # 任务编排
│   │   ├── workflow.py
│   │   └── planner.py
│   ├── computer/      # 电脑控制
│   │   ├── controller.py
│   │   └── vision.py
│   └── routers/       # API路由
├── .env.example
└── docker-compose.yml
```

## API 文档

启动后端后访问 `http://localhost:8080/docs` 查看完整API文档。

主要接口：
- `GET /api/skills` - 技能列表
- `POST /api/skills/{id}/execute` - 执行技能
- `POST /api/knowledge/upload` - 上传文档到知识库
- `POST /api/knowledge/search` - 语义搜索
- `POST /api/workflows/plan` - 智能规划任务
- `POST /api/workflows/execute` - 执行工作流
- `POST /api/computer/screenshot` - 屏幕截图
- `POST /api/computer/execute` - 自然语言操控

## License

MIT
