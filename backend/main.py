"""
材料可视化 - 后端 API
提供 XRD 数据处理与可视化数据接口、用户认证接口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import xrd_router, auth_router, visitor_router, agent_router

app = FastAPI(title="材料 XRD 可视化", version="1.0.0")

# 允许跨域请求（开发模式：前端 dev server 访问后端）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:8082"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(xrd_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(visitor_router, prefix="/api")
app.include_router(agent_router, prefix="/api")


@app.get("/")
async def root():
    """API 根路径"""
    return {"message": "材料 XRD 可视化 API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
