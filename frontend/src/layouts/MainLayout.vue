<template>
  <el-container class="layout-container">
    <!-- ================= 顶部导航栏 (毛玻璃质感) ================= -->
    <el-header class="top-header">
      <div class="header-content">
        <!-- 左侧 Logo -->
        <div class="logo">
          <span class="logo-icon">🫁</span>
          <span class="logo-text">智影时序 AI</span>
          <span class="role-tag">{{ formStore.role === 'doctor' ? '医生端' : '患者端' }}</span>
        </div>

        <!-- 中间 菜单 -->
        <el-menu :default-active="route.path" class="top-menu" mode="horizontal" router>
          <template v-if="formStore.role === 'doctor'">
            <el-menu-item index="/workbench"><el-icon><Monitor /></el-icon> 评估工作台</el-menu-item>
            <el-menu-item index="/history"><el-icon><Document /></el-icon> 历史档案</el-menu-item>
          </template>
          <template v-else>
            <el-menu-item index="/patient/home"><el-icon><House /></el-icon> 健康首页</el-menu-item>
            <el-menu-item index="/patient/report"><el-icon><Folder /></el-icon> 检查报告</el-menu-item>
            <el-menu-item index="/patient/knowledge"><el-icon><Reading /></el-icon> 健康科普</el-menu-item>
          </template>
          <el-menu-item index="/profile"><el-icon><User /></el-icon> 个人中心</el-menu-item>
        </el-menu>

        <!-- 右侧 用户信息 -->
        <div class="user-info">
          <el-avatar :size="34" :src="formStore.role === 'doctor' ? 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png' : 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'" />
          <span class="user-name">{{ formStore.doctorName }}</span>
          <el-button type="danger" text size="small" @click="handleLogout">退出</el-button>
        </div>
      </div>
    </el-header>

    <el-main class="main-content">
      <router-view></router-view>
    </el-main>

    <!-- 患者端悬浮 AI 助理 -->
    <div v-if="formStore.role === 'patient' && route.path !== '/login'">
      <el-button type="primary" circle class="float-ai-btn" @click="showAiChat = !showAiChat">
        <el-icon size="24"><ChatDotRound /></el-icon>
      </el-button>
      <div class="float-chat-box" v-show="showAiChat">
        <div class="chat-header">
          <span style="font-weight: 600; color: #0f172a; font-size: 15px;">🫁 AI 肺部健康助理</span>
          <el-button link @click="showAiChat = false">✖</el-button>
        </div>
        <div class="chat-history" v-html="renderedChat"></div>
        <div class="chat-input-area">
          <el-input v-model="patientQuestion" placeholder="例如：吃什么对肺好？" @keyup.enter="askPatientAi" />
          <el-button type="primary" @click="askPatientAi" :loading="isPatientTyping">发送</el-button>
        </div>
      </div>
    </div>
  </el-container>
</template>

<script setup>
import { Monitor, Document, House, Folder, Reading, ChatDotRound, User } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'
import { useFormStore } from '../stores/useFormStore'
import { ref, computed } from 'vue'
import { marked } from 'marked'

const route = useRoute()
const router = useRouter()
const formStore = useFormStore()

const handleLogout = () => { formStore.logout(); router.push('/login') }

const showAiChat = ref(false)
const patientQuestion = ref('')
const chatText = ref('您好，我是您的 AI 健康助理，有什么可以帮您？\n\n')
const isPatientTyping = ref(false)
const renderedChat = computed(() => marked(chatText.value))

const askPatientAi = async () => {
  if (!patientQuestion.value.trim()) return
  const q = patientQuestion.value
  chatText.value += `\n\n**👤 您：** ${q}\n\n**🫁 助理：**\n`
  patientQuestion.value = ''
  isPatientTyping.value = true
  const formData = new FormData(); formData.append('question', q)
  try {
    const response = await fetch('/api/patient_ai_chat', { method: 'POST', body: formData })
    const reader = response.body.getReader(); const decoder = new TextDecoder('utf-8')
    while (true) {
      const { done, value } = await reader.read(); if (done) break
      chatText.value += decoder.decode(value, { stream: true })
    }
  } catch (error) { chatText.value += '\n[网络异常，稍后再试]' } finally { isPatientTyping.value = false }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
  /* 恢复为清透的浅蓝灰渐变背景 */
  background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 100%);
  background-attachment: fixed;
}

.top-header {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.03);
  padding: 0;
  z-index: 100;
  position: sticky;
  top: 0;
}

.header-content { display: flex; align-items: center; justify-content: space-between; height: 100%; max-width: 1400px; margin: 0 auto; padding: 0 32px; }
.logo { display: flex; align-items: center; gap: 12px; }
.logo-icon { font-size: 24px; }
.logo-text { font-size: 20px; font-weight: 700; color: #0f172a; letter-spacing: -0.5px; }
.role-tag { font-size: 12px; background: #e0f2fe; color: #0284c7; padding: 2px 10px; border-radius: 20px; font-weight: 600; }

.top-menu { border-bottom: none; flex: 1; justify-content: center; background: transparent; }
:deep(.el-menu--horizontal > .el-menu-item) { border-bottom: none; height: 40px; line-height: 40px; margin: 12px 8px; font-size: 15px; font-weight: 500; color: #64748b; border-radius: 10px; transition: all 0.2s; }
:deep(.el-menu--horizontal > .el-menu-item:hover) { background-color: #f1f5f9; color: #0f172a; }
:deep(.el-menu--horizontal > .el-menu-item.is-active) { color: #0284c7; background-color: #f0f9ff; font-weight: 600; }

.user-info { display: flex; align-items: center; gap: 12px; }
.user-name { font-size: 14px; font-weight: 500; color: #1e293b; }

.main-content { padding: 32px 40px; max-width: 1600px; margin: 0 auto; width: 100%; box-sizing: border-box; }

.float-ai-btn { position: fixed; right: 40px; bottom: 40px; width: 60px; height: 60px; box-shadow: 0 8px 24px rgba(14, 165, 233, 0.4); z-index: 1000; background: linear-gradient(135deg, #0ea5e9, #0284c7); border: none; }
.float-chat-box { position: fixed; right: 40px; bottom: 120px; width: 380px; height: 540px; z-index: 1000; display: flex; flex-direction: column; background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.5); box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1); border-radius: 20px; overflow: hidden; }
.chat-header { padding: 16px 20px; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center; }
.chat-history { flex: 1; overflow-y: auto; font-size: 14px; line-height: 1.6; padding: 20px; color: #334155; }
.chat-history :deep(p) { margin-top: 0; margin-bottom: 10px; }
.chat-history :deep(strong) { color: #0284c7; }
.chat-input-area { padding: 16px 20px; border-top: 1px solid #f1f5f9; display: flex; gap: 12px; background: white; }
</style>