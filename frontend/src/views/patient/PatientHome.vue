<template>
  <div class="patient-home">
    <el-row :gutter="24">
      <!-- ================= 左侧：日历与节气指南 ================= -->
      <el-col :span="16">
        <!-- 迎宾横幅 -->
        <div class="welcome-banner">
          <div class="banner-content">
            <h1>您好，{{ formStore.doctorName }} 👋</h1>
            <p>今天是 {{ todayStr }}（{{ todayLunar }} · {{ todayJieQi }}）。{{ seasonGreeting }}</p>
          </div>
          <div class="banner-illustration">🫁</div>
        </div>

        <el-row :gutter="24" style="margin-top: 24px;">
          <!-- 交互式双历日历 -->
          <el-col :span="14">
            <el-card class="soft-card calendar-card">
              <template #header>
                <div class="card-header">
                  <span>📅 我的健康日历</span>
                  <span class="selected-info">
                    已选：{{ formatDate(selectedDate) }} ({{ selectedLunar }})
                  </span>
                </div>
              </template>
              
              <el-calendar v-model="selectedDate" class="custom-calendar">
                <template #date-cell="{ data }">
                  <div :class="['custom-cell', { 'is-selected': data.isSelected }]">
                    <span class="solar-day">{{ data.day.split('-').slice(2).join('') }}</span>
                    <span class="lunar-text" :class="{ 'is-jieqi': getLunarInfo(data.day).jieQi }">
                      {{ getLunarInfo(data.day).text }}
                    </span>
                  </div>
                </template>
              </el-calendar>
            </el-card>
          </el-col>

          <!-- 节气保养指南 -->
          <el-col :span="10">
            <el-card class="soft-card" style="height: 100%;">
              <template #header>
                <div class="card-header">
                  <span>💡 {{ currentJieQi }}·养生指南</span>
                </div>
              </template>
              <div class="tips-list">
                <div class="tip-item">
                  <div class="tip-icon" style="color:#ef4444">🍎</div>
                  <div class="tip-text">
                    <h4>饮食调养</h4>
                    <p>{{ currentTips.diet }}</p>
                  </div>
                </div>
                <div class="tip-item">
                  <div class="tip-icon" style="color:#0ea5e9">🚶</div>
                  <div class="tip-text">
                    <h4>起居运动</h4>
                    <p>{{ currentTips.exercise }}</p>
                  </div>
                </div>
                <div class="tip-item">
                  <div class="tip-icon" style="color:#8b5cf6">💤</div>
                  <div class="tip-text">
                    <h4>精神作息</h4>
                    <p>{{ currentTips.sleep }}</p>
                  </div>
                </div>
                <div class="tip-item">
                  <div class="tip-icon" style="color:#10b981">🛡️</div>
                  <div class="tip-text">
                    <h4>疾病预防</h4>
                    <p>{{ currentTips.prevent }}</p>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-col>

      <!-- ================= 右侧：复查倒计时 & 快捷服务 & AI 管家 ================= -->
      <el-col :span="8">
        
        <!-- 复查倒计时卡片 -->
        <el-card class="soft-card review-card" style="margin-bottom: 24px;">
          <div class="review-content">
            <div class="review-text">
              <h3>下次复查倒计时</h3>
              <p v-if="hasHistory">根据上次评估结果，建议您于 {{ nextReviewDate }} 前复查。</p>
              <p v-else>您还没有评估记录，建议尽快完成首次 AI 评估。</p>
            </div>
            <div class="review-number" v-if="hasHistory">
              <span class="num">{{ daysToReview }}</span>
              <span class="unit">天</span>
            </div>
            <div class="review-number" v-else>
              <el-button type="primary" round size="small" @click="$router.push('/patient/report')">去评估</el-button>
            </div>
          </div>
        </el-card>

        <!-- 快捷服务 -->
        <el-card class="soft-card" style="margin-bottom: 24px;">
          <template #header>
            <div class="card-header"><span>⚡ 快捷服务</span></div>
          </template>
          <div class="quick-actions">
            <el-button type="primary" class="action-btn" @click="$router.push('/patient/report')">
              <el-icon size="20"><Folder /></el-icon> 查看我的结节报告
            </el-button>
            <el-button color="#10b981" class="action-btn" @click="$router.push('/patient/knowledge')">
              <el-icon size="20"><Reading /></el-icon> 学习肺部健康知识
            </el-button>
          </div>
        </el-card>

        <!-- AI 节气管家卡片 -->
        <el-card class="soft-card ai-weather-card">
          <template #header>
            <div class="card-header" style="color: #0284c7;">
              <span>🤖 AI 节气管家</span>
            </div>
          </template>
          <div class="weather-info">
            <div class="season-icon">{{ getSeasonIcon }}</div>
            <div>
              <h3>{{ currentJieQi }}</h3>
              <p style="font-size: 12px; color: #64748b;">为 {{ formatDate(selectedDate) }} 定制方案</p>
            </div>
          </div>
          
          <div class="ai-advice-box">
            <div class="typing-content">
              {{ aiSeasonAdvice || 'AI 管家正在分析该节气的气候特点...' }}
              <span class="cursor" v-if="isTyping">|</span>
            </div>
          </div>

          <el-button type="primary" plain style="width: 100%; margin-top: 15px;" @click="fetchAiAdvice" :loading="isTyping">
            重新获取 AI 建议
          </el-button>
        </el-card>
      </el-col>
    </el-row>

    <!-- AI 肺康日记 -->
    <el-card class="soft-card diary-card">
      <template #header>
        <div class="card-header" style="color: #0ea5e9;">
          <span>📝 AI 肺康日记 - 记录今天的感觉</span>
        </div>
      </template>
      <div class="diary-content">
        <div class="diary-input-area">
          <el-input 
            v-model="diaryText" 
            type="textarea" 
            :rows="3" 
            placeholder="今天有咳嗽吗？胸闷不闷？心情怎么样？简单记两笔吧..." 
            resize="none"
          />
          <el-button type="primary" class="diary-btn" @click="submitDiary" :loading="isDiaryTyping">
            🤖 让 AI 管家看看
          </el-button>
        </div>
        <div class="diary-ai-response" v-if="diaryFeedback || isDiaryTyping">
          <div class="ai-icon">👩‍⚕️</div>
          <div class="ai-text">
            <span v-if="isDiaryTyping && !diaryFeedback" class="thinking-dots">管家正在阅读您的日记...</span>
            <div v-else v-html="renderedDiaryText"></div>
            <span class="cursor" v-if="isDiaryTyping && diaryFeedback">|</span>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 底部：AI 健康日签 -->
    <div class="daily-quote-section">
      <div class="quote-card">
        <div class="quote-icon">🌿</div>
        <div class="quote-text">
          <h4>今日 AI 健康寄语</h4>
          <p>“{{ dailyQuote }}”</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useFormStore } from '../../stores/useFormStore'
