"""
XRD 数据处理路由
提供 XRD 数据处理与可视化数据接口
"""

from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from pathlib import Path
from typing import List
import io
import os
import uuid
import numpy as np
import torch

from xrd_processor import xrd_process

router = APIRouter(tags=["XRD"])

# In-memory cache for uploaded NPY files (用于分组选择功能)
_npy_cache = {}

# ========== 请求模型 ==========

class XRDDataPoint(BaseModel):
    angle: float  # 2-theta 角度 (度)
    intensity: float  # 强度


class ProcessRequest(BaseModel):
    data: List[XRDDataPoint]  # XRD 原始数据 [{angle, intensity}, ...]
    min_angle: float = 5.0
    max_angle: float = 90.0
    step: float = 0.01
    sigma: float = 0.1


class ProcessNpyGroupRequest(BaseModel):
    filename: str
    group_index: int
    min_angle: float = 5.0
    max_angle: float = 90.0
    step: float = 0.01
    sigma: float = 0.1


# ========== 原有端点（保持不变） ==========

@router.post("/process")
async def process_xrd(request: ProcessRequest):
    """
    对文本 XRD 数据做处理
    输入: { data: [[angle, intensity], ...], min_angle, max_angle, step, sigma }
    输出: { original: { angles, intensities }, processed: { angles, intensities } }
    """
    if not request.data:
        raise HTTPException(status_code=400, detail="XRD 数据不能为空")

    try:
        # 将对象列表转换为 numpy 数组 [N, 2]
        xrd_array = np.array([[p.angle, p.intensity] for p in request.data], dtype=np.float32)

        pos_emb, sign_emb = xrd_process(
            xrd_array,
            min_angle=request.min_angle,
            max_angle=request.max_angle,
            step=request.step,
            sigma=request.sigma,
        )

        # 生成用于绘图的网格角度
        grid_length = int((request.max_angle - request.min_angle) / request.step) + 1
        grid_angles = np.linspace(
            request.min_angle, request.max_angle, grid_length
        ).tolist()

        # 转换为可 JSON 序列化的列表
        broadened_intensities = sign_emb.squeeze().numpy().tolist()

        return {
            "original": {
                "angles": xrd_array[:, 0].tolist(),
                "intensities": xrd_array[:, 1].tolist(),
            },
            "processed": {
                "angles": grid_angles,
                "intensities": broadened_intensities,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/upload-npy")
async def upload_npy(
    file: UploadFile = File(..., description="NPY 文件"),
    min_angle: float = Form(5.0),
    max_angle: float = Form(90.0),
    step: float = Form(0.01),
    sigma: float = Form(0.1),
):
    """
    上传 .npy 文件并处理 XRD 数据（原有逻辑，直接处理返回结果）
    输入: FormData { file, min_angle, max_angle, step, sigma }
    输出: { original: { angles, intensities }, processed: { angles, intensities } }
    """
    if not file.filename or not file.filename.lower().endswith(".npy"):
        raise HTTPException(status_code=400, detail="请上传 .npy 文件")

    try:
        content = await file.read()
        buf = io.BytesIO(content)

        # 加载 NPY 文件
        arr = np.load(buf, allow_pickle=True)

        # 处理不同格式的 NPY 文件
        xrd_array = None

        # 处理 0 维对象（字典格式）
        if arr.ndim == 0:
            obj = arr.item()
            if isinstance(obj, dict) and "features" in obj:
                features = np.asarray(obj["features"], dtype=np.float32)
                # 取第一组数据
                if features.ndim == 2:
                    xrd_array = process_dense_features(features, min_angle, max_angle)
                else:
                    # 尝试作为原始数据
                    xrd_array = features.reshape(-1, 2) if features.size % 2 == 0 else None
            elif isinstance(obj, dict) and "data" in obj:
                xrd_array = np.asarray(obj["data"], dtype=np.float32)
            else:
                # 尝试直接转换
                xrd_array = np.asarray(obj, dtype=np.float32)
        # 处理 1 维数组
        elif arr.ndim == 1:
            # 可能是密集数据或需要配对
            if arr.size % 2 == 0:
                xrd_array = arr.reshape(-1, 2)
            else:
                # 假设是密集强度值，需要生成角度
                xrd_array = process_dense_data(arr, min_angle, max_angle)
        # 处理 2 维数组
        elif arr.ndim == 2:
            if arr.shape[1] == 2:
                # 已经是 [[angle, intensity], ...] 格式
                xrd_array = arr
            elif arr.shape[0] == 2:
                # 转置为 [[angle, intensity], ...] 格式
                xrd_array = arr.T
            else:
                # 假设是多组数据，取第一组
                xrd_array = process_dense_features(arr, min_angle, max_angle)

        if xrd_array is None or xrd_array.ndim != 2 or xrd_array.shape[1] != 2:
            raise HTTPException(status_code=400, detail="无法解析 NPY 文件格式")

        # 处理 XRD 数据
        pos_emb, sign_emb = xrd_process(
            xrd_array,
            min_angle=min_angle,
            max_angle=max_angle,
            step=step,
            sigma=sigma,
        )

        # 生成用于绘图的网格角度
        grid_length = int((max_angle - min_angle) / step) + 1
        grid_angles = np.linspace(min_angle, max_angle, grid_length).tolist()

        # 转换为可 JSON 序列化的列表
        broadened_intensities = sign_emb.squeeze().numpy().tolist()

        return {
            "original": {
                "angles": xrd_array[:, 0].tolist(),
                "intensities": xrd_array[:, 1].tolist(),
            },
            "processed": {
                "angles": grid_angles,
                "intensities": broadened_intensities,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


def process_dense_features(features, min_angle, max_angle):
    """
    将密集特征数据转换为 XRD 处理格式
    假设 features 是 [N, grid_points] 或 [grid_points] 格式
    """
    # 如果是 2D，取第一组
    if features.ndim == 2:
        data = features[0]
    else:
        data = features

    # 假设数据覆盖 min_angle 到 max_angle 的范围
    grid_points = data.shape[0]
    angles = np.linspace(min_angle, max_angle, grid_points)

    # 过滤掉接近零的值以提高效率
    threshold = 1e-6
    valid_mask = data > threshold

    if valid_mask.sum() == 0:
        return np.column_stack([angles, data])

    valid_angles = angles[valid_mask]
    valid_intensities = data[valid_mask]

    return np.column_stack([valid_angles, valid_intensities]).astype(np.float32)


def process_dense_data(data, min_angle, max_angle):
    """
    将 1D 密集数据转换为 XRD 处理格式
    """
    grid_points = data.shape[0]
    angles = np.linspace(min_angle, max_angle, grid_points)

    # 过滤掉接近零的值
    threshold = 1e-6
    valid_mask = data > threshold

    if valid_mask.sum() == 0:
        return np.column_stack([angles, data])

    valid_angles = angles[valid_mask]
    valid_intensities = data[valid_mask]

    return np.column_stack([valid_angles, valid_intensities]).astype(np.float32)


# ========== 新增：NPY 分组选择与双数据集对比端点 ==========

@router.post("/upload-npy-cache")
async def upload_npy_cache(
    file: UploadFile = File(..., description="NPY 文件，支持 features 格式"),
):
    """
    上传 NPY 文件并缓存，返回元数据（用于后续分组选择处理）
    输入: FormData { file }
    输出: { filename, total_groups, grid_points, shape }
    """
    if not file.filename or not file.filename.lower().endswith(".npy"):
        raise HTTPException(status_code=400, detail="请上传 .npy 文件")

    try:
        content = await file.read()
        buf = io.BytesIO(content)
        arr = np.load(buf, allow_pickle=True)
        cache_key = f"{file.filename}_{uuid.uuid4().hex[:8]}"

        if arr.ndim == 0:
            obj = arr.item()
            if isinstance(obj, dict) and "features" in obj:
                features = np.asarray(obj["features"], dtype=np.float32)
                if features.ndim != 2:
                    raise HTTPException(status_code=400, detail=f"features 应为二维数组，当前形状: {features.shape}")
                _npy_cache[cache_key] = features
                return {
                    "filename": cache_key,
                    "total_groups": features.shape[0],
                    "grid_points": features.shape[1],
                    "shape": list(features.shape),
                    "message": f"成功加载 {features.shape[0]} 组数据，每组 {features.shape[1]} 个网格点"
                }
            else:
                raise HTTPException(status_code=400, detail="NPY 文件必须包含 'features' 键")
        elif arr.ndim == 2:
            features = arr.astype(np.float32)
            _npy_cache[cache_key] = features
            return {
                "filename": cache_key,
                "total_groups": features.shape[0],
                "grid_points": features.shape[1],
                "shape": list(features.shape),
                "message": f"成功加载 {features.shape[0]} 组数据，每组 {features.shape[1]} 个点"
            }
        elif arr.ndim == 1:
            features = arr.reshape(1, -1).astype(np.float32)
            _npy_cache[cache_key] = features
            return {
                "filename": cache_key,
                "total_groups": 1,
                "grid_points": features.shape[1],
                "shape": list(features.shape),
                "message": f"成功加载 1 组数据，共 {features.shape[1]} 个点"
            }
        else:
            raise HTTPException(status_code=400, detail=f"不支持的 NPY 格式，形状: {arr.shape}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"无法解析 NPY 文件: {str(e)}")


@router.post("/process-npy-group")
async def process_npy_group(request: ProcessNpyGroupRequest):
    """
    处理已缓存 NPY 文件中的指定数据组（用于双数据集对比）
    输入: { filename, group_index, min_angle, max_angle, step, sigma }
    输出: { original: { angles, intensities }, processed: { angles, intensities } }
    """
    if request.filename not in _npy_cache:
        raise HTTPException(
            status_code=404,
            detail=f"文件 '{request.filename}' 未找到，请重新上传"
        )

    features = _npy_cache[request.filename]

    if request.group_index < 0 or request.group_index >= features.shape[0]:
        raise HTTPException(
            status_code=400,
            detail=f"数据组索引超出范围，可用范围: 0-{features.shape[0] - 1}"
        )

    try:
        group_data = features[request.group_index, :]
        angles = np.linspace(request.min_angle, request.max_angle, group_data.shape[0])
        threshold = 1e-6
        valid_mask = group_data > threshold

        if valid_mask.sum() == 0:
            grid_length = int((request.max_angle - request.min_angle) / request.step) + 1
            grid_angles = np.linspace(request.min_angle, request.max_angle, grid_length).tolist()
            return {
                "original": {"angles": [], "intensities": []},
                "processed": {"angles": grid_angles, "intensities": [0.0] * grid_length}
            }

        valid_angles = angles[valid_mask]
        valid_intensities = group_data[valid_mask]
        xrd_array = np.column_stack([valid_angles, valid_intensities]).astype(np.float32)

        pos_emb, sign_emb = xrd_process(
            xrd_array,
            min_angle=request.min_angle,
            max_angle=request.max_angle,
            step=request.step,
            sigma=request.sigma,
        )

        grid_length = int((request.max_angle - request.min_angle) / request.step) + 1
        grid_angles = np.linspace(request.min_angle, request.max_angle, grid_length).tolist()
        broadened_intensities = sign_emb.squeeze().numpy().tolist()

        return {
            "original": {
                "angles": valid_angles.tolist(),
                "intensities": valid_intensities.tolist(),
            },
            "processed": {
                "angles": grid_angles,
                "intensities": broadened_intensities,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.get("/npy-info/{filename}")
async def get_npy_info(filename: str):
    """
    获取已缓存 NPY 文件的信息
    """
    if filename not in _npy_cache:
        raise HTTPException(status_code=404, detail="文件未找到，请重新上传")

    features = _npy_cache[filename]
    return {
        "filename": filename,
        "total_groups": features.shape[0],
        "grid_points": features.shape[1],
        "shape": list(features.shape),
        "dtype": str(features.dtype)
    }
