<template>
  <div class="login-container">
    <div class="login-form">
      <h2>登录</h2>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="identifier">用户名或邮箱</label>
          <input
            id="identifier"
            v-model="credentials.identifier"
            type="text"
            required
            placeholder="请输入用户名或邮箱"
            class="form-input"
          />
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="credentials.password"
            type="password"
            required
            placeholder="请输入密码"
            class="form-input"
          />
        </div>
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
        <div class="register-link">
          还没有账户？<router-link to="/register">立即注册</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { authApi } from '@/api/auth.js'

export default {
  name: 'Login',
  data() {
    return {
      credentials: {
        identifier: '',
        password: ''
      },
      loading: false,
      error: null
    }
  },
  methods: {
    async handleLogin() {
      this.loading = true
      this.error = null
      
      try {
        const response = await authApi.login(this.credentials)
        if (response.data.success && response.data.data.token) {
          localStorage.setItem('token', response.data.data.token)
          // 跳转到首页
          this.$router.push('/')
        } else {
          throw new Error('登录失败')
        }
      } catch (err) {
        console.error('登录错误:', err)
        this.error = err.response?.data?.message || '用户名或密码错误'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.login-form {
  background: white;
  padding: 32px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  width: 100%;
  max-width: 400px;
}

.login-form h2 {
  text-align: center;
  margin-bottom: 24px;
  color: #2c3e50;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: #2c3e50;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
}

.form-input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

.error-message {
  color: #e74c3c;
  margin-bottom: 16px;
  text-align: center;
}

.btn-primary {
  width: 100%;
  padding: 10px;
  border: none;
  border-radius: 4px;
  background-color: #3498db;
  color: white;
  font-size: 16px;
  cursor: pointer;
  margin-bottom: 16px;
}

.btn-primary:hover:not(:disabled) {
  background-color: #2980b9;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.register-link {
  text-align: center;
}

.register-link a {
  color: #3498db;
  text-decoration: none;
}

.register-link a:hover {
  text-decoration: underline;
}
</style>