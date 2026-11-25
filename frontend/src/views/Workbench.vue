<template>
  <div class="workbench-page">
    <!-- 顶部状态栏与核心控制 -->
    <div class="top-action-bar">
      <div class="bar-left">
        <h2 class="page-title">Reddit 热门讨论</h2>
        <span class="page-subtitle">
          实时监测高互动潜力帖子，提供符合在地表达习惯的英文回复建议，支持一键直达原帖
        </span>
      </div>

      <div class="bar-right">
        <el-button
          type="primary"
          :icon="RefreshRight"
          :loading="isRefreshing"
          @click="handleFetchNewPosts"
          class="refresh-btn"
        >
          抓取最新帖子
        </el-button>
      </div>
    </div>

    <!-- 自定义链接 / 标题回复生成器 -->
    <div class="custom-query-box">
      <el-input
        v-model="customInput"
        placeholder="粘贴 Reddit 帖子链接或输入英文标题，如 https://www.reddit.com/r/AskReddit/comments/..."
        clearable
        size="large"
        class="custom-query-input"
        @keyup.enter="handleCustomGenerate"
      >
        <template #prefix>
          <el-icon class="input-search-icon"><Search /></el-icon>
        </template>
      </el-input>
      <el-button
        type="primary"
        size="large"
        :loading="isCustomGenerating"
        :icon="EditPen"
        @click="handleCustomGenerate"
        class="custom-generate-btn"
      >
        生成回复建议
      </el-button>
    </div>

    <!-- 社区筛选与排序 -->
    <div class="filter-bar-wrap">
      <div class="filter-group-left">
        <span class="filter-label">社区:</span>
        <div class="sub-filter-pills">
          <button
            class="filter-pill-btn"
            :class="{ active: filterSubreddit === 'ALL' }"
            @click="filterSubreddit = 'ALL'"
          >
            全部 ({{ store.candidatePosts.filter(p => p.status === 'PENDING').length }})
          </button>
          <button
            v-for="sub in enabledSubreddits"
            :key="sub"
            class="filter-pill-btn"
            :class="{ active: filterSubreddit === sub }"
            @click="filterSubreddit = sub"
          >
            {{ sub }}
          </button>
        </div>
      </div>

      <div class="filter-group-right">
        <span class="filter-label">排序:</span>
        <el-select v-model="sortBy" style="width: 130px" size="small" class="sort-select">
          <el-option label="推荐分最高" value="SCORE_DESC" />
          <el-option label="互动潜力优先" value="COMMENTS_ASC" />
        </el-select>
      </div>
    </div>

    <!-- 帖子卡片列表 -->
    <div v-if="filteredPosts.length > 0" class="post-feed">
      <div
        v-for="post in filteredPosts"
        :key="post.id"
        class="post-card"
      >
        <!-- 头部信息 -->
        <div class="post-header">
          <div class="post-meta">
            <span class="sub-pill">{{ post.subreddit }}</span>
            <span class="meta-dot">·</span>
            <span class="author-text">u/{{ post.author }}</span>
            <span class="meta-dot">·</span>
            <span class="time-text">{{ post.createdTimeStr }}</span>
            <span class="meta-dot">·</span>
            <span class="stats-badge">
              <el-icon><ChatLineRound /></el-icon>
              <span>{{ post.numComments }} 评论</span>
            </span>
            <span class="meta-dot">·</span>
            <span class="stats-badge">
              <el-icon><Top /></el-icon>
              <span>{{ post.upvotes }} 赞</span>
            </span>
          </div>

          <div class="score-badge">
            <span class="score-label">潜力指数</span>
            <span class="score-val">{{ post.opportunityScore }}</span>
          </div>
        </div>

        <!-- 帖子标题与直达链接 -->
        <div class="post-body">
          <h3 class="post-title">
            <a :href="post.url" target="_blank" class="post-link" title="在 Reddit 打开原帖">
              <span>{{ post.title }}</span>
              <el-icon class="external-icon"><TopRight /></el-icon>
            </a>
          </h3>
          <p v-if="post.summary && post.summary !== post.title" class="post-summary">{{ post.summary }}</p>
        </div>

        <!-- 回复建议生成区 -->
        <div class="draft-workspace">
          <div class="draft-toolbar">
            <div class="tone-selector">
              <span class="draft-label">回复风格:</span>
              <div class="tone-pills">
                <button
                  v-for="(draft, dIdx) in post.drafts"
                  :key="dIdx"
                  type="button"
                  class="tone-pill-btn"
                  :class="{ active: (post.selectedDraftIndex || 0) === dIdx }"
                  @click="selectDraft(post, dIdx)"
                >
                  {{ formatTone(draft.tone) }}
                </button>
              </div>
            </div>

            <div class="draft-badge-tip">
              <span class="tone-hint">原生口语习惯</span>
            </div>
          </div>

          <!-- 可编辑的英文评论草稿框 -->
          <div class="draft-editor-box">
            <el-input
              type="textarea"
              :rows="3"
              :model-value="currentDraft(post).text"
              @update:model-value="(val) => store.updateDraftText(post.id, val)"
              placeholder="评论草稿..."
              resize="none"
              class="draft-textarea"
            />
          </div>

          <!-- 底部操作按钮 -->
          <div class="card-footer-actions">
            <el-button
              size="small"
              class="skip-btn"
              @click="handleSkip(post.id)"
            >
              跳过此帖
            </el-button>

            <el-button
              type="primary"
              class="copy-open-btn"
              @click="handleCopyAndOpen(post)"
            >
              <el-icon class="btn-action-icon"><DocumentCopy /></el-icon>
              <span>复制回复并打开原帖</span>
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-box">
      <el-empty description="当前分类下暂无待处理帖子，点击刷新重新抓取" :image-size="90">
        <el-button type="primary" :icon="RefreshRight" @click="handleFetchNewPosts">
          抓取最新帖子
        </el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  DocumentCopy,
  TopRight,
  ChatLineRound,
  Top,
  Search,
  EditPen,
  RefreshRight
} from '@element-plus/icons-vue'
import { useKarmaStore } from '../stores/karmaStore'
import { ElMessage, ElNotification } from 'element-plus'

