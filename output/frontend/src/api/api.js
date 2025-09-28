import axios from 'axios'
import { authApi } from './auth.js'

const API_BASE_URL = '/api/v1'

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：添加 JWT token（如果存在）
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：处理 401 错误
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // 清除 token 并跳转到登录页
      authApi.logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 文章相关 API
export const articleApi = {
  // 获取文章列表（分页）
  getArticles(page = 1, limit = 10) {
    return apiClient.get('/articles', {
      params: { page, limit }
    })
  },

  // 获取单篇文章
  getArticle(id) {
    return apiClient.get(`/articles/${id}`)
  },

  // 创建文章
  createArticle(data) {
    return apiClient.post('/articles', data)
  },

  // 更新文章
  updateArticle(id, data) {
    return apiClient.put(`/articles/${id}`, data)
  },

  // 删除文章 - 新增的删除功能
  deleteArticle(id) {
    return apiClient.delete(`/articles/${id}`)
  }
}