"""
Agent 模块
包含 AI 对话、RAG 检索、Prompt 模板等功能
"""

from .chat import router as agent_router
from .rag import retrieve, init_knowledge_base
from .prompts import SYSTEM_PROMPT, RAG_QUERY_TEMPLATE

__all__ = [
    "agent_router",
    "retrieve",
    "init_knowledge_base",
    "SYSTEM_PROMPT",
    "RAG_QUERY_TEMPLATE",
]