<template>
  <div class="templates-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">回复模板库</h2>
        <span class="page-subtitle">
          维护多场景高质量回复模板，支持参数占位符，内置 24h 去重与相似度拦截保护
        </span>
      </div>
      <el-button type="primary" size="small" icon="Plus" @click="openAddDialog">
        新建模板
      </el-button>
    </div>

    <!-- 过滤器与统计 -->
    <el-card shadow="never" class="standard-card">
      <div class="filter-flex">
        <el-radio-group v-model="selectedCategory" size="small">
          <el-radio-button label="ALL">全部 ({{ store.templates.length }})</el-radio-button>
          <el-radio-button label="经验分享">经验分享</el-radio-button>
          <el-radio-button label="方案对比">方案对比</el-radio-button>
          <el-radio-button label="追问互动">追问互动</el-radio-button>
          <el-radio-button label="日常建议">日常建议</el-radio-button>
        </el-radio-group>

        <span class="guard-pill">24h 查重与相似度拦截已启用</span>
      </div>
    </el-card>

    <!-- 模板列表 -->
    <div v-if="filteredTemplates.length > 0" class="templates-list">
      <div v-for="tpl in filteredTemplates" :key="tpl.id" class="tpl-card">
        <div class="tpl-header">
          <div class="tpl-title-group">
            <span class="tpl-title">{{ tpl.title }}</span>
            <el-tag size="small" type="info" effect="plain">{{ tpl.category }}</el-tag>
          </div>
          <div class="tpl-actions">
            <span class="tpl-usage">采用: {{ tpl.usageCount }} 次</span>
            <el-button type="primary" link size="small" @click="copyTemplate(tpl.content)">复制</el-button>
            <el-button type="danger" link size="small" @click="deleteTemplate(tpl.id)">删除</el-button>
          </div>
        </div>

        <div class="tpl-body">
          <p class="tpl-content">{{ tpl.content }}</p>
        </div>

        <div class="tpl-footer">
          <span class="tpl-scenario">适用场景：{{ tpl.suitableFor }}</span>
        </div>
      </div>
    </div>
    <el-empty
      v-else
      description="当前分类下暂无回复模板，请点击右上角「新建模板」添加"
      class="standard-card"
      style="background: #ffffff;"
      :image-size="80"
    />

    <!-- 弹窗：新建模板 -->
    <el-dialog v-model="dialogVisible" title="新建回复模板" width="500px">
      <el-form label-position="top" size="default">
        <el-form-item label="模板简述">
          <el-input v-model="form.title" placeholder="如 亲身踩坑并推荐轻量替代方案" />
        </el-form-item>
        <el-form-item label="场景分类">
          <el-select v-model="form.category" style="width: 100%">
            <el-option label="经验分享" value="经验分享" />
            <el-option label="方案对比" value="方案对比" />
            <el-option label="追问互动" value="追问互动" />
            <el-option label="日常建议" value="日常建议" />
          </el-select>
        </el-form-item>
        <el-form-item label="模板正文 (支持 {变量} 占位)">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="4"
            placeholder="例如: I had a very similar issue a while ago. What worked for me was using {Tool}..."
          />
        </el-form-item>
        <el-form-item label="适用场景">
          <el-input v-model="form.suitableFor" placeholder="如 方案选型、求助帖" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="dialogVisible = false">取消</el-button>
        <el-button size="small" type="primary" @click="saveTemplate">保存模板</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useKarmaStore } from '../stores/karmaStore'
import { ElMessage } from 'element-plus'

const store = useKarmaStore()

const selectedCategory = ref('ALL')
const dialogVisible = ref(false)

const form = reactive({
  title: '',
  category: '经验分享',
  content: '',
  suitableFor: ''
})

const filteredTemplates = computed(() => {
  if (selectedCategory.value === 'ALL') return store.templates
  return store.templates.filter(t => t.category === selectedCategory.value)
})

const openAddDialog = () => {
  form.title = ''
  form.category = '经验分享'
  form.content = ''
  form.suitableFor = ''
  dialogVisible.value = true
}

const saveTemplate = async () => {
  if (!form.content) {
    ElMessage.error('请填写完整内容')
    return
  }
  const res = await store.addTemplate({ ...form })
  if (res && res.success) {
    dialogVisible.value = false
    ElMessage.success('成功新增模板并入库')
  } else {
    ElMessage.error(res?.msg || '模板内容未通过安全合规校验')
  }
}

const deleteTemplate = async (id) => {
  await store.deleteTemplate(id)
  ElMessage.success('模板已删除')
}

const copyTemplate = (text) => {
  navigator.clipboard.writeText(text)
  ElMessage.success('已复制到剪贴板')
}
</script>

<style scoped>
.templates-page {
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

.filter-flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.guard-pill {
  font-size: 11px;
  color: #059669;
  background-color: #ecfdf5;
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid #a7f3d0;
}

.templates-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tpl-card {
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  background-color: #ffffff;
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

.tpl-title {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
}

.tpl-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tpl-usage {
  font-size: 11px;
  color: #94a3b8;
}

.tpl-body {
  background-color: #f8fafc;
  border-radius: 4px;
  padding: 8px 12px;
  border: 1px solid #f1f5f9;
  margin-bottom: 6px;
}

.tpl-content {
  font-size: 13px;
  color: #334155;
  line-height: 1.5;
}

.tpl-footer {
  font-size: 11px;
  color: #64748b;
}
</style>
