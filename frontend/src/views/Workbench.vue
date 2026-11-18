<template>
  <el-row :gutter="24">
    <el-col :span="8">
      <WorkbenchForm :loading="loading" @start-predict="startPredict" />
    </el-col>
    <el-col :span="16">
      <el-card class="soft-card result-card" style="height: 100%;">
        <template #header><span class="card-header">智能诊断报告</span></template>
        
        <div v-if="!result" class="empty-state">
          <div class="empty-icon">🫁</div>
          <h3>等待影像评估</h3>
          <p>请在左侧配置参数并点击“启动评估”</p>
        </div>
        
        <div v-else>
          <RiskReport :result="result" />
          <AiDoctorChat v-if="aiText || isTyping" :ai-text="aiText" :is-typing="isTyping" @ask-question="askQuestion" />
        </div>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useFormStore } from '../stores/useFormStore'
import WorkbenchForm from '../components/WorkbenchForm.vue'
import RiskReport from '../components/RiskReport.vue'
import AiDoctorChat from '../components/AiDoctorChat.vue'

const formStore = useFormStore()
const loading = ref(false)
const result = ref(null)
const aiText = ref('')
const isTyping = ref(false)

const startPredict = async () => {
  const form = formStore.form
  if (!form.file_cur || !form.file_pri) return ElMessage.warning('请同时上传两次 CT 影像')
  
  loading.value = true; result.value = null; aiText.value = ''
  const formData = new FormData()
  formData.append('file_cur', form.file_cur); formData.append('file_pri', form.file_pri)
  formData.append('cur_coord_x', form.cur_coordX); formData.append('cur_coord_y', form.cur_coordY); formData.append('cur_coord_z', form.cur_coordZ)
  formData.append('pri_coord_x', form.pri_coordX); formData.append('pri_coord_y', form.pri_coordY); formData.append('pri_coord_z', form.pri_coordZ)
  formData.append('months', form.months)

  try {
    const res = await axios.post('/api/predict', formData)
    if (isNaN(res.data.risk_prob)) return ElMessage.error('AI 计算异常')
    result.value = res.data
    ElMessage.success('AI 评估完成！')
    formStore.addHistory(res.data)
    fetchAiExplanation() 
  } catch (error) { ElMessage.error('评估失败') } finally { loading.value = false }
}

const fetchAiExplanation = async (questionText = '') => {
  isTyping.value = true
  const formData = new FormData()
  formData.append('risk_level', result.value.risk_level)
  formData.append('risk_prob', result.value.risk_prob)
  formData.append('volume_mm3', result.value.volume_mm3)
  formData.append('question', questionText)
  
  try {
    const response = await fetch('/api/ai_explain', { method: 'POST', body: formData })
    const reader = response.body.getReader(); const decoder = new TextDecoder('utf-8')
    while (true) {
      const { done, value } = await reader.read(); if (done) break
      aiText.value += decoder.decode(value, { stream: true })
    }
  } catch (error) { aiText.value += '\n[系统提示] AI 医生连接失败。' } finally { isTyping.value = false }
}

const askQuestion = (question) => {
  aiText.value += `\n\n**👤 患者家属：** ${question}\n\n**👨‍⚕️ AI 医生：**\n`
  fetchAiExplanation(question)
}
</script>

<style scoped>
.soft-card { 
  border-radius: 16px; 
  border: 1px solid rgba(255, 255, 255, 0.8); 
  box-shadow: 0 10px 30px -10px rgba(2, 132, 199, 0.1), 
              0 4px 6px -2px rgba(0, 0, 0, 0.02);
  background: rgba(255, 255, 255, 0.95);
  transition: all 0.3s ease;
}
.soft-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 20px 40px -10px rgba(2, 132, 199, 0.15);
}

.card-header { font-weight: 600; font-size: 18px; color: #1e293b; }

.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; min-height: 400px; color: #64748b; }
.empty-icon { font-size: 80px; opacity: 0.2; margin-bottom: 20px; filter: grayscale(100%); }
.empty-state h3 { margin: 0 0 10px 0; font-size: 18px; font-weight: 500; color: #475569; }
.empty-state p { margin: 0; font-size: 14px; }
</style>