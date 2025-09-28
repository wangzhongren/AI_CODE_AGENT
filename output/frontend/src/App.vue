<template>
  <div class="app-container">
    <header class="app-header" v-if="!isLoginPage">
      <h1>知识库</h1>
      <nav v-if="isAuthenticated">
        <router-link to="/">列表</router-link>
        <router-link to="/create">新建</router-link>
        <button @click="logout" class="logout-btn">登出</button>
      </nav>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script>
import { authApi } from '@/api/auth.js'

export default {
  name: 'App',
  computed: {
    isAuthenticated() {
      return !!localStorage.getItem('token')
    },
    isLoginPage() {
      return this.$route.path === '/login'
    }
  },
  methods: {
    logout() {
      authApi.logout()
      this.$router.push('/login')
    }
  }
}
</script>

<style scoped>
.app-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.app-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #2c3e50;
}

.app-header nav a {
  margin-left: 20px;
  text-decoration: none;
  color: #3498db;
}

.app-header nav a:hover {
  text-decoration: underline;
}

.logout-btn {
  margin-left: 20px;
  padding: 4px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  color: #e74c3c;
  cursor: pointer;
  font-size: 14px;
}

.logout-btn:hover {
  background-color: #f5f5f5;
  border-color: #bbb;
}
</style>