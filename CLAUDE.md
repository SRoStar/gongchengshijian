# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

精准化学数据平台 (Precision Chemistry Data Platform) — 化学知识库与 XRD 可视化分析平台。Vue 2 前端 + FastAPI 后端，SQLite 数据库。

## 开发命令

### 后端
```bash
cd backend && python main.py          # 启动后端 API (端口 8000)
cd frontend/xrd-backend && python main.py  # 独立 XRD 后端
```

### 前端
```bash
cd frontend && npm run serve          # 开发服务器 (端口 8080)
cd frontend && npm run serve:xrd      # 同时启动前端 + XRD 后端 (concurrently)
cd frontend && npm run build          # 生产构建
```

## 架构要点

### 前后端通信
- 前端 dev server 代理配置在 `vue.config.js`
- `/pichemdata/api/*` → `http://localhost:8000` (路径重写去除前缀)
- XRD 请求始终直连真实后端（绕过 mock）

### API 设计模式
- 前端 `src/api/index.js` 中 `USE_MOCK = false` 时优先调用真实后端，失败则降级到 mock 数据
- `xrdProcess` / `xrdProcessNpy` 始终走真实 fetch，不经过 request 封装

### 后端路由 (`backend/routers/`)
- `xrd.py` — XRD 数据处理接口（`/api/process`, `/api/upload-npy` 等）
- `auth.py` — 用户认证、访客计数接口
- 路由通过 `backend/main.py` 注册到 FastAPI 应用

### 数据库 (`backend/database/initial_db.py`)
- SQLite，`chemistry.db`
- 建表函数按模块独立（`init_molecules_table`、`init_users_table` 等）
- `insert_molecule()` 使用 `INSERT OR REPLACE` 配合 `inchikey` 去重

### 前端状态管理 (`src/store/`)
- `modules/user.js` — 用户信息与认证状态
- `modules/materials.js` — 材料数据
- `modules/molecule.js` — 分子数据

### 路由与权限 (`src/router/index.js`)
- `hash` 模式，base 为 `/pichemdata/`
- `noAuth: true` 的路由无需登录，`requireAdmin: true` 仅限管理员

## 注意事项

- 前端 XRD 工具 (`/xrd-tool`) 可同时调用两个后端：`frontend/xrd-backend/main.py`（独立服务）和 `backend/main.py`（主后端）
- 新增后端路由：在 `backend/routers/` 新建文件，在 `backend/main.py` 中注册
- 前端 mock 数据在 `src/mock/data.js`，按模块分组