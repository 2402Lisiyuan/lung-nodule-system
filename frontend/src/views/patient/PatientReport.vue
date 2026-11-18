<template>
  <div class="patient-report-container">
    
    <!-- ================= 顶部：发起评估区域 ================= -->
    <el-card class="soft-card" style="margin-bottom: 30px;">
      <template #header>
        <div class="card-header">
          <span> AI 智能评估</span>
          <span class="sub-title">如果您手头有近期的肺部 CT 影像，可在此上传获取 AI 辅助解读</span>
        </div>
      </template>

      <el-row :gutter="24">
        <!-- 左半部分：表单 -->
        <el-col :span="8">
          <el-form label-position="top">
            <!-- 当前 CT -->
            <div class="param-group">
              <h4 class="group-title">🕒 当前 CT</h4>
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

            <!-- 先前 CT -->
            <div class="param-group" style="margin-top: 16px;">
              <h4 class="group-title">📅 先前 CT</h4>
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

            <el-button type="primary" size="large" class="primary-btn" :loading="loading" @click="startPredict">
              启动评估并保存档案
            </el-button>
          </el-form>
        </el-col>

        <!-- 右半部分：评估结果 -->
        <el-col :span="16">
          <div v-if="!result" class="empty-state">
            <div class="empty-icon">🫁</div>
            <h3>等待发起评估</h3>
            <p>请在左侧上传两次 CT 影像并点击启动评估</p>
          </div>
          
          <div v-else class="result-content">
            <div :class="['risk-card', result.risk_level === '高风险' ? 'bg-danger' : (result.risk_level === '中风险' ? 'bg-warning' : 'bg-success')]">
              <h2>{{ result.risk_level }}</h2>
              <div class="probability">{{ (result.risk_prob * 100).toFixed(1) }}%</div>
              <p>3年恶性风险概率</p>
            </div>
            
            <div class="data-grid">
              <div class="data-item">
                <span class="data-label">当前结节体积</span>
                <span class="data-value">{{ result.volume_mm3 }} <small>mm³</small></span>
              </div>
              <div class="data-item">
                <span class="data-label">AI 诊断建议</span>
                <span class="data-value" style="font-size: 16px; color: #0ea5e9;">请查看下方详细解读</span>
              </div>
            </div>

            <div class="chart-container">
              <div ref="chartRef" style="width: 100%; height: 220px;"></div>
            </div>

            <!-- AI 医生解读区 -->
            <div class="ai-doctor-box" v-if="aiText || isTyping">
              <div class="ai-header" :class="{ 'ai-typing': isTyping }">
                <div class="avatar-wrapper">👨‍⚕️</div>
                <div>
                  <div class="ai-title">AI 主治医师解读</div>
                  <div class="ai-subtitle">基于大模型实时生成</div>
                </div>
              </div>
              
              <div class="ai-content">
                <div v-html="renderedAiText" style="display: inline;"></div>
                <span class="cursor" v-if="isTyping">|</span>
              </div>
              
              <div class="ai-input-area" v-if="!isTyping">
                <el-input v-model="aiQuestion" placeholder="针对报告继续追问..." @keyup.enter="askQuestion" size="large" />
                <el-button :type="isListening ? 'danger' : 'default'" size="large" @click="toggleVoiceInput" :icon="Microphone" circle />
                <el-button type="primary" size="large" @click="askQuestion">发送</el-button>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- ================= 底部：我的历史健康档案时间线 ================= -->
    <div class="history-section">
      <div class="page-header">
        <h2>我的历史健康档案</h2>
        <p>在这里，您可以随时查看历次 AI 辅助评估报告。</p>
      </div>

      <el-empty v-if="historyRecords.length === 0" description="暂无随访记录" />

      <el-timeline v-else style="margin-top: 30px; max-width: 800px; margin-left: auto; margin-right: auto;">
        <el-timeline-item
          v-for="(record, index) in historyRecords"
          :key="index"
          :timestamp="record.date"
          placement="top"
          :color="getTagColor(record.risk_level)"
          :size="index === 0 ? 'large' : 'normal'"
          :hollow="index !== 0"
        >
          <el-card shadow="hover" class="report-card">
            <div class="card-content">
              <div class="left-info">
                <h3>
                  随访评估结果：
                  <el-tag :type="getTagType(record.risk_level)" effect="dark">
                    {{ record.risk_level }}
                  </el-tag>
                </h3>
                <p class="probability-text">
                  3年恶性风险概率：<span :style="{ color: getTagColor(record.risk_level) }">{{ (record.risk_prob * 100).toFixed(1) }}%</span>
                </p>
                <p class="volume-text">结节体积：{{ record.volume_mm3 }} mm³</p>
              </div>
              
              <div class="right-action">
                <el-button type="primary" plain round @click="openReportDetail(record)">
                  查看详细报告
                </el-button>
              </div>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </div>

    <!-- 历史报告详情弹窗 -->
    <el-dialog v-model="dialogVisible" title="📋 AI 智能辅助评估报告" width="600px" align-center>
      <div v-if="currentRecord" class="dialog-content">
        <div class="report-header" :style="{ backgroundColor: getLightColor(currentRecord.risk_level) }">
          <h2>{{ currentRecord.risk_level }}</h2>
          <div class="report-score">{{ (currentRecord.risk_prob * 100).toFixed(1) }}%</div>
          <p>3年恶性风险概率</p>
        </div>
        
        <div class="report-body">
          <h4>📝 临床指标分析</h4>
          <p><b>当前结节体积：</b> {{ currentRecord.volume_mm3 }} mm³</p>
          <p><b>评估时间：</b> {{ currentRecord.date }}</p>
          
          <h4>🫁 健康随访建议</h4>
          <el-alert :title="getHealthAdvice(currentRecord.risk_level)" type="info" :closable="false" show-icon />
          
          <div class="disclaimer" style="margin-top: 20px; font-size: 12px; color: #999;">
            * 本报告由人工智能算法辅助生成，仅供临床参考，不能替代医生的最终诊断。请务必遵从您的主治医生的建议。
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onUnmounted } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'
import { marked } from 'marked'
import { Microphone } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useFormStore } from '../../stores/useFormStore'
import { storeToRefs } from 'pinia'

