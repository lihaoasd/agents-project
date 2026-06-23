<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  { name: 'home', label: '首页', icon: '🏠', path: '/' },
  { name: 'cultural-travel', label: '文化旅行', icon: '🏯', path: '/cultural-travel' },
]

const themes = [
  { value: 'simple', label: '简约', color: '#64748b' },
  { value: 'blue', label: '蓝色', color: '#2563eb' },
  { value: 'green', label: '绿色', color: '#059669' },
  { value: 'pink', label: '粉色', color: '#db2777' },
]

const currentTheme = ref('simple')
const themeOpen = ref(false)
const activeName = computed(() => route.name)

onMounted(() => {
  currentTheme.value = localStorage.getItem('cultural-travel-theme') || 'simple'
  applyTheme(currentTheme.value, false)
})

function applyTheme(theme, persist = true) {
  currentTheme.value = theme
  if (persist) {
    localStorage.setItem('cultural-travel-theme', theme)
  }
  document.documentElement.dataset.theme = theme
  themeOpen.value = false
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <RouterLink to="/" class="brand">
        <span class="brand-mark">文</span>
        <span>
          <strong>Cultural Travel</strong>
          <small>Agent Project</small>
        </span>
      </RouterLink>

      <nav class="nav-list" aria-label="项目页面导航">
        <RouterLink
          v-for="item in navItems"
          :key="item.name"
          :to="item.path"
          class="nav-item"
          :class="{ active: activeName === item.name }"
        >
          <span>{{ item.icon }}</span>
          <strong>{{ item.label }}</strong>
        </RouterLink>
      </nav>

      <div class="sidebar-footer">
        <span>当前项目</span>
        <strong>文化旅行 Agent</strong>
        <small>后续可扩展更多功能页面</small>
      </div>
    </aside>

    <main class="content">
      <slot />
    </main>

    <div class="theme-fab" :class="{ open: themeOpen }">
      <button class="theme-fab-button" type="button" aria-label="切换主题" @click="themeOpen = !themeOpen">
        <span>🎨</span>
      </button>

      <div v-if="themeOpen" class="theme-menu" role="menu">
        <button
          v-for="theme in themes"
          :key="theme.value"
          type="button"
          role="menuitem"
          :class="{ active: currentTheme === theme.value }"
          @click="applyTheme(theme.value)"
        >
          <span class="theme-dot" :style="{ background: theme.color }" />
          {{ theme.label }}
        </button>
      </div>
    </div>
  </div>
</template>
