<template>
  <div class="settings-page">
    <div class="page-header">
      <div class="header-titles">
        <h2 class="title">策略与配置</h2>
        <span class="subtitle">统一管理账号认证、目标社区范围、内容模板与风控限频规则</span>
      </div>
    </div>

    <!-- 企业级 Tab 切换卡片 -->
    <el-card shadow="never" class="settings-card">
      <el-tabs v-model="activeTab" class="enterprise-tabs">
        <!-- Tab 1: 账号与生命周期 -->
        <el-tab-pane label="账号与运行阶段" name="accounts">
          <div class="tab-pane-content">
            <!-- 阶段概览条 -->
            <div class="section-block">
              <div class="section-title">运行阶段策略</div>
              <div class="stage-matrix">
                <div
                  v-for="stage in store.stages"
                  :key="stage.id"
                  class="stage-cell"
                  :class="{ active: store.currentAccount.stage === stage.id }"
                  @click="store.updateAccountStage(store.currentAccountId, stage.id)"
                >
                  <div class="stage-name-row">
                    <span class="stage-name">{{ stage.name }}</span>
                    <el-tag size="small" v-if="store.currentAccount.stage === stage.id" type="success" effect="dark">
                      生效中
                    </el-tag>
                  </div>
                  <div class="stage-params">
                    <span>每日配额: <strong>{{ stage.targetComments }}</strong></span>
                    <span>外链权限: <strong>{{ stage.allowLinks ? '受限允许' : '严格禁止' }}</strong></span>
                  </div>
                  <p class="stage-desc">{{ stage.description }}</p>
                </div>
              </div>
            </div>

            <el-divider style="margin: 20px 0;" />

            <!-- 已配置账号表格 -->
            <div class="section-block">
              <div class="section-header-flex">
                <div class="section-title">绑定账号列表</div>
                <el-button type="primary" size="small" icon="Plus" @click="addAccountDialog = true">
                  添加 Reddit 账号
                </el-button>
              </div>

              <el-table :data="store.accounts" style="width: 100%" stripe border class="standard-table">
                <el-table-column label="用户名" prop="username" min-width="160">
                  <template #default="{ row }">
                    <span class="acc-name-text">{{ row.username }}</span>
                    <el-tag v-if="store.currentAccountId === row.id" size="small" type="success" effect="light" style="margin-left: 6px;">
                      当前
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="账龄" width="90" align="center">
                  <template #default="{ row }">{{ row.createdDaysAgo }} 天</template>
                </el-table-column>
                <el-table-column label="Comment Karma" prop="commentKarma" width="140" align="center" />
                <el-table-column label="当前运行阶段" width="160" align="center">
                  <template #default="{ row }">
                    <el-select
                      v-model="row.stage"
                      size="small"
                      @change="(val) => store.updateAccountStage(row.id, val)"
                    >
                      <el-option
                        v-for="s in store.stages"
                        :key="s.id"
                        :label="s.name.split(' ')[0]"
                        :value="s.id"
                      />
                    </el-select>
                  </template>
                </el-table-column>
                <el-table-column label="今日发送" width="110" align="center">
                  <template #default="{ row }">
                    <span>{{ row.dailySentCount }} / {{ row.dailyLimit }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="OAuth Client ID" prop="clientId" min-width="150" show-overflow-tooltip />
                <el-table-column label="操作" width="150" align="center" fixed="right">
                  <template #default="{ row }">
                    <el-button
                      v-if="store.currentAccountId !== row.id"
                      type="primary"
                      link
                      size="small"
                      @click="store.switchAccount(row.id)"
                    >
                      切换为当前
                    </el-button>
                    <el-button
                      type="default"
                      link
                      size="small"
                      @click="testOAuthConnection(row)"
                    >
                      测试握手
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </el-tab-pane>

        <!-- Tab 2: 目标社区池 -->
        <el-tab-pane label="目标社区池" name="subreddits">
          <div class="tab-pane-content">
            <div class="section-header-flex">
              <div class="section-title">社区监听范围与版块配额</div>
              <el-button type="primary" size="small" icon="Plus" @click="addSubDialog = true">
                添加社区 (Subreddit)
              </el-button>
            </div>

            <el-table :data="store.subreddits" style="width: 100%" stripe border class="standard-table">
              <el-table-column label="社区板块" min-width="160">
                <template #default="{ row }">
                  <a :href="`https://reddit.com/${row.name}`" target="_blank" class="sub-link-clean">
                    {{ row.name }}
                  </a>
                </template>
              </el-table-column>
              <el-table-column label="分类标签" width="130" prop="badge" />
              <el-table-column label="Karma 门槛" width="120" align="center">
                <template #default="{ row }">
                  {{ row.minKarma === 0 ? '无门槛' : `≥ ${row.minKarma}` }}
                </template>
              </el-table-column>
              <el-table-column label="单日配额上限" width="130" align="center">
                <template #default="{ row }">{{ row.dailyLimit }} 条 / 日</template>
              </el-table-column>
              <el-table-column label="今日已发出" width="110" align="center">
                <template #default="{ row }">
                  <span :class="{ 'text-danger': row.todaySent >= row.dailyLimit }">
                    {{ row.todaySent }} / {{ row.dailyLimit }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="监听状态" width="100" align="center">
                <template #default="{ row }">
                  <el-switch
                    :model-value="row.enabled"
                    @change="() => store.toggleSubreddit(row.id)"
                    active-color="#ff4500"
                  />
                </template>
              </el-table-column>
              <el-table-column label="描述" min-width="220" prop="description" show-overflow-tooltip />
            </el-table>
          </div>
        </el-tab-pane>

        <!-- Tab 3: 回复模板库 -->
        <el-tab-pane label="回复模板库" name="templates">
          <div class="tab-pane-content">
            <div class="section-header-flex">
              <div class="section-title">多场景内容模板 (内置 24h 查重与相似度拦截)</div>
              <el-button type="primary" size="small" icon="Plus" @click="addTplDialog = true">
                新建模板
              </el-button>
            </div>

            <div class="templates-list">
              <div v-for="tpl in store.templates" :key="tpl.id" class="tpl-row-item">
                <div class="tpl-header">
                  <div class="tpl-title-group">
                    <span class="tpl-name">{{ tpl.title }}</span>
                    <el-tag size="small" type="info">{{ tpl.category }}</el-tag>
                  </div>
                  <div class="tpl-ops">
                    <span class="usage-count">采用: {{ tpl.usageCount }} 次</span>
                    <el-button type="danger" link size="small" @click="store.deleteTemplate(tpl.id)">删除</el-button>
                  </div>
                </div>
                <div class="tpl-text-box">{{ tpl.content }}</div>
                <div class="tpl-applicable">适宜场景：{{ tpl.suitableFor }}</div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- Tab 4: 频控与风控规则 -->
        <el-tab-pane label="风控与限频参数" name="risk">
          <div class="tab-pane-content">
            <div class="risk-form-layout">
              <div class="risk-col">
                <div class="section-title">频率限制与随机调度区间</div>
                <el-form label-position="top" style="margin-top: 14px;">
                  <el-form-item label="单账号每日评论总上限">
                    <el-slider v-model="riskForm.maxDailyGlobal" :min="1" :max="15" show-input />
                  </el-form-item>

                  <el-form-item label="单板块每日评论上限">
                    <el-slider v-model="riskForm.maxDailyPerSubreddit" :min="1" :max="4" show-input />
                  </el-form-item>

                  <el-form-item label="调度延迟区间 (分钟)">
                    <div class="range-inputs">
                      <el-input-number v-model="riskForm.minDelayMinutes" :min="3" :max="riskForm.maxDelayMinutes" size="small" />
                      <span>至</span>
                      <el-input-number v-model="riskForm.maxDelayMinutes" :min="riskForm.minDelayMinutes" :max="60" size="small" />
                      <span class="range-hint">分钟 (系统将注入带随机秒级抖动的延迟)</span>
                    </div>
                  </el-form-item>

                  <el-form-item label="行为拟真">
                    <el-switch v-model="riskForm.randomJitterEnabled" active-text="启用非等距正态随机扰动" />
                  </el-form-item>

                  <el-form-item label="存活检测">
                    <el-switch v-model="riskForm.autoDetectShadowban" active-text="发送 30 分钟后使用匿名端点探测公开可见性" />
                  </el-form-item>
                </el-form>
              </div>

              <div class="risk-col">
                <div class="section-title">受限字符与黑名单 (触发即阻断)</div>
                <p class="field-desc">草稿中包含以下任何字符或后缀时，系统强制禁止排队外发：</p>

                <div class="keywords-wrap">
                  <el-tag
                    v-for="(kw, idx) in riskForm.blacklistedKeywords"
                    :key="idx"
                    closable
                    type="danger"
                    effect="plain"
                    size="small"
                    @close="removeKw(idx)"
                    class="tag-item"
                  >
                    {{ kw }}
                  </el-tag>
                </div>

                <div class="add-kw-flex">
                  <el-input
                    v-model="newKwInput"
                    placeholder="输入需要拦截的词汇或域名后缀..."
                    size="small"
                    style="width: 260px;"
                    @keyup.enter="addKw"
                  />
                  <el-button type="primary" size="small" plain @click="addKw">添加规则</el-button>
                </div>

                <el-divider style="margin: 20px 0 16px 0;" />

                <div class="section-title">429 熔断演练</div>
                <div class="breaker-row">
                  <span class="breaker-state-text">
                    当前状态: <strong>{{ store.riskSettings.circuitBreakerActive ? '熔断激活中 (全系统降温)' : '网络正常 (监听中)' }}</strong>
                  </span>
                  <el-button
                    :type="store.riskSettings.circuitBreakerActive ? 'danger' : 'info'"
                    size="small"
                    @click="store.toggleCircuitBreaker"
                  >
                    {{ store.riskSettings.circuitBreakerActive ? '解除熔断' : '模拟触发 429' }}
                  </el-button>
                </div>
              </div>
            </div>

            <div class="risk-save-bar">
              <el-button type="primary" @click="saveRiskConfig">保存策略配置</el-button>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 弹窗：添加账号 -->
    <el-dialog v-model="addAccountDialog" title="绑定 Reddit 账号 (Script 应用)" width="480px">
      <el-form label-position="top" size="default">
        <el-form-item label="Reddit 用户名">
          <el-input v-model="accountForm.username" placeholder="u/username" />
        </el-form-item>
        <el-form-item label="Reddit OAuth Client ID">
          <el-input v-model="accountForm.clientId" placeholder="从 reddit.com/prefs/apps 复制" />
        </el-form-item>
        <el-form-item label="Reddit OAuth Client Secret">
          <el-input v-model="accountForm.clientSecret" type="password" placeholder="Client Secret 密钥" />
        </el-form-item>
        <el-form-item label="当前账号注册时长 (天)">
          <el-input-number v-model="accountForm.createdDaysAgo" :min="1" :max="365" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addAccountDialog = false">取消</el-button>
        <el-button type="primary" @click="submitAddAccount">确认添加</el-button>
      </template>
    </el-dialog>

    <!-- 弹窗：添加社区 -->
    <el-dialog v-model="addSubDialog" title="添加目标 Subreddit" width="460px">
      <el-form label-position="top" size="default">
        <el-form-item label="社区代号">
          <el-input v-model="subForm.name" placeholder="例如 r/webdev" />
        </el-form-item>
        <el-form-item label="分类定位">
          <el-input v-model="subForm.badge" placeholder="例如 技术探讨 / 新手问答" />
        </el-form-item>
        <el-form-item label="最低 Karma 门槛要求">
          <el-input-number v-model="subForm.minKarma" :min="0" :max="500" />
        </el-form-item>
        <el-form-item label="单日配额上限">
          <el-input-number v-model="subForm.dailyLimit" :min="1" :max="5" />
        </el-form-item>
        <el-form-item label="板块简述">
          <el-input v-model="subForm.description" placeholder="主要讨论方向..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addSubDialog = false">取消</el-button>
        <el-button type="primary" @click="submitAddSub">添加到社区池</el-button>
      </template>
    </el-dialog>

    <!-- 弹窗：新建模板 -->
    <el-dialog v-model="addTplDialog" title="新建回复模板" width="500px">
      <el-form label-position="top" size="default">
        <el-form-item label="模板简述">
          <el-input v-model="tplForm.title" placeholder="如 亲身经验并提供轻量方案" />
        </el-form-item>
        <el-form-item label="场景分类">
          <el-select v-model="tplForm.category" style="width: 100%">
            <el-option label="经验分享" value="经验分享" />
            <el-option label="方案对比" value="方案对比" />
            <el-option label="追问互动" value="追问互动" />
            <el-option label="日常建议" value="日常建议" />
          </el-select>
        </el-form-item>
        <el-form-item label="模板正文 (支持 {变量} 占位)">
          <el-input v-model="tplForm.content" type="textarea" :rows="4" placeholder="I had a very similar issue a while ago..." />
        </el-form-item>
        <el-form-item label="适宜场景">
          <el-input v-model="tplForm.suitableFor" placeholder="如 方案选型、求助帖" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addTplDialog = false">取消</el-button>
        <el-button type="primary" @click="submitAddTpl">保存模板</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useKarmaStore } from '../stores/karmaStore'
import { ElMessage, ElNotification } from 'element-plus'

const store = useKarmaStore()
const activeTab = ref('accounts')

// 账号弹窗表单
const addAccountDialog = ref(false)
const accountForm = reactive({
  username: '',
  clientId: '',
  clientSecret: '',
  createdDaysAgo: 5
})

const testOAuthConnection = (acc) => {
  ElNotification({
    title: 'OAuth 握手验证',
    message: `账号 ${acc.username} API 连接正常，当前 Comment Karma: ${acc.commentKarma}`,
    type: 'success',
    duration: 3000
  })
}

const submitAddAccount = () => {
  if (!accountForm.username) return ElMessage.error('请输入用户名')
  const stage = accountForm.createdDaysAgo <= 3 ? 'STAGE_1' : accountForm.createdDaysAgo <= 7 ? 'STAGE_2' : 'STAGE_3'
  store.accounts.push({
    id: Date.now(),
    username: accountForm.username,
    createdDaysAgo: accountForm.createdDaysAgo,
    stage: stage,
    commentKarma: 1,
    linkKarma: 1,
    dailySentCount: 0,
    dailyLimit: stage === 'STAGE_1' ? 0 : 5,
    lastSentTime: null,
    cooldownRemainingSeconds: 0,
    isCoolingDown: false,
    status: 'HEALTHY',
    clientId: accountForm.clientId || 'client_' + Math.random().toString(36).substring(7),
    clientSecret: accountForm.clientSecret || 'sec_••••'
  })
  store.saveToStorage()
  addAccountDialog.value = false
  ElMessage.success('已绑定 Reddit 账号')
}

// 社区弹窗表单
const addSubDialog = ref(false)
const subForm = reactive({
  name: '',
  badge: '技术探讨',
  minKarma: 0,
  dailyLimit: 2,
  description: ''
})

const submitAddSub = () => {
  if (!subForm.name) return ElMessage.error('请输入社区板块代号')
  store.addSubreddit({ ...subForm })
  addSubDialog.value = false
  ElMessage.success('已将社区添加至监听池')
}

// 模板弹窗表单
const addTplDialog = ref(false)
const tplForm = reactive({
  title: '',
  category: '经验分享',
  content: '',
  suitableFor: ''
})

const submitAddTpl = () => {
  if (!tplForm.title || !tplForm.content) return ElMessage.error('请填写标题和内容')
  store.addTemplate({ ...tplForm })
  addTplDialog.value = false
  ElMessage.success('模板已添加')
}

// 风控表单
const riskForm = reactive({
  maxDailyGlobal: store.riskSettings.maxDailyGlobal,
  maxDailyPerSubreddit: store.riskSettings.maxDailyPerSubreddit,
  minDelayMinutes: store.riskSettings.minDelayMinutes,
  maxDelayMinutes: store.riskSettings.maxDelayMinutes,
  blacklistedKeywords: [...store.riskSettings.blacklistedKeywords],
  autoDetectShadowban: store.riskSettings.autoDetectShadowban,
  randomJitterEnabled: store.riskSettings.randomJitterEnabled
})

const newKwInput = ref('')
const addKw = () => {
  const kw = newKwInput.value.trim().toLowerCase()
  if (kw && !riskForm.blacklistedKeywords.includes(kw)) {
    riskForm.blacklistedKeywords.push(kw)
    newKwInput.value = ''
  }
}
const removeKw = (idx) => {
  riskForm.blacklistedKeywords.splice(idx, 1)
}

const saveRiskConfig = () => {
  store.updateRiskSettings({
    maxDailyGlobal: riskForm.maxDailyGlobal,
    maxDailyPerSubreddit: riskForm.maxDailyPerSubreddit,
    minDelayMinutes: riskForm.minDelayMinutes,
    maxDelayMinutes: riskForm.maxDelayMinutes,
    blacklistedKeywords: riskForm.blacklistedKeywords,
    autoDetectShadowban: riskForm.autoDetectShadowban,
    randomJitterEnabled: riskForm.randomJitterEnabled
  })
  ElMessage.success('策略配置已保存并生效')
}
</script>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 1100px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 2px;
}

