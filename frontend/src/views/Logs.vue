<template>
  <div class="logs-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">历史记录</h2>
        <span class="page-subtitle">
          查看已处理、复制并直达原帖的讨论与回复记录
        </span>
      </div>

      <div class="header-btns">
        <el-button size="small" :icon="Download" @click="exportLogs" class="action-btn">
          导出记录
        </el-button>
        <el-button size="small" type="default" :icon="Delete" @click="clearLogs" class="action-btn">
          清空记录
        </el-button>
      </div>
    </div>

    <!-- 过滤器与统计 -->
    <div class="filter-card">
      <div class="filter-bar">
        <div class="filter-item">
          <span class="label">状态筛选:</span>
          <el-select v-model="statusFilter" size="small" style="width: 140px;" class="status-select">
            <el-option label="全部记录" value="ALL" />
            <el-option label="已复制直达" value="SUCCESS" />
            <el-option label="已跳过" value="SKIPPED" />
            <el-option label="已拦截" value="BLOCKED" />
          </el-select>
        </div>

        <div class="summary-pills">
          <span class="pill-item">总记录: <strong>{{ store.logs.length }}</strong></span>
          <span class="pill-item text-green">已复制发出: <strong>{{ successCount }}</strong></span>
          <span class="pill-item text-gray">已跳过: <strong>{{ skippedCount }}</strong></span>
        </div>
      </div>
    </div>

    <!-- 历史表格 -->
    <div class="table-card">
      <el-table :data="filteredLogs" style="width: 100%" stripe class="standard-table">
        <el-table-column label="时间" prop="timestamp" width="165" />

        <el-table-column label="社区" width="160">
          <template #default="{ row }">
            <span class="sub-badge">{{ row.subreddit }}</span>
          </template>
        </el-table-column>

        <el-table-column label="帖子标题与回复预览" min-width="280">
          <template #default="{ row }">
            <div class="post-log-cell">
              <span class="post-title">{{ row.postTitle }}</span>
              <p v-if="row.commentSnippet && row.commentSnippet !== '---'" class="comment-quote">
                “{{ row.commentSnippet }}”
              </p>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag
              size="small"
              :type="row.status === 'SUCCESS' ? 'success' : row.status === 'SKIPPED' ? 'info' : 'danger'"
              class="status-tag"
            >
              {{ row.status === 'SUCCESS' ? '已复制直达' : row.status === 'SKIPPED' ? '已跳过' : '已拦截' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="原帖" width="110" align="center">
          <template #default="{ row }">
            <el-button
              v-if="row.postId"
              type="primary"
              link
              size="small"
              @click="openRedditPost(row)"
            >
              打开原帖
            </el-button>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="暂无历史记录，可在热门讨论工作台开始浏览回复" :image-size="80" />
        </template>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useKarmaStore } from '../stores/karmaStore'
import { ElMessage } from 'element-plus'
import { Download, Delete } from '@element-plus/icons-vue'

const store = useKarmaStore()

const statusFilter = ref('ALL')

const filteredLogs = computed(() => {
  if (statusFilter.value === 'ALL') return store.logs
  return store.logs.filter(l => l.status === statusFilter.value)
})

const successCount = computed(() => store.logs.filter(l => l.status === 'SUCCESS').length)
const skippedCount = computed(() => store.logs.filter(l => l.status === 'SKIPPED').length)

const openRedditPost = (row) => {
  if (row.postId) {
    const url = `https://reddit.com/r/${row.subreddit}/comments/${row.postId}`
    window.open(url, '_blank')
  }
}

const exportLogs = () => {
  const jsonStr = JSON.stringify(store.logs, null, 2)
  const blob = new Blob([jsonStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `reddit_logs_${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('已导出记录文件')
}

const clearLogs = async () => {
  const res = await store.clearLogs()
  if (res.success) {
    ElMessage.info('记录已清空')
  } else {
    ElMessage.error(res.msg || '清空失败')
  }
}
</script>

<style scoped>
.logs-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 1080px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.page-subtitle {
  font-size: 13px;
  color: #64748b;
  margin-top: 4px;
  display: block;
}

.header-btns {
  display: flex;
  gap: 8px;
}

.action-btn {
  border-radius: 6px;
  font-size: 12.5px;
}

.filter-card {
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background-color: #ffffff;
  padding: 14px 18px;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-item .label {
  font-size: 12.5px;
  color: #64748b;
  font-weight: 500;
}

.summary-pills {
  display: flex;
  gap: 16px;
  font-size: 12.5px;
  color: #475569;
}

.pill-item strong {
  color: #0f172a;
  font-weight: 600;
}

.text-green strong {
  color: #10b981;
}

.text-gray strong {
  color: #94a3b8;
}

.table-card {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background-color: #ffffff;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.standard-table :deep(th.el-table__cell) {
  background-color: #f8fafc;
  color: #475569;
  font-size: 12.5px;
  font-weight: 600;
  border-bottom: 1px solid #e2e8f0;
  padding: 10px 0;
}

.standard-table :deep(td.el-table__cell) {
  border-bottom: 1px solid #f1f5f9;
  padding: 12px 0;
  font-size: 13px;
}

.sub-badge {
  background-color: #fff7ed;
  color: #ea580c;
  font-weight: 600;
  font-size: 11.5px;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid #ffedd5;
  display: inline-block;
}

.post-log-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.post-title {
  font-size: 13.5px;
  font-weight: 600;
  color: #0f172a;
  line-height: 1.4;
}

.comment-quote {
  font-size: 12.5px;
  color: #64748b;
  line-height: 1.5;
  font-style: italic;
  margin: 0;
}

.status-tag {
  font-size: 11px;
  font-weight: 500;
}

.text-gray {
  color: #cbd5e1;
}
</style>
