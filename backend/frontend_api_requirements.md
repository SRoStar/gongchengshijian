# 前端所需后端接口清单

> 基于前端代码 (`frontend/src/api/index.js`) 整理
> 基础URL: `/pichemdata/api`
> 返回格式统一: `{ code: 200, msg: null, data: {...} }`

---

## 一、认证相关 (Auth)

### 1. 用户注册
- **接口**: `POST /register`
- **请求体**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": { "success": true }
}
```

### 2. 用户登出
- **接口**: `POST /logout`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": null
}
```

### 3. 获取访客数
- **接口**: `GET /visitor-count`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": 23748
}
```

### 4. 修改密码
- **接口**: `POST /change-password`
- **请求体**:
```json
{
  "oldPassword": "string",
  "newPassword": "string"
}
```
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": { "success": true }
}
```

---

## 二、新闻管理 (News)

### 5. 获取新闻列表
- **接口**: `GET /news`
- **参数**: `page`, `size`, `keyword`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": {
    "result": [
      {
        "id": 1,
        "title": "string",
        "summary": "string",
        "content": "string",
        "publishDate": "2024-01-01",
        "author": "string",
        "views": 100
      }
    ],
    "page": { "size": 10, "current": 1, "total": 100 }
  }
}
```

### 6. 获取新闻详情
- **接口**: `GET /news/{id}`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": {
    "id": 1,
    "title": "string",
    "summary": "string",
    "content": "string",
    "publishDate": "2024-01-01",
    "author": "string",
    "views": 100
  }
}
```

---

## 三、公告管理 (Announcements)

### 7. 获取公告列表
- **接口**: `GET /announcements`
- **参数**: `page`, `size`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": {
    "result": [
      {
        "id": 1,
        "title": "string",
        "content": "string",
        "publishDate": "2024-01-01",
        "priority": "high"
      }
    ],
    "page": { "size": 10, "current": 1, "total": 100 }
  }
}
```

### 8. 获取公告详情
- **接口**: `GET /announcements/{id}`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": {
    "id": 1,
    "title": "string",
    "content": "string",
    "publishDate": "2024-01-01",
    "priority": "high"
  }
}
```

---

## 四、分子数据 (Molecule)

### 9. 获取分子列表
- **接口**: `GET /molecule/list`
- **参数**: `page`, `size`, `keyword`, `type`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": {
    "result": [
      {
        "id": 1,
        "formula": "H2O",
        "smiles": "O",
        "inchi": "string",
        "mass": 18.015,
        "charge": 0,
        "spin": 0,
        "type": "organic",
        "tags": ["small", "solvent"]
      }
    ],
    "page": { "size": 10, "current": 1, "total": 100 }
  }
}
```

### 10. 获取分子详情
- **接口**: `GET /molecule/detail/{id}`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": {
    "id": 1,
    "formula": "H2O",
    "smiles": "O",
    "inchi": "string",
    "mass": 18.015,
    "charge": 0,
    "spin": 0,
    "type": "organic",
    "tags": ["small", "solvent"],
    "structure": "string",
    "properties": {}
  }
}
```

### 11. 获取分子标签列表
- **接口**: `GET /molecule/tags`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": ["organic", "inorganic", "metal", "polymer"]
}
```

### 12. 相似分子搜索
- **接口**: `POST /molecule/similarity`
- **请求体**:
```json
{
  "smiles": "CCO",
  "type": "2d",
  "threshold": 0.7
}
```
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": {
    "result": [
      {
        "id": 1,
        "formula": "H2O",
        "smiles": "O",
        "similarity": "0.9500"
      }
    ]
  }
}
```

---

## 五、材料数据 (Materials)

