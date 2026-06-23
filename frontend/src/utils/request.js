import axios from 'axios'
import { getToken, clearAuth } from './auth'
import { Message } from 'element-ui'
import router from '@/router'

const service = axios.create({
  baseURL: '/pichemdata/api',
  timeout: 15000
})

// 自动解析响应数据中的 JSON 字符串字段（tags、keywords、atoms、bonds 等）
function parseJsonFields(obj) {
  if (Array.isArray(obj)) {
    return obj.map(parseJsonFields)
  }
  if (obj && typeof obj === 'object') {
    const result = {}
    for (const [key, value] of Object.entries(obj)) {
      if (typeof value === 'string' && (value.startsWith('[') || value.startsWith('{'))) {
        try {
          result[key] = JSON.parse(value)
        } catch {
          result[key] = value
        }
      } else if (typeof value === 'object' && value !== null) {
        result[key] = parseJsonFields(value)
      } else {
        result[key] = value
      }
    }
    return result
  }
  return obj
}

// Request interceptor
service.interceptors.request.use(
  config => {
    const token = getToken()
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// Response interceptor
service.interceptors.response.use(
  response => {
    const res = response.data
    if (res.code === 403 || res.code === 401) {
      // 开发阶段仅拒绝请求，不清除登录态（避免 mock 登录被踢）
      return Promise.reject(new Error(res.msg || 'Auth failed'))
    }
    if (res.code !== 200) {
      Message.error(res.msg || 'Request failed')
      return Promise.reject(new Error(res.msg || 'Error'))
    }
    // 自动解析 JSON 字符串字段（如 tags、keywords、atoms、bonds）
    if (res.data) {
      res.data = parseJsonFields(res.data)
    }
    return res
  },
  error => {
    // 尝试从 HTTP 错误响应体中提取后端实际错误信息
    let msg = ''
    if (error.response && error.response.data) {
      const data = error.response.data
      if (typeof data === 'string') {
        // FastAPI 默认 500 返回纯文本，直接使用
        msg = data
      } else {
        msg = data.detail || data.msg || data.message || ''
      }
    }
    if (!msg) {
      msg = error.message || 'Network error'
    }
    Message.error(msg)
    return Promise.reject(new Error(msg))
  }
)

export default service
