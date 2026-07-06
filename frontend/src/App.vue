<template>
  <el-container class="layout">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <span class="logo-icon">S</span>
        <div>
          <div class="logo-title">SanyMES</div>
          <div class="logo-sub">制造执行系统 Demo</div>
        </div>
      </div>
      <el-menu
        :default-active="$route.path"
        router
        background-color="#141b26"
        text-color="#8b95a5"
        active-text-color="#fff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Monitor /></el-icon>
          <span>PCC 控制中心</span>
        </el-menu-item>
        <el-menu-item index="/work-orders">
          <el-icon><Document /></el-icon>
          <span>工单管理</span>
        </el-menu-item>
        <el-menu-item index="/terminal">
          <el-icon><Cellphone /></el-icon>
          <span>MES 终端机</span>
        </el-menu-item>
        <el-menu-item index="/materials">
          <el-icon><Box /></el-icon>
          <span>物料管理</span>
        </el-menu-item>
        <el-menu-item index="/quality">
          <el-icon><CircleCheck /></el-icon>
          <span>质量管理</span>
        </el-menu-item>
      </el-menu>
      <div class="sidebar-footer">
        <div class="factory-badge">18号工厂 · 总装线A</div>
      </div>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <span class="header-title">{{ currentTitle }}</span>
        </div>
        <div class="header-right">
          <el-tag type="success" effect="dark" size="small">系统运行中</el-tag>
          <span class="time">{{ currentTime }}</span>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const currentTime = ref('')
let timer = null

const currentTitle = computed(() => route.meta.title || 'SanyMES')

function updateTime() {
  currentTime.value = new Date().toLocaleString('zh-CN')
}

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
})

onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.layout {
  min-height: 100vh;
}

.sidebar {
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 16px;
  border-bottom: 1px solid var(--border);
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: var(--sany-red);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: 800;
  color: #fff;
}

.logo-title {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
}

.logo-sub {
  font-size: 11px;
  color: var(--text-muted);
}

.sidebar-footer {
  margin-top: auto;
  padding: 16px;
}

.factory-badge {
  background: #1e3a5f;
  color: #60a5fa;
  font-size: 12px;
  padding: 8px 12px;
  border-radius: 6px;
  text-align: center;
}

.header {
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px !important;
  padding: 0 24px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.time {
  font-size: 13px;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

.main {
  background: var(--bg-dark);
  padding: 24px;
  min-height: calc(100vh - 56px);
}

:deep(.el-menu) {
  border-right: none;
}

:deep(.el-menu-item.is-active) {
  background: rgba(230, 0, 18, 0.15) !important;
  border-right: 3px solid var(--sany-red);
}
</style>