### 13. 获取材料列表
- **接口**: `GET /materials`
- **参数**: `page`, `size`, `keyword`, `type`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": {
    "result": [
      {
        "id": 1,
        "name": "Graphene",
        "formula": "C",
        "type": "2D",
        "tags": ["conductor", "nanomaterial"],
        "description": "string"
      }
    ],
    "page": { "size": 10, "current": 1, "total": 100 }
  }
}
```

### 14. 获取材料详情
- **接口**: `GET /materials/{id}`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": {
    "id": 1,
    "name": "Graphene",
    "formula": "C",
    "type": "2D",
    "tags": ["conductor", "nanomaterial"],
    "description": "string",
    "properties": {},
    "structure": {}
  }
}
```

### 15. 获取材料标签列表
- **接口**: `GET /materials/tags`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": ["2D", "3D", "metal", "semiconductor"]
}
```

---

## 六、文献数据 (Literature)

### 16. 获取文献列表
- **接口**: `GET /literature`
- **参数**: `page`, `size`, `keyword`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": {
    "result": [
      {
        "id": 1,
        "title": "string",
        "authors": "string",
        "doi": "string",
        "journal": "string",
        "year": 2024,
        "abstract": "string"
      }
    ],
    "page": { "size": 10, "current": 1, "total": 100 }
  }
}
```

### 17. 获取文献详情
- **接口**: `GET /literature/{id}`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": {
    "id": 1,
    "title": "string",
    "authors": "string",
    "doi": "string",
    "journal": "string",
    "year": 2024,
    "abstract": "string",
    "fullText": "string"
  }
}
```

---

## 七、API 服务 (API Info)

### 18. 获取API服务列表
- **接口**: `GET /api-services`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": [
    {
      "id": 1,
      "name": "string",
      "endpoint": "string",
      "description": "string",
      "status": "active"
    }
  ]
}
```

---

## 八、管理后台 (Admin)

### 19. 获取审计日志
- **接口**: `GET /admin/audit-logs`
- **参数**: `page`, `size`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": {
    "result": [
      {
        "id": 1,
        "action": "string",
        "user": "string",
        "timestamp": "2024-01-01T00:00:00",
        "details": "string"
      }
    ],
    "page": { "size": 10, "current": 1, "total": 100 }
  }
}
```

### 20. 获取元数据列表
- **接口**: `GET /admin/metadata`
- **参数**: `page`, `size`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": {
    "result": [
      {
        "id": 1,
        "key": "string",
        "value": "string",
        "type": "string"
      }
    ],
    "page": { "size": 10, "current": 1, "total": 100 }
  }
}
```

### 21. 保存元数据
- **接口**: `POST /admin/metadata`
- **请求体**:
```json
{
  "id": 1,
  "key": "string",
  "value": "string",
  "type": "string"
}
```
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": { "success": true, "id": 12345 }
}
```

### 22. 删除元数据
- **接口**: `DELETE /admin/metadata/{id}`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": { "success": true }
}
```

---

## 九、文件上传 (Upload)

### 23. 通用数据上传
- **接口**: `POST /upload`
- **Content-Type**: `multipart/form-data`
- **请求**: FormData with file(s)
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": { "success": true, "fileId": 12345 }
}
```

---

## 十、分子开放API (Molecule Open APIs)

### 24. 核心分子搜索
- **接口**: `POST /molecule/open/search/core`
- **请求体**:
```json
{
  "page": 1,
  "size": 10,
  "keyword": "string",
  "type": "string",
  "category": "string",
  "formula": "string",
  "smiles": "string",
  "inchi": "string",
  "massMin": 0,
  "massMax": 1000,
  "charge": 0,
  "spin": 0,
  "tags": [],
  "sortField": "mass",
  "sortOrder": "asc"
}
```
- **响应**: 同 获取分子列表

### 25. 根据PIC ID获取分子
- **接口**: `GET /molecule/open/{picId}`
- **响应**: 同 获取分子详情

### 26. 按类别统计
- **接口**: `GET /molecule/open/summary/groupbycategory`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": {
    "organic": 150,
    "inorganic": 80,
    "metal": 45,
    "polymer": 30
  }
}
```

