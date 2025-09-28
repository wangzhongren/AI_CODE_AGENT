<template>
  <div class="register-container">
    <div class="register-form">
      <h2>注册</h2>
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label for="username">用户名</label>
          <input
            id="username"
            v-model="credentials.username"
            type="text"
            required
            placeholder="请输入用户名"
            class="form-input"
          />
        </div>
        <div class="form-group">
          <label for="email">邮箱</label>
          <input
            id="email"
            v-model="credentials.email"
            type="email"
            required
            placeholder="请输入邮箱"
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
          {{ loading ? '注册中...' : '注册' }}
        </button>
        <div class="login-link">
          已有账户？<router-link to="/login">立即登录</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { authApi } from '@/api/auth.js'

export default {
  name: 'Register',
  data() {
    return {
      credentials: {
        username: '',
        email: '',
        password: ''
      },
      loading: false,
      error: null
    }
  },
  methods: {
    async handleRegister() {
      this.loading = true
      this.error = null
      
      try {
        const response = await authApi.register({
          username: this.credentials.username,
          email: this.credentials.email,
          password: this.credentials.password
        })
        
        if (response.data.success) {
          // 注册成功，自动登录
          if (response.data.data.token) {
            localStorage.setItem('token', response.data.data.token)
            this.$router.push('/')
          } else {
            // 如果没有返回 token，跳转到登录页
            this.$router.push('/login')
          }
        } else {
          throw new Error('注册失败')
        }
      } catch (err) {
        console.error('注册错误:', err)
        this.error = err.response?.data?.message || '注册失败，请稍后重试'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.register-form {
  background: white;
  padding: 32px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  width: 100%;
  max-width: 400px;
}

.register-form h2 {
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

.login-link {
  text-align: center;
}

.login-link a {
  color: #3498db;
  text-decoration: none;
}

.login-link a:hover {
  text-decoration: underline;
}
</style>