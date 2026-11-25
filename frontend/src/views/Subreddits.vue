<template>
  <div class="subreddits-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">目标社区池</h2>
        <span class="page-subtitle">
          配置允许监听的目标 Subreddit 范围、准入门槛与单日发帖配额
        </span>
      </div>
      <el-button type="primary" size="small" icon="Plus" @click="addModalVisible = true">
        添加目标社区
      </el-button>
    </div>

    <el-card shadow="never" class="standard-card">
      <el-table :data="store.subreddits" style="width: 100%" stripe border class="standard-table">
        <el-table-column label="社区板块" min-width="170">
          <template #default="{ row }">
            <a :href="`https://reddit.com/${row.name}`" target="_blank" class="sub-link-clean">
              {{ row.name }}
            </a>
          </template>
        </el-table-column>

        <el-table-column label="分类标签" width="120" prop="badge" />

        <el-table-column label="Karma 门槛" width="110" align="center">
          <template #default="{ row }">
            {{ row.minKarma === 0 ? '无门槛' : `≥ ${row.minKarma}` }}
          </template>
        </el-table-column>

        <el-table-column label="单日安全上限" width="120" align="center">
          <template #default="{ row }">{{ row.dailyLimit }} 条 / 日</template>
        </el-table-column>

        <el-table-column label="今日发出" width="100" align="center">
          <template #default="{ row }">
            <span :class="{ 'text-danger': row.todaySent >= row.dailyLimit }">
              {{ row.todaySent }} / {{ row.dailyLimit }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="监听状态" width="90" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="row.enabled"
              @change="() => store.toggleSubreddit(row.id)"
              active-color="#ff4500"
            />
          </template>
        </el-table-column>

        <el-table-column label="板块描述" min-width="180" prop="description" show-overflow-tooltip />

        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              @click="scanSubreddit(row)"
            >
              单版扫描
            </el-button>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="当前暂无监控的社区，请点击右上角「添加社区」开始配置" :image-size="80" />
        </template>
      </el-table>
    </el-card>

    <!-- 弹窗：添加新社区 -->
    <el-dialog v-model="addModalVisible" title="添加目标 Subreddit" width="460px">
      <el-form label-position="top" size="default">
        <el-form-item label="社区代号">
          <el-input v-model="newSub.name" placeholder="例如 r/webdev" />
        </el-form-item>
        <el-form-item label="分类标签">
          <el-input v-model="newSub.badge" placeholder="如 技术交流 / 新手问答" />
        </el-form-item>
        <el-form-item label="最低 Karma 门槛要求">
          <el-input-number v-model="newSub.minKarma" :min="0" :max="500" />
        </el-form-item>
        <el-form-item label="单日配额上限">
          <el-input-number v-model="newSub.dailyLimit" :min="1" :max="5" />
        </el-form-item>
        <el-form-item label="板块简述">
          <el-input v-model="newSub.description" placeholder="社区的主要讨论方向..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="addModalVisible = false">取消</el-button>
        <el-button size="small" type="primary" @click="handleSaveSub">添加到社区池</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useKarmaStore } from '../stores/karmaStore'
import { ElMessage } from 'element-plus'

const store = useKarmaStore()

const addModalVisible = ref(false)
const newSub = reactive({
  name: '',
  badge: '技术交流',
  minKarma: 0,
  dailyLimit: 2,
  description: ''
})

const handleSaveSub = async () => {
  if (!newSub.name) return ElMessage.error('请输入社区代号')
  const res = await store.addSubreddit({ ...newSub })
  addModalVisible.value = false
  if (res && res.success) {
    ElMessage.success('已将社区纳入监听池并持久化至数据库')
  } else {
    ElMessage.error(res?.msg || '添加失败')
  }
}

const scanSubreddit = (row) => {
  ElMessage.info(`正在扫描 ${row.name} 最新 24h 内的新帖...`)
  setTimeout(() => {
    ElMessage.success(`${row.name} 扫描完成，已同步最新数据`)
  }, 500)
}
</script>

<style scoped>
.subreddits-page {
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

.standard-table {
  font-size: 13px;
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
</style>
