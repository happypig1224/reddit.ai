<template>
  <div class="accounts-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">账号与阶段策略</h2>
        <span class="page-subtitle">
          管理 Reddit 养号矩阵，按成长阶段执行每日安全回复配额 (免 API 凭据)
        </span>
      </div>
      <el-button type="primary" size="small" icon="Plus" @click="addAccountDialog = true">
        添加 Reddit 账号
      </el-button>
    </div>

    <!-- 运行阶段策略矩阵 -->
    <el-card shadow="never" class="standard-card">
      <div class="section-title">阶段规则</div>
      <div class="stage-matrix">
        <div
          v-for="stage in store.stages"
          :key="stage.id"
          class="stage-cell"
          :class="{ active: store.currentAccount?.stage === stage.id }"
          @click="store.currentAccountId && store.updateAccountStage(store.currentAccountId, stage.id)"
        >
          <div class="stage-name-row">
            <span class="stage-name">{{ stage.name }}</span>
            <el-tag size="small" v-if="store.currentAccount?.stage === stage.id" type="success" effect="dark">
              当前执行中
            </el-tag>
          </div>
          <div class="stage-params">
            <span>每日配额: <strong>{{ stage.targetComments }}</strong></span>
            <span>外链权限: <strong>{{ stage.allowLinks ? '受限允许' : '严格禁止' }}</strong></span>
          </div>
          <p class="stage-desc">{{ stage.description }}</p>
        </div>
      </div>
    </el-card>

    <!-- 账号列表数据表格 -->
    <el-card shadow="never" class="standard-card">
      <div class="section-title" style="margin-bottom: 12px;">已配置账号列表</div>
      <el-table :data="store.accounts" style="width: 100%" stripe border class="standard-table">
        <el-table-column label="用户名" min-width="150">
          <template #default="{ row }">
            <span class="acc-name-text">{{ row.username }}</span>
            <el-tag v-if="store.currentAccountId === row.id" size="small" type="success" effect="light" style="margin-left: 6px;">
              当前使用
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="账龄" width="80" align="center">
          <template #default="{ row }">{{ row.createdDaysAgo }} 天</template>
        </el-table-column>

        <el-table-column label="Comment Karma" prop="commentKarma" width="130" align="center" />
        <el-table-column label="Link Karma" prop="linkKarma" width="100" align="center" />

        <el-table-column label="当前运行阶段" width="150" align="center">
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

        <el-table-column label="今日已完成" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.dailySentCount >= row.dailyLimit ? 'danger' : 'success'" size="small" effect="light">
              {{ row.dailySentCount }} / {{ row.dailyLimit }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="140" align="center">
          <template #default="{ row }">
            <el-button
              v-if="store.currentAccountId !== row.id"
              type="primary"
              link
              size="small"
              @click="store.switchAccount(row.id)"
            >
              设为当前
            </el-button>
            <el-popconfirm
              title="确定要解除该 Reddit 账号的绑定吗？"
              confirm-button-text="确定"
              cancel-button-text="取消"
              @confirm="handleDelete(row.id)"
            >
              <template #reference>
                <el-button type="danger" link size="small">
                  删除
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="当前暂无已绑定的 Reddit 账号，请点击右上角「添加 Reddit 账号」开始配置" :image-size="80" />
        </template>
      </el-table>
    </el-card>

    <!-- 弹窗：录入新账号 -->
    <el-dialog v-model="addAccountDialog" title="录入 Reddit 账号 (免 API 凭据)" width="520px" destroy-on-close @closed="handleDialogClosed">
      <el-form label-position="top" size="default">
        <el-form-item label="Reddit 用户名">
          <el-input v-model="accountForm.username" placeholder="如 u/Dry-Bridge7201 (支持带或不带 u/)" />
        </el-form-item>
        <el-form-item label="当前账号注册时长 / 所属阶段">
          <div class="age-selector-container">
            <el-radio-group v-model="agePreset" size="small" class="age-radio-group" @change="handleAgePresetChange">
              <el-radio-button value="unsure">不确定 (自动校准)</el-radio-button>
              <el-radio-button value="stage1">新注册 (1-3天)</el-radio-button>
              <el-radio-button value="stage2">破冰期 (4-7天)</el-radio-button>
              <el-radio-button value="stage3">成长期 (8-14天)</el-radio-button>
              <el-radio-button value="stage4">稳定期 (15天以上)</el-radio-button>
              <el-radio-button value="custom">自定义天数</el-radio-button>
            </el-radio-group>

            <!-- 自定义天数调节 -->
            <div v-if="agePreset === 'custom'" class="custom-days-wrapper">
              <span class="custom-label">精确账龄：</span>
              <el-input-number v-model="accountForm.createdDaysAgo" :min="1" :max="3650" size="small" />
              <span class="custom-unit">天</span>
            </div>

            <!-- 阶梯风控与智能自校准说明卡片 -->
            <div class="stage-guide-card">
              <div class="guide-header-row">
                <el-tag size="small" :type="stageGuide.tagType" effect="dark">{{ stageGuide.badge }}</el-tag>
                <div class="guide-metrics">
                  <span>每日配额: <strong>{{ stageGuide.quota }}</strong></span>
                  <span style="margin-left: 10px;">外链权限: <strong>{{ stageGuide.links }}</strong></span>
                </div>
              </div>
              <p class="guide-desc">{{ stageGuide.desc }}</p>
              <div class="guide-notice">
                <el-icon style="margin-top: 2px;"><InfoFilled /></el-icon>
                <span>半自动助手模式：直接在工作台一键复制文案并直达原帖，无需等待 Reddit 官方 API 审批，录入用户名即可使用。</span>
              </div>
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="addAccountDialog = false">取消</el-button>
        <el-button size="small" type="primary" :loading="isSubmitting" @click="submitAddAccount">确认添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useKarmaStore } from '../stores/karmaStore'