import { Folder, Reading } from '@element-plus/icons-vue'
import { Solar } from 'lunar-javascript'
import { marked } from 'marked' // 用于渲染 Markdown
import { ElMessage } from 'element-plus'

const formStore = useFormStore()
const selectedDate = ref(new Date())

// ================= 时间与节气核心逻辑 =================
const formatDate = (date) => {
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const getLunarInfo = (dateStr) => {
  try {
    const [y, m, d] = dateStr.split('-')
    const solar = Solar.fromYmd(Number(y), Number(m), Number(d))
    const lunar = solar.getLunar()
    const jieQi = lunar.getJieQi()
    if (jieQi) return { text: jieQi, jieQi: true }
    const lunarDay = lunar.getDayInChinese()
    const text = lunarDay === '初一' ? `${lunar.getMonthInChinese()}月` : lunarDay
    return { text, jieQi: false }
  } catch (e) {
    return { text: '', jieQi: false }
  }
}

const todayStr = computed(() => new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }))
const todayLunarInfo = computed(() => getLunarInfo(formatDate(new Date())))
const todayLunar = computed(() => todayLunarInfo.value.jieQi ? '' : `农历${getLunarMonth(new Date())}${todayLunarInfo.value.text}`)
const todayJieQi = computed(() => todayLunarInfo.value.jieQi ? todayLunarInfo.value.text : getCurrentJieQi(new Date()))