// ================= 状态管理 =================
const formStore = useFormStore()
const { form, saveForm, historyRecords } = storeToRefs(formStore)

const loading = ref(false)
const result = ref(null)
const aiText = ref('')
const isTyping = ref(false)
const aiQuestion = ref('')
const chartRef = ref(null)
let myChart = null

const isListening = ref(false)
let recognition = null
const renderedAiText = computed(() => marked(aiText.value))

// 历史记录弹窗状态
const dialogVisible = ref(false)
const currentRecord = ref(null)

// 语音识别初始化
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  recognition = new SpeechRecognition()
  recognition.lang = 'zh-CN'
  recognition.onstart = () => { isListening.value = true }
  recognition.onend = () => { isListening.value = false }
  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript
    aiQuestion.value = transcript
    if (transcript.trim()) askQuestion()
  }
}
const toggleVoiceInput = () => {
  if (!recognition) return ElMessage.warning('不支持语音识别')
  isListening.value ? recognition.stop() : recognition.start()
}
onUnmounted(() => { if (recognition) recognition.stop() })

// ================= 影像上传 =================
const customUpload = async (options, type) => {
  const formData = new FormData()
  formData.append('file', options.file)
  try {
    loading.value = true
    const res = await axios.post('/api/upload', formData)
    if (type === 'cur') form.value.file_cur = res.data.filename
    else form.value.file_pri = res.data.filename
    saveForm.value() 
    ElMessage.success('影像加载成功！')
  } catch (error) { ElMessage.error('上传失败') } finally { loading.value = false }
}

