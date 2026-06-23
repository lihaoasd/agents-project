<script setup>
const projectCards = [
  {
    icon: '🏯',
    title: '文化旅行',
    path: '/cultural-travel',
    description: '输入旅行需求，推荐地方、景点、历史文化、路线和内容资源。',
    tags: ['进行中', 'Vue 3', 'FastAPI'],
  },
  {
    icon: '📚',
    title: '未来功能页',
    path: '/',
    description: '预留页面入口，后续可根据项目需要继续扩展。',
    tags: ['预留', '可扩展'],
  },
]
</script>

<template>
  <section class="home-hero">
    <p class="eyebrow">Agent Project Portal</p>
    <h1>文化旅行 Agent 项目首页</h1>
    <p>
      这里作为项目入口，用于规整当前和未来的功能页面。当前已启动“文化旅行”页面，
      后续可以继续添加其他文旅相关功能模块。
    </p>
  </section>

  <section class="project-grid">
    <RouterLink v-for="card in projectCards" :key="card.title" class="project-card" :to="card.path">
      <span class="project-icon">{{ card.icon }}</span>
      <div>
        <h2>{{ card.title }}</h2>
        <p>{{ card.description }}</p>
      </div>
      <div class="tags">
        <span v-for="tag in card.tags" :key="tag">{{ tag }}</span>
      </div>
    </RouterLink>
  </section>

  <section class="panel">
    <p class="eyebrow">Project Structure</p>
    <h2>页面规划</h2>
    <div class="planning-list">
      <div>
        <strong>01</strong>
        <span>首页：项目入口和功能导航</span>
      </div>
      <div>
        <strong>02</strong>
        <span>文化旅行：5 个进度节点的文化旅行 Agent 页面</span>
      </div>
      <div>
        <strong>03</strong>
        <span>未来页面：根据业务需要继续扩展</span>
      </div>
    </div>
  </section>
</template>