const store = useKarmaStore()

const filterSubreddit = ref('ALL')
const sortBy = ref('SCORE_DESC')
const isRefreshing = ref(false)

const customInput = ref('')
const isCustomGenerating = ref(false)

// 提取当前帖子涉及的社区列表
const enabledSubreddits = computed(() => {
  const subs = new Set()
  store.candidatePosts.forEach(p => {
    if (p.subreddit) subs.add(p.subreddit)
  })
  return Array.from(subs)
})

const filteredPosts = computed(() => {
  let list = store.candidatePosts.filter(p => p.status === 'PENDING')
  
  if (filterSubreddit.value !== 'ALL') {
    list = list.filter(p => p.subreddit === filterSubreddit.value)
  }

  if (sortBy.value === 'SCORE_DESC') {
    list.sort((a, b) => b.opportunityScore - a.opportunityScore)
  } else if (sortBy.value === 'COMMENTS_ASC') {
    list.sort((a, b) => a.numComments - b.numComments)
  }

  return list
})

const formatTone = (tone) => {
  if (!tone) return '常规回复'
  return tone.replace('神评', '风趣')
}

const currentDraft = (post) => {
  if (!post.drafts || post.drafts.length === 0) {
    return { tone: '生活经验', text: '' }
  }
  const idx = post.selectedDraftIndex || 0
  return post.drafts[idx] || post.drafts[0]
}

const selectDraft = (post, idx) => {
  post.selectedDraftIndex = idx
}

const handleSkip = async (postId) => {
  await store.skipPost(postId, '人工跳过')
  ElMessage.info('已跳过该帖子')
}

