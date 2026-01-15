# LLM Client App

一个基于 Streamlit + FastAPI 的本地 LLM 客户端应用，包含聊天界面、工具调用与开发者工具箱。

## 功能概览
- 聊天界面：支持多轮对话、系统提示词、模型选择与思考等级配置。
- 工具调用：后端提供时间获取与模拟联网搜索的工具接口。
- 存档管理：聊天记录与参数可保存/加载，支持归档并开启新对话。
- 开发者工具箱：批量将指定目录下的 `.py` 文件转换为 `.txt`。

## 技术栈
- Python
- Streamlit（前端 UI）
- FastAPI + Uvicorn（后端 API）
- OpenAI SDK（通过自定义 `BASE_URL` 调用模型）
- Pydantic、Requests

## 目录结构
- `start.py`：一键启动脚本（启动后端 + 前端）。
- `backend/`：FastAPI 服务、路由与核心逻辑。
- `frontend/`：Streamlit UI、组件与交互逻辑。
- `shared/constants.py`：全局配置（API Key、模型列表、存档路径等）。
- `app_config.json`：本地配置文件（存档路径、活跃存档）。

## 快速开始
1) 创建并激活虚拟环境：
```bash
python -m venv .venv
source .venv/bin/activate
```

2) 安装依赖：
```bash
pip install -r requirements.txt
```

3) 一键启动：
```bash
python start.py
```

或分别启动：
```bash
python backend/main.py
streamlit run frontend/main.py
```

前端地址：`http://localhost:8501`  
后端地址：`http://127.0.0.1:8000`

## 配置说明
- `shared/constants.py`
  - `API_KEY`、`BASE_URL`：模型 API 配置。
  - `MODEL_NAME_LIST`：可选模型列表。
  - `DEFAULT_BASE_HISTORY_DIR`：聊天存档默认目录。
  - `SOURCE_CODE_DIRS` / `DEFAULT_EXPORT_DIR`：工具箱批量转换路径配置。
- `app_config.json`
  - `history_dir`：存档目录（由 UI 更新）。
  - `active_archive_path`：当前活跃存档路径。

## API 接口
- `GET /`：健康检查。
- `POST /api/chat/chat`：聊天请求（请求体：`messages`）。
- `POST /api/tools/convert/py-to-txt`：批量转换 `.py` → `.txt`。
- `GET /api/tools/time`：获取系统时间。
- `POST /api/tools/search`：模拟联网搜索。

## 注意事项
- API Key 目前写在 `shared/constants.py`，建议改为环境变量或本地私密配置。
- `DEFAULT_BASE_HISTORY_DIR` 默认指向 WSL/OneDrive 路径，非该环境请修改。
