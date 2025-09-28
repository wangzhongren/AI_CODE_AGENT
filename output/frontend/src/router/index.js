import { createRouter, createWebHistory } from 'vue-router'
import ArticleList from '../views/ArticleList.vue'
import ArticleDetail from '../views/ArticleDetail.vue'
import ArticleCreate from '../views/ArticleCreate.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'

const routes = [
  { path: '/login', component: Login, name: 'Login' },
  { path: '/register', component: Register, name: 'Register' },
  { path: '/', component: ArticleList, meta: { requiresAuth: true } },
  { path: '/articles/:id', component: ArticleDetail, props: true, meta: { requiresAuth: true } },
  { path: '/create', component: ArticleCreate, meta: { requiresAuth: true } },
  { path: '/edit/:id', component: ArticleCreate, props: true, meta: { requiresAuth: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫 - 检查认证状态
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  
  if (requiresAuth && !token) {
    // 需要认证但没有 token，跳转到登录页
    next('/login')
  } else if ((to.path === '/login' || to.path === '/register') && token) {
    // 已登录用户访问登录/注册页，跳转到首页
    next('/')
  } else {
    next()
  }
})

export default router