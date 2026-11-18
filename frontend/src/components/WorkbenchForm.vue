<template>
  <el-card class="soft-card">
    <template #header><div class="card-header"><span>影像参数输入</span></div></template>
    
    <el-collapse v-model="activeCollapse" class="custom-collapse" style="margin-bottom: 16px;">
      <el-collapse-item name="1" title="⚙️ 导入患者标注文件 (CSV)">
        <el-upload action="#" accept=".csv" :show-file-list="false" :http-request="uploadCSV">
          <el-button size="small" type="info" plain round>选择 CSV</el-button>
          <span v-if="csvLoaded" style="margin-left: 10px; color: #0ea5e9; font-size: 13px;">✅ 已加载 {{ csvCount }} 条</span>
        </el-upload>
      </el-collapse-item>
    </el-collapse>

    <div style="margin-bottom: 16px; text-align: center;">
      <el-button type="warning" plain size="small" round @click="fillDemoData">一键填充演示数据</el-button>
    </div>

    <el-form label-position="top">
      <div class="param-group">
        <h4 class="group-title">当前 CT</h4>
        <el-form-item label="影像文件 (.nii 或 .mhd)">
          <el-upload class="custom-upload" drag action="#" accept=".nii,.gz,.mhd,.raw" :show-file-list="false" :http-request="(opt) => customUpload(opt, 'cur')">
            <div class="el-upload__text" v-if="!form.file_cur">拖拽或 <em>点击上传</em></div>
            <div class="el-upload__text" v-else style="color: #0ea5e9; font-weight: 600;">✅ 已加载</div>
          </el-upload>
        </el-form-item>
        <el-form-item label="坐标 (X, Y, Z) mm">
          <div style="display: flex; gap: 8px; width: 100%;">
            <el-input-number v-model="form.cur_coordX" :controls="false" @change="saveForm" style="flex:1; width: 100%;" />
            <el-input-number v-model="form.cur_coordY" :controls="false" @change="saveForm" style="flex:1; width: 100%;" />
            <el-input-number v-model="form.cur_coordZ" :controls="false" @change="saveForm" style="flex:1; width: 100%;" />
          </div>
        </el-form-item>
      </div>

      <div class="param-group" style="margin-top: 16px;">
        <h4 class="group-title">先前 CT</h4>
        <el-form-item label="影像文件 (.nii 或 .mhd)">
          <el-upload class="custom-upload" drag action="#" accept=".nii,.gz,.mhd,.raw" :show-file-list="false" :http-request="(opt) => customUpload(opt, 'pri')">
            <div class="el-upload__text" v-if="!form.file_pri">拖拽或 <em>点击上传</em></div>
            <div class="el-upload__text" v-else style="color: #0ea5e9; font-weight: 600;">✅ 已加载</div>
          </el-upload>
        </el-form-item>
        <el-form-item label="坐标 (X, Y, Z) mm">
          <div style="display: flex; gap: 8px; width: 100%;">
            <el-input-number v-model="form.pri_coordX" :controls="false" @change="saveForm" style="flex:1; width: 100%;" />
            <el-input-number v-model="form.pri_coordY" :controls="false" @change="saveForm" style="flex:1; width: 100%;" />
            <el-input-number v-model="form.pri_coordZ" :controls="false" @change="saveForm" style="flex:1; width: 100%;" />
          </div>
        </el-form-item>
      </div>

      <el-form-item label="检查间隔 (月)" style="margin-top: 16px;">
        <el-slider v-model="form.months" @change="saveForm" :min="1" :max="24" show-input />
      </el-form-item>

      <el-button type="primary" size="large" class="primary-btn" :loading="loading" @click="$emit('start-predict')">
        启动评估
      </el-button>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useFormStore } from '../stores/useFormStore'
import { storeToRefs } from 'pinia'

defineProps({ loading: Boolean })
defineEmits(['start-predict'])

const formStore = useFormStore()
const { form, saveForm } = storeToRefs(formStore)

