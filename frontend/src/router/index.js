import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import CulturalTravelView from '../views/CulturalTravelView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { title: '首页' },
  },
  {
    path: '/cultural-travel',
    name: 'cultural-travel',
    component: CulturalTravelView,
    meta: { title: '文化旅行' },
  },
  {
    path: '/debate',
    name: 'debate-setup',
    component: () => import('../views/debate/DebateSetupView.vue'),
    meta: { title: '多Agent辩论' },
  },
  {
    path: '/debate/:sessionId',
    name: 'debate-chat',
    component: () => import('../views/debate/DebateChatView.vue'),
    props: true,
    meta: { title: '辩论中' },
  },
  {
    path: '/debate/:sessionId/result',
    name: 'debate-result',
    component: () => import('../views/debate/DebateResultView.vue'),
    props: true,
    meta: { title: '辩论结果' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  document.title = `${to.meta.title || '文化旅行 Agent'} · Cultural Travel Agent`
})

export default router