const handleCopyAndOpen = async (post) => {
  const text = currentDraft(post).text.trim()
  if (!text) {
    return ElMessage.warning('草稿内容为空')
  }

  // 1. 复制文案至系统剪贴板
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text)
    } else {
      const ta = document.createElement('textarea')
      ta.value = text
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
    }
  } catch (e) {
    console.warn('Clipboard write error', e)
  }

  // 2. 在新标签页打开真实 Reddit 原帖
  const targetUrl = post.url || (post.permalink ? (post.permalink.startsWith('http') ? post.permalink : `https://reddit.com${post.permalink}`) : null)
  if (targetUrl) {
    window.open(targetUrl, '_blank')
  }

  // 3. 记录打卡状态并更新本地
  post.status = 'SENT'
  await store.recordManualSent(post.id)

  // 4. 通知
  ElNotification({
    title: '已复制回复文案',
    message: '英文回复已存入剪贴板，原帖已在新标签页打开，可直接粘贴回复。',
    type: 'success',
    duration: 4000
  })
}

const handleCustomGenerate = async () => {
  const val = customInput.value.trim()
  if (!val) {
    return ElMessage.warning('请输入 Reddit 帖子标题或链接')
  }

  isCustomGenerating.value = true
  const res = await store.generateCustomDrafts({
    title: val.startsWith('http') ? '' : val,
    url: val.startsWith('http') ? val : '',
    subreddit: 'r/AskReddit'
  })
  isCustomGenerating.value = false

  if (res.success) {
    customInput.value = ''
    ElMessage.success('已生成 3 种风格的回复建议')
  } else {
    ElMessage.error(res.msg || '生成失败')
  }
}

const handleFetchNewPosts = async () => {
  isRefreshing.value = true
  try {
    if (store && typeof store.refreshPosts === 'function') {
      await store.refreshPosts()
    } else {
      await store.fetchInitialData()
    }
    ElMessage.success('已更新最新热门讨论与回复建议')
  } catch (err) {
    console.error('Fetch posts error', err)
    try {
      await store.fetchInitialData()
      ElMessage.success('已更新最新热门讨论与回复建议')
    } catch (e) {
      ElMessage.error('网络连接异常，请按 F5 刷新页面后重试')
    }
  } finally {
    isRefreshing.value = false
  }
}
</script>

<style scoped>
.workbench-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 1080px;
  margin: 0 auto;
}

/* 顶部操作区 */
.top-action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
  line-height: 1.25;
}

.page-subtitle {
  font-size: 13px;
  color: #64748b;
  margin-top: 4px;
  display: block;
}

.refresh-btn {
  background-color: #0f172a;
  border-color: #0f172a;
  color: #ffffff;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.15s ease;
}

.refresh-btn:hover {
  background-color: #1e293b;
  border-color: #1e293b;
}

/* 自定义输入框 */
.custom-query-box {
  display: flex;
  gap: 10px;
  background: #ffffff;
  padding: 6px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
}

.custom-query-input {
  flex: 1;
}

.custom-query-input :deep(.el-input__wrapper) {
  box-shadow: none !important;
  background: transparent;
  padding-left: 8px;
}

.custom-query-input :deep(.el-input__inner) {
  font-size: 13.5px;
  color: #0f172a;
}

.input-search-icon {
  font-size: 16px;
  color: #94a3b8;
}

.custom-generate-btn {
  background-color: #ea580c;
  border-color: #ea580c;
  color: #ffffff;
  font-weight: 500;
  border-radius: 8px;
  padding: 0 18px;
  transition: all 0.15s ease;
}

.custom-generate-btn:hover {
  background-color: #c2410c;
  border-color: #c2410c;
}

/* 筛选与排序 */
.filter-bar-wrap {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 2px 0;
}

.filter-group-left,
.filter-group-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 12.5px;
  color: #64748b;
  font-weight: 600;
}