const activeCollapse = ref([])
const csvLoaded = ref(false)
const csvCount = ref(0)
const annotationsData = ref({})

const fillDemoData = () => {
  form.value.file_cur = 'demo_current.nii.gz'
  form.value.file_pri = 'demo_prior.nii.gz'
  form.value.cur_coordX = -128.69; form.value.cur_coordY = -175.31; form.value.cur_coordZ = -298.38
  form.value.pri_coordX = -128.69; form.value.pri_coordY = -175.31; form.value.pri_coordZ = -298.38
  form.value.months = 12
  saveForm.value()
  ElMessage.success('已填充演示参数，请直接点击启动评估！')
}

const uploadCSV = async (options) => {
  const formData = new FormData(); formData.append('file', options.file)
  try {
    const res = await axios.post('/api/upload_annotations', formData)
    if (res.data.status === 'success') {
      annotationsData.value = res.data.annotations; csvCount.value = res.data.total; csvLoaded.value = true
      ElMessage.success(`成功加载 ${res.data.total} 条标注`); activeCollapse.value = []
    }
  } catch (error) { ElMessage.error('CSV解析失败') }
}

const customUpload = async (options, type) => {
  const formData = new FormData(); formData.append('file', options.file)
  try {
    const originalName = options.file.name 
    const res = await axios.post('/api/upload', formData)
    if (type === 'cur') form.value.file_cur = res.data.filename
    else form.value.file_pri = res.data.filename
    saveForm.value(); ElMessage.success('文件上传成功！')

    if (csvLoaded.value) {
      const seriesuid = originalName.replace('.nii.gz', '').replace('.nii', '').replace('.mhd', '')
      const matched = annotationsData.value[seriesuid]
      if (matched && matched.length > 0) {
        const nodule = matched[0]
        if (type === 'cur') {
          form.value.cur_coordX = nodule.coordX; form.value.cur_coordY = nodule.coordY; form.value.cur_coordZ = nodule.coordZ
        } else {
          form.value.pri_coordX = nodule.coordX; form.value.pri_coordY = nodule.coordY; form.value.pri_coordZ = nodule.coordZ
        }
        saveForm.value(); ElMessage.success(`自动匹配到结节坐标`)
      }
    }
  } catch (error) { ElMessage.error('上传失败') }
}
</script>

<style scoped>
.soft-card { border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.8); box-shadow: 0 10px 30px -10px rgba(2, 132, 199, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.02); background: rgba(255, 255, 255, 0.95); }
.card-header { font-weight: 600; font-size: 18px; color: #1e293b; }

.custom-collapse { border: none; background: #f8fafc; border-radius: 8px; overflow: hidden; }
.custom-collapse :deep(.el-collapse-item__header) { border-bottom: none; background: transparent; padding-left: 16px; color: #64748b; font-size: 13px; }
.custom-collapse :deep(.el-collapse-item__wrap) { border-bottom: none; background: transparent; }
.custom-collapse :deep(.el-collapse-item__content) { padding: 0 16px 16px 16px; }

.param-group { background: #fafcff; padding: 16px; border-radius: 12px; border: 1px solid #e2e8f0; }
.group-title { margin: 0 0 12px 0; color: #0ea5e9; font-size: 15px; font-weight: 600; }

.custom-upload :deep(.el-upload-dragger) { padding: 20px; border-radius: 8px; border: 2px dashed #cbd5e1; background: white; transition: all 0.2s; }
.custom-upload :deep(.el-upload-dragger:hover) { border-color: #0ea5e9; background: #f0f9ff; }
.el-upload__text { color: #64748b; }
.el-upload__text em { color: #0ea5e9; font-style: normal; }

:deep(.el-form-item__label) { color: #475569; }
:deep(.el-input__inner) { text-align: center; color: #1e293b; }

.primary-btn { width: 100%; height: 48px; font-size: 16px; border-radius: 12px; background: linear-gradient(135deg, #0ea5e9, #0284c7); border: none; margin-top: 10px; box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3); transition: all 0.3s; }
.primary-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(14, 165, 233, 0.4); }
</style>