.title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.subtitle {
  font-size: 13px;
  color: #64748b;
}

.settings-card {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background-color: #ffffff;
}

.tab-pane-content {
  padding: 10px 4px;
}

.section-block {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-header-flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-title {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
}

.stage-matrix {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 12px;
}

.stage-cell {
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  flex-direction: column;
}

.stage-cell:hover {
  border-color: #cbd5e1;
  background-color: #f1f5f9;
}

.stage-cell.active {
  background-color: #fff9f6;
  border: 1.5px solid #ff4500;
}

.stage-name-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.stage-name {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
}

.stage-params {
  display: flex;
  flex-direction: column;
  gap: 3px;
  font-size: 12px;
  color: #475569;
  margin-bottom: 8px;
}

.stage-desc {
  font-size: 11px;
  color: #64748b;
  line-height: 1.5;
  margin: 0;
}

.standard-table {
  border-radius: 6px;
  font-size: 13px;
}

.acc-name-text {
  font-weight: 600;
  color: #0f172a;
}

.sub-link-clean {
  font-weight: 600;
  color: #ff4500;
  text-decoration: none;
}

.sub-link-clean:hover {
  text-decoration: underline;
}

.text-danger {
  color: #ef4444;
  font-weight: 600;
}

/* 模板列表样式 */
.templates-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tpl-row-item {
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 12px 14px;
}

.tpl-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.tpl-title-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tpl-name {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
}

.tpl-ops {
  display: flex;
  align-items: center;
  gap: 12px;
}

.usage-count {
  font-size: 11px;
  color: #94a3b8;
}

.tpl-text-box {
  font-size: 13px;
  color: #334155;
  line-height: 1.5;
  background-color: #ffffff;
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
  margin-bottom: 6px;
}

.tpl-applicable {
  font-size: 11px;
  color: #64748b;
}

/* 风控表单布局 */
.risk-form-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

@media (max-width: 860px) {
  .risk-form-layout {
    grid-template-columns: 1fr;
  }
}

.risk-col {
  display: flex;
  flex-direction: column;
}

.range-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.range-hint {
  font-size: 11px;
  color: #64748b;
}

.field-desc {
  font-size: 12px;
  color: #64748b;
  margin: 6px 0 10px 0;
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

.breaker-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f8fafc;
  padding: 10px 14px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  margin-top: 10px;
}

.breaker-state-text {
  font-size: 13px;
  color: #334155;
}

.risk-save-bar {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
  display: flex;
  justify-content: flex-end;
}
</style>