const getLunarMonth = (date) => {
  const solar = Solar.fromDate(new Date(date))
  return solar.getLunar().getMonthInChinese() + '月'
}

const getCurrentJieQi = (date) => {
  const solar = Solar.fromDate(new Date(date))
  const lunar = solar.getLunar()
  return lunar.getJieQi() || lunar.getPrevJieQi(true).getName()
}

const currentJieQi = computed(() => getCurrentJieQi(selectedDate.value))
const selectedLunar = computed(() => getLunarMonth(selectedDate.value) + getLunarInfo(formatDate(selectedDate.value)).text)

const getSeasonIcon = computed(() => {
  const jq = currentJieQi.value
  if (['立春','雨水','惊蛰','春分','清明','谷雨'].includes(jq)) return '🌸'
  if (['立夏','小满','芒种','夏至','小暑','大暑'].includes(jq)) return '☀️'
  if (['立秋','处暑','白露','秋分','寒露','霜降'].includes(jq)) return '🍂'
  return '❄️'
})

const seasonGreeting = computed(() => {
  const jq = todayJieQi.value
  if (['立春','雨水','惊蛰','春分','清明','谷雨'].includes(jq)) return '春回大地，万物生发。注意防风保暖，防范过敏原。'
  if (['立夏','小满','芒种','夏至','小暑','大暑'].includes(jq)) return '夏日炎炎，暑热易伤肺气。注意防暑降温，保持室内通风。'
  if (['立秋','处暑','白露','秋分','寒露','霜降'].includes(jq)) return '秋燥伤肺，此时最宜滋阴润肺。注意多饮水，防秋燥。'
  return '冬藏时节，寒邪易侵。注意防寒保暖，晨练不宜过早。'
})

const currentTips = computed(() => {
  const jq = currentJieQi.value
  if (['立春','雨水','惊蛰','春分','清明','谷雨'].includes(jq)) {
    return { diet: '多吃韭菜、春笋等助阳升发之物，疏肝理气。', exercise: '宜踏青、散步。早晨不宜过早锻炼。', sleep: '早睡早起，顺应阳气生发。', prevent: '春季多风，花粉较多，外出建议佩戴口罩，预防哮喘发作。' }
  } else if (['立夏','小满','芒种','夏至','小暑','大暑'].includes(jq)) {
    return { diet: '饮食宜清淡，多吃西瓜、绿豆等清热解暑食品。', exercise: '避开高温时段，选择清晨或傍晚散步。', sleep: '晚睡早起，适当午休，空调温度勿过低。', prevent: '夏季湿热，注意防潮防霉，避免滋生细菌引发呼吸道感染。' }
  } else if (['立秋','处暑','白露','秋分','寒露','霜降'].includes(jq)) {
    return { diet: '润燥为主，多吃雪梨、百合、银耳等滋阴润肺食物。', exercise: '秋高气爽，适合慢跑、登山，但不宜大汗淋漓。', sleep: '早睡早起，收敛神气。注意室内保湿。', prevent: '秋燥易伤肺，注意多补充水分，避免咽喉干痛、干咳。' }
  } else {
    return { diet: '温补为主，适量吃羊肉、萝卜，提高抗寒能力。', exercise: '可进行室内运动，户外注意头背部保暖。', sleep: '早睡晚起，必待日光。养精蓄锐。', prevent: '冬季寒冷，是流感高发期，注意防寒保暖，勤洗手，少去人流密集处。' }
  }
})

// ================= 复查倒计时逻辑 =================
const hasHistory = computed(() => formStore.historyRecords.length > 0)

const nextReviewDate = computed(() => {
  if (!hasHistory.value) return ''
  const lastRecord = formStore.historyRecords[0]
  const lastDate = new Date(lastRecord.date)
  let addMonths = 12
  if (lastRecord.risk_level === '高风险') addMonths = 3
  else if (lastRecord.risk_level === '中风险') addMonths = 6
  
  lastDate.setMonth(lastDate.getMonth() + addMonths)
  return formatDate(lastDate)
})

const daysToReview = computed(() => {
  if (!hasHistory.value) return 0
  const targetDate = new Date(nextReviewDate.value)
  const today = new Date()
  const diffTime = targetDate - today
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  return diffDays > 0 ? diffDays : 0
})

