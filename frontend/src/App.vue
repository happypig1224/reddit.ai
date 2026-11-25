<template>
  <el-container class="layout-container">
    <!-- 左侧极简侧边栏导航 -->
    <el-aside width="220px" class="aside-nav">
      <div class="brand-box">
        <div class="brand-logo">
          <svg viewBox="0 0 20 20" width="18" height="18" fill="none">
            <circle cx="10" cy="10" r="10" fill="#ea580c"/>
            <path d="M16.67 10a1.46 1.46 0 00-2.47-1.05 7.12 7.12 0 00-3.85-1.23l.65-3.08 2.13.45a1.03 1.03 0 101.07-1 1.03 1.03 0 00-1 .73l-2.39-.51a.22.22 0 00-.26.17l-.76 3.56a7.17 7.17 0 00-3.9 1.22 1.46 1.46 0 10-1.62 2.37c-.01.12-.02.25-.02.37 0 2.45 2.53 4.45 5.66 4.45s5.66-2 5.66-4.45c0-.12-.01-.25-.02-.37a1.45 1.45 0 00.74-1.62zm-9.35.82a.89.89 0 11.89.89.89.89 0 01-.89-.89zm5.37 2.87a3.4 3.4 0 01-4.38 0 .2.2 0 01.27-.29 3 3 0 003.84 0 .2.2 0 01.27.29zm-.25-2a.89.89 0 11.89-.89.89.89 0 01-.89.89z" fill="#FFF"/>
          </svg>
        </div>
        <div class="brand-text">
          <span class="brand-title">Reddit Pilot</span>
          <span class="brand-sub">内容与互动工作台</span>
        </div>
      </div>

      <el-menu
        :default-active="$route.path"
        router
        class="custom-menu"
        background-color="transparent"
        text-color="#94a3b8"
        active-text-color="#ffffff"
      >
        <el-menu-item index="/">
          <el-icon><Compass /></el-icon>
          <span>热门讨论</span>
        </el-menu-item>

        <el-menu-item index="/logs">
          <el-icon><Clock /></el-icon>
          <span>历史记录</span>
        </el-menu-item>
      </el-menu>

      <!-- 侧边栏底部精简状态 -->
      <div class="aside-footer">
        <div class="status-indicator-clean">
          <span class="status-dot-pulse"></span>
          <span class="status-clean-text">服务正常运行</span>
        </div>
      </div>
    </el-aside>

    <!-- 右侧主体内容 -->
    <el-container class="main-layout">
      <!-- 顶部精简导航条 -->
      <el-header height="52px" class="top-header">
        <div class="header-left">
          <span class="header-view-title">{{ currentRouteTitle }}</span>
        </div>

        <div class="header-right">
          <el-button
            size="small"
            class="header-refresh-btn"
            :loading="isRefreshing"
            @click="handleManualRefresh"
          >
            <el-icon class="btn-icon"><Refresh /></el-icon>
            <span>刷新数据</span>
          </el-button>
        </div>
      </el-header>

      <!-- 视图呈现区域 -->
      <el-main class="content-view">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Compass, Clock, Refresh } from '@element-plus/icons-vue'
import { useKarmaStore } from './stores/karmaStore'
import { ElMessage } from 'element-plus'

const store = useKarmaStore()
const isRefreshing = ref(false)

onMounted(async () => {
  await store.fetchInitialData()
})

const route = useRoute()

const currentRouteTitle = computed(() => {
  return route.meta?.title || '热门讨论与回复'
})

const handleManualRefresh = async () => {
  isRefreshing.value = true
  await store.fetchInitialData()
  isRefreshing.value = false
  ElMessage.success('数据已更新')
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  display: flex;
  background-color: #f8fafc;
}

.aside-nav {
  background-color: #0b0f19;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #1e293b;
  user-select: none;
}

.brand-box {
  padding: 18px 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.brand-logo {
  width: 28px;
  height: 28px;
  border-radius: 7px;
  background-color: rgba(234, 88, 12, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.brand-text {
  display: flex;
  flex-direction: column;
}

.brand-title {
  color: #f8fafc;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.brand-sub {
  color: #64748b;
  font-size: 11px;
  margin-top: 1px;
}

.custom-menu {
  border-right: none;
  flex: 1;
  padding: 12px 8px;
}

.custom-menu :deep(.el-menu-item) {
  margin: 3px 0;
  border-radius: 8px;
  height: 40px;
  line-height: 40px;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
}

.custom-menu :deep(.el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.05) !important;
  color: #e2e8f0 !important;
}

.custom-menu :deep(.el-menu-item.is-active) {
  background-color: #1e293b !important;
  color: #ffffff !important;
  font-weight: 600;
}

.custom-menu :deep(.el-menu-item.is-active .el-icon) {
  color: #ea580c !important;
}

.aside-footer {
  padding: 14px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  background-color: #080c14;
}

.status-indicator-clean {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot-pulse {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #10b981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
}

.status-clean-text {
  font-size: 11.5px;
  color: #64748b;
  font-weight: 500;
}

.main-layout {
  display: flex;
  flex-direction: column;
  background-color: #f8fafc;
  height: 100vh;
  overflow: hidden;
}

.top-header {
  background-color: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-view-title {
  font-size: 14.5px;
  font-weight: 600;
  color: #0f172a;
  letter-spacing: -0.01em;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-refresh-btn {
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  color: #475569;
  border-radius: 6px;
  font-weight: 500;
  font-size: 12.5px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  transition: all 0.15s ease;
}

.header-refresh-btn:hover {
  border-color: #cbd5e1;
  color: #0f172a;
  background-color: #f8fafc;
}

.btn-icon {
  font-size: 13px;
}

.content-view {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background-color: #f8fafc;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.12s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
