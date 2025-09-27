import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Detail from '../views/Detail.vue'
import ShareView from '../views/ShareView.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/item/:id', component: Detail, props: true },
  { path: '/share/:token', component: ShareView, props: true }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router