// ================= 启动评估 =================
const startPredict = async () => {
  if (!form.value.file_cur || !form.value.file_pri) return ElMessage.warning('请同时上传两次 CT 影像')
  loading.value = true; result.value = null; aiText.value = ''
  if (myChart) { myChart.dispose(); myChart = null; }

  const formData = new FormData()
  formData.append('file_cur', form.value.file_cur); formData.append('file_pri', form.value.file_pri)
  formData.append('cur_coord_x', form.value.cur_coordX); formData.append('cur_coord_y', form.value.cur_coordY); formData.append('cur_coord_z', form.value.cur_coordZ)
  formData.append('pri_coord_x', form.value.pri_coordX); formData.append('pri_coord_y', form.value.pri_coordY); formData.append('pri_coord_z', form.value.pri_coordZ)
  formData.append('months', form.value.months)

  try {
    const res = await axios.post('/api/predict', formData)
    if (isNaN(res.data.risk_prob)) return ElMessage.error('AI 计算异常')
    
    result.value = res.data
    ElMessage.success('评估完成！已存入您的健康档案')
    // 核心：将结果保存到 Pinia 全局状态，下方时间线会自动更新
    formStore.addHistory(res.data)
    
    renderChart()
    fetchAiExplanation() 
  } catch (error) { ElMessage.error('评估失败') } finally { loading.value = false }
}

// ================= 图表渲染 =================
const renderChart = () => {
  nextTick(() => {
    if (chartRef.value) {
      if (!myChart) myChart = echarts.init(chartRef.value)
      const baseRisk = result.value.risk_prob * 100
      const option = {
        title: { text: '未来3年风险演化趋势', left: 'center', textStyle: { fontSize: 13 } },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: ['当前', '1年后', '2年后', '3年后'] },
        yAxis: { type: 'value', min: 0, max: 100, axisLabel: { formatter: '{value}%' } },
        series: [{ data: [baseRisk, baseRisk * 1.1, baseRisk * 1.25, baseRisk * 1.4].map(v => Math.min(v, 100).toFixed(1)), type: 'line', smooth: true, itemStyle: { color: '#e53935' }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(229,57,53,0.4)' }, { offset: 1, color: 'rgba(229,57,53,0.05)' }]) } }]
      }
      myChart.setOption(option)
    }
  })
}

// ================= AI 解读 =================
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
  } catch (error) { aiText.value += '\n[系统提示] AI 连接失败。' } finally { isTyping.value = false }
}

const askQuestion = () => {
  if (!aiQuestion.value.trim()) return
  aiText.value += `\n\n**👤 您：** ${aiQuestion.value}\n\n**👨‍⚕️ AI 医生：**\n`
  fetchAiExplanation(aiQuestion.value)
  aiQuestion.value = ''
}

// ================= 历史档案辅助函数 =================
const openReportDetail = (record) => {
  currentRecord.value = record
  dialogVisible.value = true
}
const getTagType = (level) => {
  if (level === '高风险') return 'danger'
  if (level === '中风险') return 'warning'
  return 'success'
}
const getTagColor = (level) => {
  if (level === '高风险') return '#f56c6c'
  if (level === '中风险') return '#e6a23c'
  return '#67c23a'
}
const getLightColor = (level) => {
  if (level === '高风险') return '#fef0f0'
  if (level === '中风险') return '#fdf6ec'
  return '#f0f9eb'
}
const getHealthAdvice = (level) => {
  if (level === '高风险') return '该结节当前被评估为高风险，建议您尽快携带原始影像资料，前往三甲医院就诊。'
  if (level === '中风险') return '该结节目前被评估为中风险，建议您按照医生要求进行定期随访（通常为6个月）。'
  return '该结节当前被评估为低风险，通常无需过度干预。建议您保持正常的一年一次年度体检。'
}
</script>

<style scoped>
.patient-report-container { max-width: 1200px; margin: 0 auto; padding-bottom: 40px; }
.soft-card { border-radius: var(--card-radius); border: 1px solid rgba(255, 255, 255, 0.6); box-shadow: var(--card-shadow); background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(10px); }
.card-header { font-weight: 600; font-size: 18px; color: var(--text-main); display: flex; align-items: center; gap: 10px; }
.sub-title { font-size: 13px; color: var(--text-sub); font-weight: normal; }

