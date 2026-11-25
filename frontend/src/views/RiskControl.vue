<template>
  <div class="risk-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">防封与风控策略</h2>
        <span class="page-subtitle">
          配置每日安全配额、单社区频次上限与敏感词外链拦截 (半自动安全基线)
        </span>
      </div>
      <el-button type="primary" size="small" icon="Check" @click="saveSettings">
        保存策略
      </el-button>
    </div>

    <!-- 养号防风控四大黄金准则卡片 -->
    <el-card shadow="never" class="standard-card warm-up-guide-card">
      <div class="guide-rules-header">
        <el-tag type="success" effect="dark" size="small">玩法一：安全半自动养号准则</el-tag>
        <span class="guide-rules-title">新号防封与存活率保障指南</span>
      </div>
      <div class="guide-rules-grid">
        <div class="rule-box">
          <div class="rule-num">01</div>
          <div class="rule-content">
            <strong>前 3 天零评论潜伏 (STAGE_1)</strong>
            <p>冷启动期仅在 Reddit 原生页面浏览和点赞，严禁发表带外链或营销性质的内容。</p>
          </div>
        </div>
        <div class="rule-box">
          <div class="rule-num">02</div>
          <div class="rule-content">
            <strong>手动回复间隔保持 15-30 分钟</strong>
            <p>手动回复一条帖子后，请至少间隔 15 分钟再回复下一条，避免短时间内连续发帖触发 Reddit 垃圾过滤规则。</p>
          </div>
        </div>
        <div class="rule-box">
          <div class="rule-num">03</div>
          <div class="rule-content">
            <strong>严格禁止携带外链与品牌词</strong>
            <p>在 Karma 未达 100 之前，草稿中严禁出现任何网址链接、优惠券或联系方式。</p>
          </div>
        </div>
        <div class="rule-box">
          <div class="rule-num">04</div>
          <div class="rule-content">
            <strong>严格遵守每日阶段配额</strong>
            <p>破冰期单日上限不超过 3-5 条，达到配额后建议让账号休息，降低新号被平台限制的风险。</p>
          </div>
        </div>
      </div>
    </el-card>

    <div class="risk-grid">
      <!-- 频率与配额控制 -->
      <el-card shadow="never" class="standard-card">
        <div class="section-title">每日安全发帖配额 (防封阈值)</div>

        <el-form label-position="top" style="margin-top: 14px;">
          <el-form-item label="单账号每日评论总上限">
            <el-slider v-model="form.maxDailyGlobal" :min="1" :max="15" show-input />
          </el-form-item>

          <el-form-item label="同一 Subreddit 每日发送上限">
            <el-slider v-model="form.maxDailyPerSubreddit" :min="1" :max="4" show-input />
          </el-form-item>

          <div class="quota-tip-box">
            <el-icon style="margin-top: 2px; color: #ff4500;"><InfoFilled /></el-icon>
            <span>达到配额上限后，审核工作台将自动锁定发帖按钮，防止新号在单日内过量操作触发 Reddit 限流规则。新号建议保持在每日 3~5 条以内。</span>
          </div>
        </el-form>
      </el-card>

      <!-- 敏感词与外链黑名单 -->
      <el-card shadow="never" class="standard-card">
        <div class="section-title">受限敏感词与外链拦截 (实时阻断)</div>
        <p class="field-desc">草稿中包含以下任何词汇或域名后缀时，工作台实时标红并锁定复制按钮，严防新号携带外链被封：</p>

        <div class="keywords-wrap">
          <el-tag
            v-for="(kw, idx) in form.blacklistedKeywords"
            :key="idx"
            closable
            type="danger"
            effect="plain"
            size="small"
            @close="removeKeyword(idx)"
            class="tag-item"
          >
            {{ kw }}
          </el-tag>
        </div>

        <div class="add-kw-flex">
          <el-input
            v-model="newKeyword"
            placeholder="输入需要拦截的词汇或域名后缀..."
            size="small"
            style="width: 240px;"
            @keyup.enter="addKeyword"
          />
          <el-button type="primary" size="small" plain @click="addKeyword">添加规则</el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useKarmaStore } from '../stores/karmaStore'
import { ElMessage } from 'element-plus'
import { InfoFilled, Check } from '@element-plus/icons-vue'

const store = useKarmaStore()

const form = reactive({
  maxDailyGlobal: store.riskSettings.maxDailyGlobal,
  maxDailyPerSubreddit: store.riskSettings.maxDailyPerSubreddit,
  minDelayMinutes: store.riskSettings.minDelayMinutes || 15,
  maxDelayMinutes: store.riskSettings.maxDelayMinutes || 30,
  blacklistedKeywords: [...store.riskSettings.blacklistedKeywords],
  autoDetectShadowban: store.riskSettings.autoDetectShadowban || false,
  randomJitterEnabled: store.riskSettings.randomJitterEnabled || false
})

const newKeyword = ref('')

const addKeyword = () => {
  const kw = newKeyword.value.trim().toLowerCase()
  if (kw && !form.blacklistedKeywords.includes(kw)) {
    form.blacklistedKeywords.push(kw)
    newKeyword.value = ''
    ElMessage.success(`已添加拦截规则 "${kw}"`)
  }
}

const removeKeyword = (idx) => {
  form.blacklistedKeywords.splice(idx, 1)
}

const saveSettings = async () => {
  const res = await store.updateRiskSettings({
    maxDailyGlobal: form.maxDailyGlobal,
    maxDailyPerSubreddit: form.maxDailyPerSubreddit,
    minDelayMinutes: form.minDelayMinutes,
    maxDelayMinutes: form.maxDelayMinutes,
    blacklistedKeywords: form.blacklistedKeywords,
    autoDetectShadowban: form.autoDetectShadowban,
    randomJitterEnabled: form.randomJitterEnabled
  })
  if (res && res.success) {
    ElMessage.success('防封策略配置已保存并生效')
  } else {
    ElMessage.error(res?.msg || '保存失败')
  }
}
</script>

<style scoped>
.risk-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.page-subtitle {
  font-size: 13px;
  color: #64748b;
  margin-top: 2px;
}

.standard-card {
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  background-color: #ffffff;
}

.risk-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

@media (max-width: 860px) {
  .risk-grid {
    grid-template-columns: 1fr;
  }
}

.section-title {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
}

.field-desc {
  font-size: 12px;
  color: #64748b;
  margin: 6px 0 10px 0;
}

.quota-tip-box {
  margin-top: 14px;
  padding: 10px 12px;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.keywords-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 10px;
  min-height: 100px;
  max-height: 160px;
  overflow-y: auto;
  margin-bottom: 12px;
}

.add-kw-flex {
  display: flex;
  gap: 8px;
}

.warm-up-guide-card {
  background: linear-gradient(135deg, #f0fdf4 0%, #f8fafc 100%);
  border: 1px solid #bbf7d0;
}

.guide-rules-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.guide-rules-title {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.guide-rules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.rule-box {
  display: flex;
  gap: 10px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 10px 12px;
}

.rule-num {
  font-size: 16px;
  font-weight: 800;
  color: #16a34a;
  line-height: 1;
  margin-top: 2px;
}

.rule-content strong {
  font-size: 12px;
  color: #1e293b;
  display: block;
  margin-bottom: 4px;
}

.rule-content p {
  font-size: 11px;
  color: #64748b;
  line-height: 1.4;
  margin: 0;
}
</style>