### 27. 获取分子统计摘要
- **接口**: `GET /molecule/open/summary`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": {
    "total": 305,
    "withSpectrum": 200,
    "withStructure": 280,
    "lastUpdated": "2024-01-01"
  }
}
```

### 28. 上传分子文件
- **接口**: `POST /molecule/open/upload`
- **Content-Type**: `multipart/form-data`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": {
    "success": true,
    "uploadId": 12345,
    "fileCount": 3
  }
}
```

### 29. 获取光谱数据
- **接口**: `GET /molecule/open/spectrum/{picId}`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": [
    {
      "type": "IR",
      "data": [{ "x": 1000, "y": 0.5 }],
      "unit": "cm-1"
    }
  ]
}
```

### 30. 按光谱类型搜索
- **接口**: `POST /molecule/open/search/by-spectra-type`
- **请求体**:
```json
{
  "spectraType": "IR",
  "page": 1,
  "size": 10
}
```
- **响应**: 同 获取分子列表

### 31. 上传OBS文件
- **接口**: `POST /molecule/open/obs-files`
- **Content-Type**: `multipart/form-data`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": { "success": true, "fileId": "obs-12345" }
}
```

### 32. 下载OBS文件
- **接口**: `GET /molecule/open/obs-files/download`
- **参数**: `fileId`
- **响应**: 文件流 或
```json
{
  "code": 200,
  "msg": null,
  "data": {
    "id": "obs-12345",
    "name": "file.txt",
    "downloadUrl": "string"
  }
}
```

### 33. 流式预览OBS文件
- **接口**: `GET /molecule/open/obs-files/stream`
- **参数**: `fileId`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": {
    "id": "obs-12345",
    "name": "file.txt",
    "previewContent": "string",
    "previewType": "text"
  }
}
```

---

## 十一、AI 聊天 (AI Chat)

### 34. AI对话
- **接口**: `POST /ai/chat`
- **请求体**:
```json
{
  "message": "string",
  "history": [
    { "role": "user", "content": "string" },
    { "role": "assistant", "content": "string" }
  ]
}
```
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": {
    "reply": "string",
    "actions": [],
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

---

## 十二、社区 (Community)

### 35. 获取社区列表
- **接口**: `GET /community`
- **参数**: `page`, `size`
- **响应**:
```json
{
  "code": 200,
  "msg": null,
  "data": {
    "result": [
      {
        "id": 1,
        "name": "string",
        "description": "string",
        "members": 100
      }
    ],
    "page": { "size": 10, "current": 1, "total": 100 }
  }
}
```

---

## 十三、XRD (已实现)

> 以下接口前端注释说明已对接Python后端，**已实现**

- `POST /pichemdata/api/process`
- `POST /pichemdata/api/upload-npy`

---

## 接口实现状态统计

| 模块 | 接口数量 | 状态 |
|------|----------|------|
| Auth | 4 | 待实现 |
| News | 2 | 待实现 |
| Announcements | 2 | 待实现 |
| Molecule | 4 | 待实现 |
| Materials | 3 | 待实现 |
| Literature | 2 | 待实现 |
| API Info | 1 | 待实现 |
| Admin | 4 | 待实现 |
| Upload | 1 | 待实现 |
| Molecule Open APIs | 10 | 待实现 |
| AI Chat | 1 | 待实现 |
| Community | 1 | 待实现 |
| XRD | 2 | **已实现** |
| **合计** | **37** | **35待实现 / 2已实现** |

---

## 注意事项

1. **认证**: 除注册、登录、访客数外，其他接口需要 JWT Token 认证
2. **Token**: 在请求头中携带 `Authorization: Bearer <token>`
3. **分页**: 统一使用 `{ page: { size, current, total }, result: [...] }` 格式
4. **错误码**: 统一返回 `code` 字段，200 表示成功，401/403 表示认证失败
