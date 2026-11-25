import { defineStore } from 'pinia'
import axios from 'axios'

// 配置后端 API 客户端 (基于 Vite 代理 /api -> http://127.0.0.1:8001)
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 自适应延迟显示
export const formatDuration = (seconds) => {
  if (!seconds || seconds <= 0) return '0秒'
  if (seconds < 60) return `${seconds}秒`
  return `${Math.round(seconds / 60)}分钟`
}

export const useKarmaStore = defineStore('karma', {
  state: () => ({
    isBackendConnected: false,
    currentAccountId: null,
    // 生产模式：初始状态必须为干净的空数组，全部由后端数据库真实驱动
    accounts: [],

    // 账号阶段通用定义
    stages: [
      {
        id: 'STAGE_1',
        name: '冷启动期 (1-3天)',
        targetComments: '0条 / 日',
        description: '仅允许浏览与点赞，避免新号发帖触发风控。',
        maxDaily: 0,
        allowLinks: false
      },
      {
        id: 'STAGE_2',
        name: '破冰期 (4-7天)',
        targetComments: '2-5条 / 日',
        description: '在问答板块回复日常话题积累 Karma，禁止携带外链。',
        maxDaily: 5,
        allowLinks: false
      },
      {
        id: 'STAGE_3',
        name: '成长期 (8-14天)',
        targetComments: '3-8条 / 日',
        description: '参与技术与兴趣板块讨论，禁止营销引流。',
        maxDaily: 8,
        allowLinks: false
      },
      {
        id: 'STAGE_4',
        name: '稳定期 (Karma 100+)',
        targetComments: '5-10条 / 日',
        description: '可参与垂直社区讨论，受限添加外链。',
        maxDaily: 10,
        allowLinks: true
      }
    ],

    // 目标社区池 (纯后端真实数据)
    subreddits: [],

    // 候选待审帖子流 (纯后端真实爬取数据)
    candidatePosts: [],

    // 模板库 (纯后端真实数据)
    templates: [],

    // 风控全局配置
    riskSettings: {
      maxDailyGlobal: 5,
      maxDailyPerSubreddit: 2,
      minDelayMinutes: 5,
      maxDelayMinutes: 30,
      blacklistedKeywords: [
        'http://', 'https://', 'www.', '.com', '.io', '.ai',
        'whatsapp', 'telegram', 't.me', 'wa.me', 'wechat', '微信',
        'coupon', 'discount', 'dm me', 'check my bio', 'promo code'
      ],
      circuitBreakerActive: false,
      circuitBreakerReason: '',
      autoDetectShadowban: true,
      randomJitterEnabled: true
    },

    // 执行与审计流水 (纯后端真实物理日志)
    logs: []
  }),

  getters: {
    currentAccount(state) {
      if (!state.accounts || state.accounts.length === 0) return null
      return state.accounts.find(a => a.id === state.currentAccountId) || state.accounts[0] || null
    },
    currentStageInfo(state) {
      const acc = this.currentAccount
      if (!acc) return state.stages[0]
      return state.stages.find(s => s.id === acc.stage) || state.stages[0]
    },
    pendingPosts(state) {
      return state.candidatePosts.filter(p => p.status === 'PENDING')
    }
  },

  actions: {
    // ------------------------------------------------------------------
    // 全量异步初始化：对接 FastAPI /api/v1 (No Mock Fallback)
    // ------------------------------------------------------------------
    async fetchInitialData() {
      try {
        const [accRes, candRes, subRes, tmplRes, riskRes, logRes] = await Promise.allSettled([
          api.get('/accounts'),
          api.get('/workbench/candidates?status=PENDING&limit=20'),
          api.get('/subreddits'),
          api.get('/templates'),
          api.get('/risk-control/settings'),
          api.get('/logs?page=1&pageSize=50')
        ])

        // 1. 账号列表
        if (accRes.status === 'fulfilled' && accRes.value.data.code === 200) {
          const accList = accRes.value.data.data || []
          this.accounts = accList
          if (accList.length > 0) {
            if (!this.accounts.some(a => a.id === this.currentAccountId)) {
              this.currentAccountId = this.accounts[0].id
            }
          } else {
            this.currentAccountId = null
          }
        }

        // 2. 待审候选帖
        if (candRes.status === 'fulfilled' && candRes.value.data.code === 200) {
          const candidates = candRes.value.data.data || []
          this.candidatePosts = candidates.map(c => ({
            id: c.id,
            numericId: c.id,
            redditPostId: c.redditPostId,
            subreddit: c.subreddit,
            title: c.title,
            author: c.author || 'reddit_user',
            createdTimeStr: c.createdAgo || '刚刚',
            url: c.permalink || `https://reddit.com/${c.subreddit}/comments/${c.redditPostId}`,
            numComments: c.numComments,
            upvotes: c.score,
            opportunityScore: c.recommendedScore,
            scoreBreakdown: {
              recency: c.createdAgo || '近期抓取',
              sweetSpot: `${c.numComments}条评论，黄金互动窗口`,
              keywordMatch: c.recommendedReason || '求助信号'
            },
            matchedKeyword: c.matchKeyword || 'recommend',
            summary: c.content || c.title,
            status: c.status,
            selectedDraftIndex: 0,
            drafts: c.drafts && c.drafts.length > 0 ? c.drafts : [
              {
                tone: '生活经验',
                text: c.draftComment || ''
              }
            ]
          }))
        } else {
          this.candidatePosts = []
        }

        // 3. 目标社区池
        if (subRes.status === 'fulfilled' && subRes.value.data.code === 200) {
          const subs = subRes.value.data.data || []
          this.subreddits = subs.map(s => ({
            id: s.id,
            name: s.name,
            minKarma: s.minKarma,
            dailyLimit: s.dailyLimit,
            todaySent: s.todaySent,
            enabled: s.isEnabled,
            badge: s.badge,
            description: s.description
          }))
        } else {
          this.subreddits = []
        }

        // 4. 回复模板库
        if (tmplRes.status === 'fulfilled' && tmplRes.value.data.code === 200) {
          const tmpls = tmplRes.value.data.data || []
          this.templates = tmpls.map(t => ({
            id: t.id,
            category: t.tone,
            title: `${t.tone}回复模板`,
            content: t.templateText,
            usageCount: t.usageCount,
            suitableFor: t.tone,
            isCoolingDown: t.isCoolingDown
          }))
        } else {
          this.templates = []
        }

        // 5. 风控配置
        if (riskRes.status === 'fulfilled' && riskRes.value.data.code === 200) {
          const r = riskRes.value.data.data
          this.riskSettings.minDelayMinutes = r.minDelayMinutes
          this.riskSettings.maxDelayMinutes = r.maxDelayMinutes
          this.riskSettings.maxDailyGlobal = r.maxDailyCommentsPerAccount
          this.riskSettings.maxDailyPerSubreddit = r.maxDailyCommentsPerSub
          this.riskSettings.circuitBreakerActive = r.circuitBreakerActive
          this.riskSettings.circuitBreakerReason = r.circuitBreakerReason || ''
          if (r.sensitiveKeywords && r.sensitiveKeywords.length > 0) {
            this.riskSettings.blacklistedKeywords = r.sensitiveKeywords
          }
        }

        // 6. 执行审计日志
        if (logRes.status === 'fulfilled' && logRes.value.data.code === 200) {
          const logs = logRes.value.data.data || []
          this.logs = logs.map(l => ({
            id: l.id,
            timestamp: new Date(l.createdAt).toLocaleString('zh-CN'),
            account: l.accountUsername,
            subreddit: l.subreddit,
            postId: l.redditPostId,
            postTitle: l.postTitle,
            commentSnippet: l.commentSnippet,
            delaySeconds: l.delaySeconds,
            status: l.status,
            shadowbanStatus: l.shadowbanStatus,
            details: l.status === 'SUCCESS' ? `安全调度延迟 ${formatDuration(l.delaySeconds)}` : '被系统拦截'
          }))
        } else {
          this.logs = []
        }

        this.isBackendConnected = true
      } catch (err) {
        console.error('Backend API error', err)
        this.isBackendConnected = false
      }
    },

    switchAccount(id) {
      this.currentAccountId = id
    },

    async addAccount(form) {
      try {
        const resp = await api.post('/accounts', {
          username: form.username,
          clientId: form.clientId || 'semi_auto_client',
          clientSecret: form.clientSecret || 'semi_auto_secret',
          createdDaysAgo: form.createdDaysAgo || 5,
          proxyUrl: form.proxyUrl || null
        })
        if (resp.data.code === 200) {
          const newAcc = resp.data.data
          this.accounts.push(newAcc)
          if (!this.currentAccountId) {
            this.currentAccountId = newAcc.id
          }
          return { success: true, data: newAcc }
        }
        return { success: false, msg: resp.data.message }
      } catch (err) {
        return { success: false, msg: err.response?.data?.detail || err.response?.data?.message || err.message }
      }
    },

    async deleteAccount(accountId) {
      try {
        const resp = await api.delete(`/accounts/${accountId}`)
        if (resp.data.code === 200) {
          this.accounts = this.accounts.filter(a => a.id !== accountId)
          if (this.currentAccountId === accountId) {
            this.currentAccountId = this.accounts[0]?.id || null
          }
          return { success: true }
        }
        return { success: false, msg: resp.data.message }
      } catch (err) {
        return { success: false, msg: err.response?.data?.detail || err.response?.data?.message || err.message }
      }
    },

    async updateAccountStage(accountId, stageId) {
      try {
        const resp = await api.patch(`/accounts/${accountId}/stage`, { stage: stageId })
        if (resp.data.code === 200) {
          const acc = this.accounts.find(a => a.id === accountId)
          if (acc) {
            acc.stage = stageId
            acc.dailyLimit = resp.data.data.dailyLimit
          }
          return { success: true }
        }
        return { success: false, msg: resp.data.message }
      } catch (err) {
        return { success: false, msg: err.response?.data?.detail || err.response?.data?.message || err.message }
      }
    },

    cycleDraft(postId) {
      const post = this.candidatePosts.find(p => p.id === postId)
      if (post && post.drafts && post.drafts.length > 0) {
        post.selectedDraftIndex = (post.selectedDraftIndex + 1) % post.drafts.length
      }
    },

    updateDraftText(postId, newText) {
      const post = this.candidatePosts.find(p => p.id === postId)
      if (post && post.drafts && post.drafts[post.selectedDraftIndex]) {
        post.drafts[post.selectedDraftIndex].text = newText
      }
    },

    async skipPost(postId, reason = '人工忽略') {
      const post = this.candidatePosts.find(p => p.id === postId)
      if (!post) return

      try {
        const targetId = post.numericId || post.id
        await api.post(`/workbench/candidates/${targetId}/action`, { action: 'SKIP' })
        post.status = 'SKIPPED'
        await this.fetchLogs()
      } catch (e) {
        console.warn('Backend skipPost error', e)
      }
    },


    async scanSubreddit(subredditName) {
      try {
        const sub = this.subreddits.find(s => s.name === subredditName)
        if (sub) {
          await api.post(`/subreddits/${sub.id}/scan-now`)
        }
      } catch (e) {
        console.warn('scanSubreddit warning', e)
      }
    },

    async refreshPosts() {
      try {
        await api.post('/workbench/refresh')
      } catch (e) {
        console.warn('refreshPosts warning', e)
      }
      await this.fetchInitialData()
      return { success: true }
    },

    async generateCustomDrafts(payload) {
      try {
        const resp = await api.post('/workbench/custom-drafts', payload)
        if (resp.data.code === 200) {
          const data = resp.data.data
          const newPost = {
            id: 'custom_' + Date.now(),
            numericId: null,
            redditPostId: 'custom_' + Date.now(),
            subreddit: data.subreddit || 'r/AskReddit',
            title: data.title,
            author: 'reddit_user',
            createdTimeStr: '刚刚',
            url: data.url,
            numComments: 18,
            upvotes: 48,
            opportunityScore: 96,
            scoreBreakdown: {
              recency: '实时分析',
              sweetSpot: '高互动潜力',
              keywordMatch: '自定义帖子'
            },
            matchedKeyword: 'custom',
            summary: data.title,
            status: 'PENDING',
            selectedDraftIndex: 0,
            drafts: data.drafts
          }
          this.candidatePosts.unshift(newPost)
          return { success: true, post: newPost }
        }
        return { success: false, msg: resp.data.message }
      } catch (err) {
        return { success: false, msg: err.response?.data?.detail || err.message }
      }
    },

    async recordManualSent(postId) {
      const post = this.candidatePosts.find(p => p.id === postId)
      if (!post) return { success: false, msg: '帖子未找到' }

      const account = this.currentAccount
      const draft = post.drafts ? post.drafts[post.selectedDraftIndex] : null
      const text = draft ? draft.text.trim() : ''

      const targetId = post.numericId || post.id

      try {
        const resp = await api.post(`/workbench/candidates/${targetId}/action`, {
          action: 'MANUAL_SENT',
          accountId: account ? account.id : null,
          finalComment: text
        })

        if (resp.data.code === 200) {
          const resData = resp.data.data
          post.status = 'SENT'
          if (account) {
            account.dailySentCount = resData.todaySentAfter
            account.dailyLimit = resData.todayLimit
          }

          const sub = this.subreddits.find(s => s.name === post.subreddit)
          if (sub) sub.todaySent += 1

          await this.fetchLogs()
          return { success: true, todaySentAfter: resData.todaySentAfter, todayLimit: resData.todayLimit }
        }
        return { success: false, msg: resp.data.message }
      } catch (err) {
        const errMsg = err.response?.data?.detail || err.response?.data?.message || err.message
        return { success: false, msg: errMsg }
      }
    },

    async sendComment(postId, customDelaySeconds = null) {
      const post = this.candidatePosts.find(p => p.id === postId)
      if (!post) return { success: false, msg: '帖子未找到' }

      const account = this.currentAccount
      if (!account) return { success: false, msg: '当前未绑定任何 Reddit 账号，无法排期发帖！' }

      const draft = post.drafts ? post.drafts[post.selectedDraftIndex] : null
      const text = draft ? draft.text.trim() : ''

      if (!text) {
        return { success: false, msg: '输入校验失败：评论内容不能为空！' }
      }

      const targetId = post.numericId || post.id
      const delayMinutes = customDelaySeconds ? Math.max(1, Math.round(customDelaySeconds / 60)) : null

      try {
        const resp = await api.post(`/workbench/candidates/${targetId}/action`, {
          action: 'APPROVE',
          accountId: account.id,
          finalComment: text,
          customDelayMinutes: delayMinutes
        })

        if (resp.data.code === 200) {
          const resData = resp.data.data
          post.status = 'SENT'
          account.dailySentCount = resData.todaySentAfter
          account.dailyLimit = resData.todayLimit
          account.lastSentTime = Date.now()
          account.cooldownRemainingSeconds = resData.delaySeconds
          account.isCoolingDown = true

          const sub = this.subreddits.find(s => s.name === post.subreddit)
          if (sub) sub.todaySent += 1

          await this.fetchLogs()
          return { success: true, delaySeconds: resData.delaySeconds }
        }
        return { success: false, msg: resp.data.message }
      } catch (err) {
        const errMsg = err.response?.data?.detail || err.response?.data?.message || err.message
        return { success: false, msg: errMsg }
      }
    },

    async toggleSubreddit(id) {
      const sub = this.subreddits.find(s => s.id === id)
      if (!sub) return

      try {
        const resp = await api.put(`/subreddits/${id}/toggle`)
        if (resp.data.code === 200) {
          sub.enabled = resp.data.data.isEnabled
        }
      } catch (e) {
        console.warn('toggleSubreddit failed', e)
      }
    },

    async addSubreddit(subData) {
      try {
        const resp = await api.post('/subreddits', {
          name: subData.name,
          badge: subData.badge || '新手友好',
          minKarma: subData.minKarma || 0,
          dailyLimit: subData.dailyLimit || 2,
          description: subData.description || ''
        })
        if (resp.data.code === 200) {
          const s = resp.data.data
          this.subreddits.push({
            id: s.id,
            name: s.name,
            minKarma: s.minKarma,
            dailyLimit: s.dailyLimit,
            todaySent: s.todaySent,
            enabled: s.isEnabled,
            badge: s.badge,
            description: s.description
          })
          return { success: true }
        }
      } catch (err) {
        return { success: false, msg: err.response?.data?.detail || err.response?.data?.message || err.message }
      }
    },

    async addTemplate(templateData) {
      try {
        const resp = await api.post('/templates', {
          tone: templateData.category || templateData.tone || '真诚经验',
          templateText: templateData.content || templateData.templateText
        })
        if (resp.data.code === 200) {
          const t = resp.data.data
          this.templates.push({
            id: t.id,
            category: t.tone,
            title: `${t.tone}回复模板`,
            content: t.templateText,
            usageCount: t.usageCount,
            suitableFor: t.tone,
            isCoolingDown: t.isCoolingDown
          })
          return { success: true }
        }
      } catch (err) {
        return { success: false, msg: err.response?.data?.detail || err.response?.data?.message || err.message }
      }
    },

    async deleteTemplate(id) {
      try {
        const resp = await api.delete(`/templates/${id}`)
        if (resp.data.code === 200) {
          this.templates = this.templates.filter(t => t.id !== id)
          return { success: true }
        }
      } catch (e) {
        console.warn('deleteTemplate error', e)
      }
    },

    async updateRiskSettings(settings) {
      try {
        const resp = await api.put('/risk-control/settings', {
          minDelayMinutes: settings.minDelayMinutes,
          maxDelayMinutes: settings.maxDelayMinutes,
          maxDailyCommentsPerAccount: settings.maxDailyGlobal,
          maxDailyCommentsPerSub: settings.maxDailyPerSubreddit,
          sensitiveKeywords: settings.blacklistedKeywords
        })
        if (resp.data.code === 200) {
          this.riskSettings = { ...this.riskSettings, ...settings }
          return { success: true }
        }
      } catch (err) {
        return { success: false, msg: err.response?.data?.detail || err.response?.data?.message || err.message }
      }
    },

    async toggleCircuitBreaker() {
      const nextActive = !this.riskSettings.circuitBreakerActive
      try {
        const resp = await api.post('/risk-control/circuit-breaker', {
          action: nextActive ? 'TRIP' : 'RESET',
          reason: nextActive ? '人工挂起全局外发 (429 降温保护)' : null
        })
        if (resp.data.code === 200) {
          this.riskSettings.circuitBreakerActive = resp.data.data.circuitBreakerActive
          this.riskSettings.circuitBreakerReason = resp.data.data.circuitBreakerReason || ''
        }
      } catch (e) {
        console.warn('toggleCircuitBreaker error', e)
      }
    },

    async fetchLogs() {
      try {
        const resp = await api.get('/logs?page=1&pageSize=50')
        if (resp.data.code === 200) {
          const logs = resp.data.data || []
          this.logs = logs.map(l => ({
            id: l.id,
            timestamp: new Date(l.createdAt).toLocaleString('zh-CN'),
            account: l.accountUsername,
            subreddit: l.subreddit,
            postId: l.redditPostId,
            postTitle: l.postTitle,
            commentSnippet: l.commentSnippet,
            delaySeconds: l.delaySeconds,
            status: l.status,
            shadowbanStatus: l.shadowbanStatus,
            details: l.status === 'SUCCESS' ? `安全调度延迟 ${formatDuration(l.delaySeconds)}` : '被系统拦截'
          }))
        }
      } catch (e) {
        console.warn('Failed to fetch logs', e)
      }
    },

    async clearLogs() {
      try {
        const resp = await api.delete('/logs')
        if (resp.data.code === 200) {
          this.logs = []
          return { success: true }
        }
        return { success: false, msg: resp.data.message }
      } catch (err) {
        return { success: false, msg: err.response?.data?.detail || err.message }
      }
    },

    async probeShadowban(logId) {
      try {
        const resp = await api.post(`/logs/${logId}/probe-shadowban`)
        if (resp.data.code === 200) {
          const res = resp.data.data
          const targetLog = this.logs.find(l => l.id === logId)
          if (targetLog) {
            targetLog.shadowbanStatus = res.newStatus
            targetLog.details = `探针探测更新: ${res.newStatus}`
          }
          return { success: true, newStatus: res.newStatus, message: res.message }
        }
        return { success: false, msg: resp.data.message }
      } catch (err) {
        return { success: false, msg: err.response?.data?.detail || err.response?.data?.message || err.message }
      }
    },

    async testHandshake(accountId) {
      try {
        const resp = await api.post(`/accounts/${accountId}/test-handshake`)
        return resp.data
      } catch (err) {
        return {
          code: 500,
          message: err.response?.data?.detail || err.response?.data?.message || err.message,
          data: null
        }
      }
    },

    resetToDefault() {
      this.fetchInitialData()
    }
  }
})