import { ElMessage, ElNotification } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const store = useKarmaStore()

const addAccountDialog = ref(false)
const isSubmitting = ref(false)
const agePreset = ref('unsure')

const accountForm = reactive({
  username: '',
  clientId: '',
  clientSecret: '',
  proxyUrl: '',
  createdDaysAgo: 5
})

const handleAgePresetChange = (val) => {
  switch (val) {
    case 'stage1':
      accountForm.createdDaysAgo = 2
      break
    case 'stage2':
      accountForm.createdDaysAgo = 5
      break
    case 'stage3':
      accountForm.createdDaysAgo = 10
      break
    case 'stage4':
      accountForm.createdDaysAgo = 30
      break
    case 'unsure':
    default:
      accountForm.createdDaysAgo = 5
      break
  }
}

const stageGuide = computed(() => {
  switch (agePreset.value) {
    case 'stage1':
      return {
        badge: '冷启动期 (1-3天)',
        tagType: 'info',
        quota: '0 条 / 日',
        links: '严格禁止',
        desc: '仅允许浏览与点赞，避免新号发帖触发风控。'
      }
    case 'stage2':
      return {
        badge: '破冰期 (4-7天)',
        tagType: 'warning',
        quota: '2-5 条 / 日',
        links: '严格禁止',
        desc: '在问答板块回复日常话题积累 Karma，禁止携带外链。'
      }
    case 'stage3':
      return {
        badge: '成长期 (8-14天)',
        tagType: 'primary',
        quota: '3-8 条 / 日',
        links: '严格禁止',
        desc: '参与技术与兴趣板块讨论，禁止营销引流。'
      }
    case 'stage4':
      return {
        badge: '稳定期 (15天以上)',
        tagType: 'success',
        quota: '5-10 条 / 日',
        links: '受限允许',
        desc: '可参与垂直社区讨论，受限添加外链。'
      }
    case 'custom':
      const d = accountForm.createdDaysAgo || 5
      const q = d <= 3 ? '0 条 / 日' : d <= 7 ? '2-5 条 / 日' : d <= 14 ? '3-8 条 / 日' : '5-10 条 / 日'
      const l = d > 14 ? '受限允许' : '严格禁止'
      return {
        badge: `自定义 (${d} 天账龄)`,
        tagType: 'info',
        quota: q,
        links: l,
        desc: `按设定的 ${d} 天自动匹配对应配额与发帖限制。`
      }
    case 'unsure':
    default:
      return {
        badge: '自动校准 (先按破冰期 5 天运行)',
        tagType: 'warning',
        quota: '2-5 条 / 日',
        links: '严格禁止',
        desc: '默认按破冰期限制发帖。握手成功后将读取账号真实注册时间自动调整。'
      }
  }
})

onMounted(() => {
  if (route.query.add === 'true') {
    addAccountDialog.value = true
  }
})

watch(() => route.query.add, (newVal) => {
  if (newVal === 'true') {
    addAccountDialog.value = true
  }
})

const handleDialogClosed = () => {
  if (route.query.add) {
    router.replace({ path: '/accounts' })
  }
}

const testConnection = async (acc) => {
  const res = await store.testHandshake(acc.id)
  if (res && res.code === 200) {
    const ageInfo = res.data?.createdDaysAgo ? `，真实账龄: ${res.data.createdDaysAgo} 天` : ''
    ElNotification({
      title: 'OAuth 握手验证通过',
      message: `账号 ${acc.username} API 连接正常，耗时 ${res.data.latencyMs}ms，当前 Karma: ${res.data.commentKarma}${ageInfo}`,
      type: 'success',
      duration: 3500
    })
    store.fetchInitialData()
  } else {
    ElNotification({
      title: 'OAuth 握手响应',
      message: res?.message || '连接异常',
      type: 'warning',
      duration: 3500
    })
  }
}

const submitAddAccount = async () => {
  if (!accountForm.username.trim()) return ElMessage.error('请输入 Reddit 用户名')

  isSubmitting.value = true
  const res = await store.addAccount({
    username: accountForm.username.trim(),
    createdDaysAgo: accountForm.createdDaysAgo || 5
  })
  isSubmitting.value = false

  if (res.success) {
    ElMessage.success('Reddit 账号已成功录入养号矩阵')
    addAccountDialog.value = false
    accountForm.username = ''
    accountForm.createdDaysAgo = 5
    agePreset.value = 'unsure'
  } else {
    ElMessage.error(res.msg || '添加账号失败')
  }
}

const handleDelete = async (id) => {
  const res = await store.deleteAccount(id)
  if (res.success) {
    ElMessage.success('已解除账号绑定')
  } else {
    ElMessage.error(res.msg || '删除失败')
  }
}
</script>

<style scoped>
.accounts-page {
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

.section-title {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 10px;
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
  font-size: 13px;
}

.acc-name-text {
  font-weight: 600;
  color: #0f172a;
}

.age-selector-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.age-radio-group {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.custom-days-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #f1f5f9;
  border-radius: 6px;
  width: fit-content;
}

.custom-label, .custom-unit {
  font-size: 12px;
  color: #475569;
}

.stage-guide-card {
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.guide-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.guide-metrics {
  color: #475569;
  font-size: 12px;
}

.guide-metrics strong {
  color: #0f172a;
}

.guide-desc {
  font-size: 12px;
  color: #64748b;
  margin: 0;
  line-height: 1.5;
}

.guide-notice {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 11px;
  color: #0284c7;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 4px;
  padding: 6px 8px;
  line-height: 1.4;
}
</style>
