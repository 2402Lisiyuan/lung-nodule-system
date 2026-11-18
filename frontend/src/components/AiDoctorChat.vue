<template>
  <div class="ai-doctor-box">
    <div class="ai-header" :class="{ 'ai-typing': isTyping }">
      <div class="avatar-wrapper">👨‍⚕️</div>
      <div>
        <div class="ai-title">AI 主治医师</div>
        <div class="ai-subtitle">基于大模型与指南库实时生成</div>
      </div>
    </div>
    
    <div class="ai-content">
      <div v-if="isTyping && !aiText" class="ai-thinking">
        <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        <span class="thinking-text">正在调取医学知识库并深度分析...</span>
      </div>
      <div v-html="renderedAiText" style="display: inline;"></div>
      <span class="cursor" v-if="isTyping && aiText">|</span>
    </div>

    <div class="quick-chips" v-if="!isTyping && aiText">
      <span class="chip" @click="submitQuestion('如果结节长到了10mm，风险大吗？体积是多少？')">测算 10mm 结节风险与体积</span>
      <span class="chip" @click="submitQuestion('根据最新指南，我这种情况应该多久复查一次？')">查询指南复查建议</span>
      <span class="chip" @click="submitQuestion('日常饮食需要注意什么？')">饮食指导</span>
    </div>
    
    <div class="ai-input-area" v-if="!isTyping">
      <el-input v-model="aiQuestion" placeholder="针对报告继续追问..." @keyup.enter="submitQuestion(aiQuestion)" size="large" />
      <el-button :type="isListening ? 'danger' : 'default'" size="large" @click="toggleVoiceInput" :icon="Microphone" circle />
      <el-button type="primary" size="large" @click="submitQuestion(aiQuestion)">发送</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { marked } from 'marked'
import { Microphone } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({ aiText: { type: String, default: '' }, isTyping: { type: Boolean, default: false } })
const emit = defineEmits(['ask-question'])

const aiQuestion = ref('')
const isListening = ref(false)
let recognition = null

const renderedAiText = computed(() => marked(props.aiText))

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  recognition = new SpeechRecognition()
  recognition.lang = 'zh-CN'
  recognition.onstart = () => { isListening.value = true }
  recognition.onend = () => { isListening.value = false }
  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript
    aiQuestion.value = transcript
    if (transcript.trim()) submitQuestion(transcript)
  }
}

const toggleVoiceInput = () => {
  if (!recognition) return ElMessage.warning('不支持语音识别')
  isListening.value ? recognition.stop() : recognition.start()
}

const submitQuestion = (question) => {
  const q = typeof question === 'string' ? question : aiQuestion.value
  if (!q.trim()) return
  emit('ask-question', q)
  aiQuestion.value = ''
}

onUnmounted(() => { if (recognition) recognition.stop() })
</script>

<style scoped>
.ai-doctor-box { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; margin-top: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
.ai-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; border-bottom: 1px solid #f1f5f9; padding-bottom: 16px; }
.avatar-wrapper { font-size: 28px; background: #f0f9ff; width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; border-radius: 12px; }
.ai-title { font-weight: 600; color: #1e293b; font-size: 16px; }
.ai-subtitle { font-size: 12px; color: #64748b; }
.ai-content { line-height: 1.8; color: #334155; font-size: 15px; max-height: 350px; overflow-y: auto; padding-right: 10px; }
.ai-content :deep(p) { margin-top: 0; margin-bottom: 12px; }
.ai-content :deep(strong) { color: #0ea5e9; }

.quick-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }
.chip { background: #f0f9ff; color: #0284c7; border: 1px solid #bae6fd; padding: 6px 12px; border-radius: 20px; font-size: 13px; cursor: pointer; transition: all 0.2s; }
.chip:hover { background: #e0f2fe; transform: translateY(-1px); box-shadow: 0 2px 8px rgba(14, 165, 233, 0.15); }

.ai-input-area { margin-top: 20px; display: flex; gap: 12px; align-items: center; }

.cursor { animation: blink 1s step-end infinite; color: #0ea5e9; font-weight: bold; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
.ai-thinking { display: flex; align-items: center; gap: 4px; color: #0ea5e9; font-size: 14px; padding: 10px 0; }
.ai-thinking .dot { width: 6px; height: 6px; background-color: #0ea5e9; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; }
.ai-thinking .dot:nth-child(1) { animation-delay: -0.32s; }
.ai-thinking .dot:nth-child(2) { animation-delay: -0.16s; }
.ai-thinking .dot:nth-child(3) { animation-delay: 0s; }
.thinking-text { margin-left: 8px; font-weight: 500; opacity: 0.8; }
@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
</style>