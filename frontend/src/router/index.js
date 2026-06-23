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
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  document.title = `${to.meta.title || '文化旅行 Agent'} · Cultural Travel Agent`
})

export default router