/* 表单样式 */
.param-group { background: #fafcff; padding: 16px; border-radius: 12px; border: 1px solid #e2e8f0; }
.group-title { margin: 0 0 12px 0; color: #0ea5e9; font-size: 15px; font-weight: 600; }
.custom-upload :deep(.el-upload-dragger) { padding: 16px; border-radius: 8px; border: 2px dashed #cbd5e1; background: white; transition: all 0.2s; }
.custom-upload :deep(.el-upload-dragger:hover) { border-color: #0ea5e9; background: #f0f9ff; }
.primary-btn { width: 100%; height: 48px; font-size: 16px; border-radius: 12px; background: linear-gradient(135deg, #0ea5e9, #0284c7); border: none; margin-top: 10px; }
:deep(.el-input__inner) { text-align: center; }

/* 空状态 */
.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; min-height: 300px; color: var(--text-sub); }
.empty-icon { font-size: 70px; opacity: 0.2; margin-bottom: 20px; filter: grayscale(100%); }
.empty-state h3 { margin: 0 0 10px 0; font-size: 18px; font-weight: 500; color: #475569; }

/* 评估结果卡片 */
.risk-card { text-align: center; padding: 30px 20px; border-radius: 16px; color: white; margin-bottom: 20px; }
.bg-danger { background: linear-gradient(135deg, #ff7a7a, #e53935); box-shadow: 0 10px 24px rgba(229, 57, 53, 0.2); }
.bg-warning { background: linear-gradient(135deg, #fbbf24, #f59e0b); box-shadow: 0 10px 24px rgba(245, 158, 11, 0.2); }
.bg-success { background: linear-gradient(135deg, #34d399, #059669); box-shadow: 0 10px 24px rgba(5, 150, 105, 0.2); }
.risk-card h2 { margin: 0; font-size: 22px; font-weight: 500; letter-spacing: 1px; }
.risk-card .probability { font-size: 60px; font-weight: 700; margin: 5px 0; }
.risk-card p { margin: 0; font-size: 14px; opacity: 0.9; }

.data-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }
.data-item { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; display: flex; flex-direction: column; gap: 6px; }
.data-label { font-size: 13px; color: var(--text-sub); }
.data-value { font-size: 22px; font-weight: 700; color: var(--text-main); }

.chart-container { border: 1px solid #f1f5f9; border-radius: 12px; padding: 10px; background: white; margin-bottom: 20px; }

/* AI 医生 */
.ai-doctor-box { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
.ai-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; border-bottom: 1px solid #f1f5f9; padding-bottom: 12px; }
.avatar-wrapper { font-size: 24px; background: #f0f9ff; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border-radius: 10px; }
.ai-title { font-weight: 600; color: var(--text-main); font-size: 15px; }
.ai-subtitle { font-size: 12px; color: var(--text-sub); }
.ai-content { line-height: 1.7; color: #334155; font-size: 14px; max-height: 300px; overflow-y: auto; padding-right: 10px; }
.ai-content :deep(p) { margin-top: 0; margin-bottom: 10px; }
.ai-content :deep(strong) { color: #0ea5e9; }
.ai-input-area { margin-top: 15px; display: flex; gap: 10px; align-items: center; }
.cursor { animation: blink 1s step-end infinite; color: #0ea5e9; font-weight: bold; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

/* 历史档案时间线 */
.history-section { margin-top: 40px; }
.page-header { text-align: center; margin-bottom: 30px; }
.page-header h2 { color: #0f172a; font-size: 24px; margin-bottom: 10px; }
.page-header p { color: #64748b; font-size: 14px; }
.report-card { border-radius: 12px; border: 1px solid #e2e8f0; background: rgba(255, 255, 255, 0.9); }
.card-content { display: flex; justify-content: space-between; align-items: center; }
.left-info h3 { margin: 0 0 10px 0; color: #0f172a; font-size: 16px; }
.probability-text { margin: 0 0 5px 0; font-size: 15px; color: #334155; }
.probability-text span { font-size: 24px; font-weight: bold; }
.volume-text { margin: 0; font-size: 13px; color: #64748b; }
.dialog-content { border-radius: 8px; overflow: hidden; }
.report-header { text-align: center; padding: 30px; border-radius: 8px; margin-bottom: 20px; }
.report-header h2 { margin: 0; color: #333; }
.report-score { font-size: 48px; font-weight: bold; color: #333; margin: 10px 0; }
.report-body h4 { color: #0284c7; margin-top: 20px; margin-bottom: 10px; border-left: 4px solid #0284c7; padding-left: 10px; }
.report-body p { line-height: 1.8; color: #334155; }
</style>