// ================= AI 智能节气建议 =================
const aiSeasonAdvice = ref('')
const isTyping = ref(false)

const fetchAiAdvice = async () => {
  isTyping.value = true
  aiSeasonAdvice.value = ''
  const dateStr = formatDate(selectedDate.value)
  const lunarStr = selectedLunar.value
  const jq = currentJieQi.value

  const prompt = `今天是公历${dateStr}，农历${lunarStr}，当前处于二十四节气中的【${jq}】。请结合该节气的气候特点，为一位肺结节患者提供一段约150字的专属肺部保养建议（包含饮食和起居），语气温暖亲切。`

  const formData = new FormData()
  formData.append('question', prompt)

  try {
    const response = await fetch('/api/patient_ai_chat', { method: 'POST', body: formData })
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      aiSeasonAdvice.value += decoder.decode(value, { stream: true })
    }
  } catch (error) {
    aiSeasonAdvice.value = 'AI 管家暂时无法连接，请稍后重试。'
  } finally {
    isTyping.value = false
  }
}

watch(selectedDate, () => { fetchAiAdvice() })

// ================= AI 肺康日记逻辑 =================
const diaryText = ref('')
const diaryFeedback = ref('')
const isDiaryTyping = ref(false)
const renderedDiaryText = computed(() => marked(diaryFeedback.value))

const submitDiary = async () => {
  if (!diaryText.value.trim()) return ElMessage.warning('请先写点今天的感觉哦~')
  
  isDiaryTyping.value = true
  diaryFeedback.value = ''
  
  const formData = new FormData()
  formData.append('diary_text', diaryText.value)

  try {
    const response = await fetch('/api/diary_analysis', { method: 'POST', body: formData })
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      diaryFeedback.value += decoder.decode(value, { stream: true })
    }
  } catch (error) {
    diaryFeedback.value = '日记管家暂时无法连接，请稍后重试。'
  } finally {
    isDiaryTyping.value = false
  }
}

// ================= 每日金句逻辑 =================
const dailyQuote = ref('心平气和，肺气自降。良好的心态与规律的随访，是守护肺部健康最好的良药。')

onMounted(() => {
  fetchAiAdvice()
})
</script>

