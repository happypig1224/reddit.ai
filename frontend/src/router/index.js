import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Workbench',
    component: () => import('../views/Workbench.vue'),
    meta: { title: '热门讨论' }
  },
  {
    path: '/logs',
    name: 'Logs',
    component: () => import('../views/Logs.vue'),
    meta: { title: '回帖历史记录' }
  },
  // 保持旧路径重定向
  { path: '/accounts', redirect: '/' },
  { path: '/settings', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
