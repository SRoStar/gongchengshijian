"""
Routers package
"""

from .xrd import router as xrd_router
from .auth import router as auth_router, visitor_router

__all__ = ["xrd_router", "auth_router", "visitor_router"]