<style scoped>
.welcome-banner { background: linear-gradient(135deg, #0ea5e9, #0284c7); border-radius: 20px; padding: 40px; color: white; box-shadow: 0 10px 30px rgba(14, 165, 233, 0.2); position: relative; overflow: hidden; }
.banner-content h1 { margin: 0 0 10px 0; font-size: 32px; font-weight: 700; }
.banner-content p { margin: 0; font-size: 16px; opacity: 0.9; position: relative; z-index: 2; }
.banner-illustration { position: absolute; right: 20px; bottom: -20px; font-size: 160px; opacity: 0.15; transform: rotate(-15deg); z-index: 1; }

.soft-card { 
  border-radius: 16px; 
  border: 1px solid rgba(255, 255, 255, 0.8); 
  box-shadow: 0 10px 30px -10px rgba(2, 132, 199, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
  background: rgba(255, 255, 255, 0.95); 
  transition: all 0.3s; 
}
.soft-card:hover { transform: translateY(-3px); box-shadow: 0 20px 40px -10px rgba(2, 132, 199, 0.15); }
.card-header { font-weight: 600; font-size: 16px; color: #1e293b; display: flex; justify-content: space-between; align-items: center; }
.selected-info { font-size: 13px; color: #0284c7; font-weight: 500; }

.calendar-card { height: 100%; display: flex; flex-direction: column; }
.custom-calendar { flex: 1; background: transparent; }
.custom-calendar :deep(.el-calendar__header) { padding: 12px 20px; border-bottom: none; display: flex; justify-content: center; }
.custom-calendar :deep(.el-calendar__title) { font-size: 16px; font-weight: bold; color: #0f172a; }
.custom-calendar :deep(.el-calendar__button-group) { margin-top: 0; }
.custom-calendar :deep(.el-button-group button) { border-radius: 8px !important; border: 1px solid #e2e8f0; color: #475569; background: #fff; }
.custom-calendar :deep(.el-button-group button:hover) { color: #0ea5e9; border-color: #0ea5e9; }
.custom-calendar :deep(.el-calendar-table .el-calendar-day) { height: 65px; padding: 4px; }
.custom-cell { width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; border-radius: 8px; transition: all 0.2s; }
.solar-day { font-size: 16px; font-weight: 600; color: #1e293b; }
.lunar-text { font-size: 11px; color: #94a3b8; margin-top: 2px; }
.lunar-text.is-jieqi { color: #ea580c; font-weight: 600; }
.custom-cell.is-selected { background-color: #0ea5e9; box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3); }
.custom-cell.is-selected .solar-day, .custom-cell.is-selected .lunar-text { color: white; }

.tips-list { display: flex; flex-direction: column; gap: 16px; }
.tip-item { display: flex; align-items: flex-start; gap: 16px; padding: 16px; background: #f8fafc; border-radius: 12px; }
.tip-icon { font-size: 24px; background: white; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.tip-text h4 { margin: 0 0 6px 0; color: #1e293b; font-size: 14px; }
.tip-text p { margin: 0; color: #64748b; font-size: 13px; line-height: 1.5; }

.review-card { background: linear-gradient(135deg, #fff 0%, #f0f9ff 100%); border: 1px solid #bae6fd; }
.review-content { display: flex; justify-content: space-between; align-items: center; }
.review-text h3 { margin: 0 0 8px 0; font-size: 16px; color: #0284c7; }
.review-text p { margin: 0; font-size: 13px; color: #64748b; max-width: 180px; line-height: 1.5; }
.review-number .num { font-size: 36px; font-weight: 700; color: #ea580c; }
.review-number .unit { font-size: 14px; color: #ea580c; margin-left: 4px; }

.quick-actions { display: flex; flex-direction: column; gap: 16px; }
.action-btn { width: 100%; height: 50px; border-radius: 12px; font-size: 15px; display: flex; justify-content: flex-start; padding-left: 20px; gap: 12px; border: none; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.action-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,0.1); }

.ai-weather-card { background: linear-gradient(180deg, #ffffff 0%, #f0f9ff 100%); }
.weather-info { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.season-icon { font-size: 40px; }
.weather-info h3 { margin: 0 0 4px 0; font-size: 18px; color: #0f172a; }
.ai-advice-box { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; min-height: 120px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.02); }
.typing-content { font-size: 14px; line-height: 1.6; color: #334155; }

.cursor { animation: blink 1s step-end infinite; color: #0ea5e9; font-weight: bold; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

.diary-card { margin-top: 24px; border: 1px solid #bae6fd; }
.diary-content { display: flex; gap: 24px; }
.diary-input-area { flex: 1; display: flex; flex-direction: column; gap: 12px; }
.diary-input-area :deep(.el-textarea__inner) { border-radius: 12px; background-color: #f8fafc; font-size: 14px; padding: 12px; }
.diary-btn { align-self: flex-end; border-radius: 8px; background: linear-gradient(135deg, #0ea5e9, #0284c7); border: none; }
.diary-ai-response { flex: 1; background: #f0fdf4; border: 1px dashed #86efac; border-radius: 12px; padding: 16px; display: flex; gap: 12px; align-items: flex-start; }
.ai-icon { font-size: 24px; background: white; padding: 6px; border-radius: 50%; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.ai-text { font-size: 14px; color: #166534; line-height: 1.6; }
.thinking-dots { animation: pulse 1.5s infinite; color: #16a34a; font-weight: 500; }
@keyframes pulse { 0%, 100% { opacity: 0.5; } 50% { opacity: 1; } }

.daily-quote-section { margin-top: 24px; }
.quote-card { background: #ecfdf5; border: 1px dashed #a7f3d0; border-radius: 16px; padding: 20px 30px; display: flex; align-items: center; gap: 20px; }
.quote-icon { font-size: 30px; }
.quote-text h4 { margin: 0 0 6px 0; color: #047857; font-size: 16px; }
.quote-text p { margin: 0; color: #065f46; font-size: 15px; font-style: italic; letter-spacing: 0.5px; }
</style>