.sub-filter-pills {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.filter-pill-btn {
  border: 1px solid #e2e8f0;
  background-color: #ffffff;
  color: #64748b;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.filter-pill-btn:hover {
  background-color: #f8fafc;
  color: #0f172a;
  border-color: #cbd5e1;
}

.filter-pill-btn.active {
  background-color: #0f172a;
  border-color: #0f172a;
  color: #ffffff;
  font-weight: 600;
}

/* 风格药丸 */
.tone-pills {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tone-pill-btn {
  border: 1px solid #e2e8f0;
  background-color: #ffffff;
  color: #64748b;
  font-size: 11.5px;
  font-weight: 500;
  padding: 4px 10px;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.tone-pill-btn:hover {
  background-color: #f1f5f9;
  color: #0f172a;
}

.tone-pill-btn.active {
  background-color: #0f172a;
  border-color: #0f172a;
  color: #ffffff;
  font-weight: 600;
}

/* 帖子流 */
.post-feed {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.post-card {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background-color: #ffffff;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
  transition: all 0.2s ease;
}

.post-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 6px 16px -2px rgba(0, 0, 0, 0.05);
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.post-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12.5px;
  color: #64748b;
}

.sub-pill {
  background-color: #fff7ed;
  color: #ea580c;
  font-weight: 600;
  font-size: 11.5px;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid #ffedd5;
}

.meta-dot {
  color: #cbd5e1;
}

.author-text {
  color: #475569;
  font-weight: 500;
}

.time-text {
  color: #94a3b8;
}

.stats-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #64748b;
  font-size: 12px;
}

.score-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: #f1f5f9;
  border-radius: 6px;
  padding: 3px 9px;
  font-size: 11.5px;
  border: 1px solid #e2e8f0;
}

.score-label {
  color: #64748b;
  font-weight: 500;
}

.score-val {
  color: #0f172a;
  font-weight: 700;
}

.post-body {
  margin: 6px 0 16px 0;
}

.post-title {
  margin: 0;
  font-size: 16.5px;
  font-weight: 600;
  line-height: 1.45;
  color: #0f172a;
}

.post-link {
  color: #0f172a;
  text-decoration: none;
  display: inline-flex;
  align-items: baseline;
  gap: 5px;
  transition: color 0.15s ease;
}

.post-link:hover {
  color: #ea580c;
}

.external-icon {
  font-size: 13px;
  color: #94a3b8;
  transform: translateY(1px);
}

.post-summary {
  font-size: 13.5px;
  color: #475569;
  margin: 8px 0 0 0;
  line-height: 1.55;
}

/* 回复建议区域 */
.draft-workspace {
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 14px;
}

.draft-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.tone-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.draft-label {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
}



.tone-hint {
  font-size: 11.5px;
  color: #94a3b8;
  font-weight: 500;
}

.draft-editor-box {
  margin-bottom: 10px;
}

.draft-textarea :deep(.el-textarea__inner) {
  font-size: 13.5px;
  line-height: 1.6;
  color: #1e293b;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  border-color: #cbd5e1;
  border-radius: 6px;
  background-color: #ffffff;
  padding: 10px 12px;
}

.draft-textarea :deep(.el-textarea__inner:focus) {
  border-color: #ea580c;
  box-shadow: 0 0 0 1px #ea580c;
}

.card-footer-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.skip-btn {
  background-color: transparent;
  border: 1px solid #cbd5e1;
  color: #64748b;
  border-radius: 6px;
  font-size: 12px;
  transition: all 0.15s ease;
}

.skip-btn:hover {
  background-color: #f1f5f9;
  color: #0f172a;
  border-color: #94a3b8;
}

.copy-open-btn {
  background-color: #ea580c;
  border-color: #ea580c;
  font-weight: 600;
  border-radius: 6px;
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  transition: all 0.15s ease;
}

.copy-open-btn:hover {
  background-color: #c2410c;
  border-color: #c2410c;
}

.btn-action-icon {
  font-size: 14px;
}

.empty-box {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  padding: 48px 24px;
  text-align: center;
}
</style>
