"""
认证模块路由
提供用户认证相关接口：登录、注册、获取用户信息、退出登录、修改密码、访客计数
"""

from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
import sqlite3
import hashlib
import secrets
from pathlib import Path

router = APIRouter(tags=["Auth"])

# 数据库路径
DB_PATH = Path(__file__).resolve().parent.parent / "db_table" / "chemistry.db"

# 简单的 token 存储（生产环境应使用 Redis 等）
_token_store = {}


def get_db_path():
    """获取数据库路径"""
    return str(DB_PATH)


def get_visitor_count(db_path: str = None) -> int:
    """获取访客计数"""
    if db_path is None:
        db_path = get_db_path()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT count FROM visitor_count WHERE id = 1')
        result = cursor.fetchone()
        if result:
            return result[0]
        return 0


def increment_visitor_count(db_path: str = None) -> bool:
    """增加访客计数"""
    if db_path is None:
        db_path = get_db_path()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE visitor_count SET count = count + 1 WHERE id = 1
        ''')
        conn.commit()
        return cursor.rowcount > 0


def hash_password(password: str) -> str:
    """对密码进行哈希处理"""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_token(user_id: int) -> str:
    """生成 JWT 风格的 token"""
    token = secrets.token_urlsafe(32)
    _token_store[token] = user_id
    return token


def get_user_by_token(token: str) -> Optional[dict]:
    """根据 token 获取用户信息"""
    if token not in _token_store:
        return None
    user_id = _token_store[token]
    return get_user_by_id(user_id)


def get_user_by_username(username: str) -> Optional[dict]:
    """根据用户名获取用户信息"""
    with sqlite3.connect(get_db_path()) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password, email, role, nickname, phone, avatar, createTime FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def get_user_by_id(user_id: int) -> Optional[dict]:
    """根据 ID 获取用户信息"""
    with sqlite3.connect(get_db_path()) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, email, role, nickname, phone, avatar, createTime FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def create_user(username: str, password: str, email: str, nickname: str, phone: Optional[str] = None) -> bool:
    """创建新用户"""
    from datetime import datetime
    hashed_password = hash_password(password)
    create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(get_db_path()) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, email, nickname, phone, role, createTime) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (username, hashed_password, email, nickname, phone, "user", create_time)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def update_password(user_id: int, new_password: str) -> bool:
    """更新用户密码"""
    hashed_password = hash_password(new_password)
    with sqlite3.connect(get_db_path()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password = ? WHERE id = ?",
            (hashed_password, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


# ========== 请求/响应模型 ==========

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    userInfo: dict


class RegisterRequest(BaseModel):
    username: str
    password: str
    confirmPassword: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    nickname: Optional[str] = None


class RegisterResponse(BaseModel):
    success: bool


class ChangePasswordRequest(BaseModel):
    oldPassword: str
    newPassword: str


class ChangePasswordResponse(BaseModel):
    success: bool


# ========== 依赖项 ==========

from fastapi.responses import JSONResponse

async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """验证 token 并返回当前用户信息"""
    if not authorization:
        return JSONResponse(
            status_code=401,
            content={"code": 401, "msg": "未提供认证信息", "data": None}
        )

    # 处理 Bearer token
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    else:
        token = authorization

    user = get_user_by_token(token)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"code": 401, "msg": "无效的 token 或用户不存在", "data": None}
        )

    return user


# ========== 路由 ==========

@router.post("/login")
async def login(request: LoginRequest):
    """
    用户登录
    """
    user = get_user_by_username(request.username)
    if not user:
        return {"code": 401, "msg": "用户名或密码错误", "data": None}

    if user["password"] != hash_password(request.password):
        return {"code": 401, "msg": "用户名或密码错误", "data": None}

    # 生成 token
    token = generate_token(user["id"])

    # 构造响应
    user_info = {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"] or "",
        "role": user["role"] or "user",
        "nickname": user["nickname"] or "",
        "phone": user["phone"] or "",
        "avatar": user["avatar"] or "",
        "password": user["password"] or "",
        "createTime": user["createTime"] or ""
    }

    return {
        "code": 200,
        "msg": None,
        "data": {
            "token": token,
            "userInfo": user_info
        }
    }


@router.post("/register")
async def register(request: RegisterRequest):
    """
    用户注册
    """
    success = create_user(
        username=request.username,
        password=request.password,
        email=request.email,
        nickname=request.nickname or request.username,
        phone=request.phone
    )

    if not success:
        return {"code": 400, "msg": "用户名已存在", "data": None}

    return {"code": 200, "msg": None, "data": {"success": True}}


@router.get("/userinfo")
async def get_userinfo(current_user: dict = Depends(get_current_user)):
    """
    获取当前用户信息
    """
    return {
        "code": 200,
        "msg": None,
        "data": {
            "id": current_user["id"],
            "username": current_user["username"],
            "email": current_user["email"] or "",
            "role": current_user["role"] or "user",
            "nickname": current_user["nickname"] or "",
            "phone": current_user.get("phone", ""),
            "avatar": current_user.get("avatar", ""),
            "createTime": current_user.get("createTime", "")
        }
    }


@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """
    退出登录
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        if token in _token_store:
            del _token_store[token]

    return {"code": 200, "msg": None, "data": None}


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    修改密码
    """
    # 验证旧密码
    user = get_user_by_username(current_user["username"])
    if not user or user["password"] != hash_password(request.oldPassword):
        return {"code": 400, "msg": "旧密码错误", "data": None}

    # 更新密码
    success = update_password(current_user["id"], request.newPassword)
    if not success:
        return {"code": 500, "msg": "密码修改失败", "data": None}

    return {"code": 200, "msg": None, "data": {"success": True}}


# ========== 访客计数路由（不在 /auth 前缀下）==========

from fastapi import APIRouter as BaseRouter
visitor_router = BaseRouter(tags=["Visitor"])


@visitor_router.get("/visitor-count")
async def visitor_count():
    """
    获取访客计数
    """
    count = get_visitor_count(get_db_path())
    # 每次访问增加计数
    increment_visitor_count(get_db_path())
    return {"code": 200, "msg": None, "data": count}
