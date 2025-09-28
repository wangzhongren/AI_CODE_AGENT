import axios from 'axios'

const AUTH_BASE_URL = '/api/v1'

// 创建 axios 实例用于认证
const authClient = axios.create({
  baseURL: AUTH_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 认证相关 API - 严格按照 API spec 实现
export const authApi = {
  // 注册 - POST /auth/register
  register(userData) {
    return authClient.post('/auth/register', {
      username: userData.username,
      email: userData.email,
      password: userData.password
    })
  },
  
  // 登录 - POST /auth/login
  login(credentials) {
    return authClient.post('/auth/login', {
      identifier: credentials.identifier, // 用户名或邮箱
      password: credentials.password
    })
  },
  
  // 登出
  logout() {
    localStorage.removeItem('token')
  },
  
  // 获取当前用户信息 - GET /auth/me
  getCurrentUser() {
    const token = localStorage.getItem('token')
    if (!token) {
      return Promise.reject(new Error('No token found'))
    }
    
    return authClient.get('/auth/me')
  }
}