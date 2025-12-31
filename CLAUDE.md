# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI Assistant Web Application with a dual frontend/backend architecture. The application provides:
- **Chat mode**: AI conversation interface using Gemini API via proxy
- **Toolbox mode**: File conversion utilities (Python to text batch processing)

## Architecture

### MVC Pattern with Streamlit Data Bus
The application follows an MVC pattern where `st.session_state` serves as a "data bus" for cross-module communication. This is a key architectural decision documented in Chinese comments throughout the codebase.

### Component Structure
- **Frontend** (`/src/`): Streamlit-based web UI
  - `chat_logic.py`: Chat message rendering, session initialization, AI request logic
  - `ui_components.py`: Streamlit UI components, user input handling, sidebar rendering
  - `storage_module.py`: File operations, debugging logs, image encoding, history management
  - `constants.py`: API keys, model configurations, default settings, file paths
  - `toolbox_logic.py`: Batch file conversion utilities (py→txt)
  - `model_tools_call_functions.py`: AI model tool calling functions
  - `api_client.py`: API client initialization and configuration

- **Backend** (`/backend/`): FastAPI REST API server
  - `main.py`: FastAPI app initialization, server entry point
  - `tools_router.py`: REST API endpoints for toolbox operations
  - `schemas.py`: Pydantic data models for API requests/responses

### Key Architectural Decisions
1. **Dual-mode navigation**: Sidebar radio buttons switch between "💬 AI 对话" and "🛠️ 工具箱" modes
2. **WSL/OneDrive integration**: Persistence uses Windows OneDrive-mounted paths (`/mnt/c/Users/laplas/OneDrive/...`)
3. **API proxy usage**: Uses custom API endpoint (`https://api.fate86.cn/v1`) with OpenAI client to access Gemini API
4. **Defensive programming**: Extensive error handling and debug logging via `storage.debug_log()`
5. **Chinese comments**: Technical explanations in Chinese throughout the codebase

## Development Commands

### Environment Setup
```bash
# Run setup script (WSL-specific)
bash setup_environment.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running the Application
```bash
# Frontend (Streamlit web UI)
streamlit run main.py

# Backend (FastAPI REST API)
python backend/main.py
# Or directly with uvicorn:
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### Testing
No formal test framework is configured. Debug logging is available via `storage.debug_log()` function calls throughout the codebase.

## Configuration

### Key Configuration Files
- `app_config.json`: Application configuration (history directory path)
- `constants.py`: Static configuration (API endpoints, model settings, file paths)
- `requirements.txt` / `requirements-minimal.txt`: Python dependencies
- `environment.yml`: Conda environment configuration

### API Configuration
The application uses a proxy API endpoint for Gemini access:
- Base URL: `https://api.fate86.cn/v1`
- Client: OpenAI client configured to use the proxy endpoint
- Fallback: Google Generative AI client as backup

## File Persistence

History and session data are stored in:
- Primary: OneDrive-mounted directory (`/mnt/c/Users/laplas/OneDrive/...`)
- Configured via `app_config.json` → `history_dir` path

## Development Notes

### Code Conventions
- **Chinese comments**: Extensive technical explanations in Chinese
- **Session state usage**: `st.session_state` is the primary data bus for cross-module communication
- **Modular imports**: All `src/` modules are imported in `main.py` and communicate via session state
- **Debug logging**: Use `storage.debug_log()` for development tracing

### WSL Considerations
- Paths assume WSL2 environment with Windows OneDrive mounted at `/mnt/c/`
- `setup_environment.sh` includes WSL detection and setup guidance

### VS Code Configuration
Minimal VS Code settings in `.vscode/settings.json`:
```json
{
    "python.analysis.autoImportCompletions": false
}
```