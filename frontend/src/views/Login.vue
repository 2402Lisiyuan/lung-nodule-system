<template>
  <div class="login-container">
    <!-- 背景装饰 -->
    <div class="grid-overlay"></div>
    <div class="glow glow-1"></div>
    <div class="glow glow-2"></div>
    <div class="glow glow-3"></div>

    <div class="login-box">
      <div class="login-header">
        <h1>🫁 智影时序 AI</h1>
        <p>肺结节全周期智能随访平台</p>
      </div>
      
      <div class="role-selector">
        <div :class="['role-card', { active: selectedRole === 'doctor' }]" @click="selectedRole = 'doctor'">
          <div class="icon">👨‍⚕️</div>
          <h3>我是医生</h3>
        </div>
        <div :class="['role-card', { active: selectedRole === 'patient' }]" @click="selectedRole = 'patient'">
          <div class="icon">🤒</div>
          <h3>我是患者</h3>
        </div>
      </div>

      <el-form label-position="top" class="login-form" style="margin-top: 20px;">
        <el-form-item label="账号 / 手机号">
          <el-input v-model="username" placeholder="请输入账号" size="large" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="password" type="password" placeholder="请输入密码" size="large" show-password />
        </el-form-item>
        
        <div class="test-hint">
          <p>医生测试号: doctor / doctor123</p>
          <p>患者测试号: patient / patient123</p>
        </div>

        <div style="display: flex; gap: 10px; margin-top: 20px;">
          <el-button type="primary" size="large" style="flex: 1;" :loading="loading" @click="handleLogin">
            {{ isRegisterMode ? '注册账号' : '登 录' }}
          </el-button>
          <el-button size="large" style="flex: 1;" @click="isRegisterMode = !isRegisterMode">
            {{ isRegisterMode ? '返回登录' : '去注册' }}
          </el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useFormStore } from '../stores/useFormStore'
import { ElMessage } from 'element-plus'

const router = useRouter()
const formStore = useFormStore()
const username = ref('')
const password = ref('')
const selectedRole = ref('doctor')
const isRegisterMode = ref(false)
const loading = ref(false)

const handleLogin = async () => {
  if (!username.value || !password.value) return ElMessage.warning('请填写账号和密码')
  
  loading.value = true
  if (isRegisterMode.value) {
    const res = await formStore.register(username.value, selectedRole.value, password.value)
    if (res.success) {
      ElMessage.success('注册成功，请登录！')
      isRegisterMode.value = false
    } else {
      ElMessage.error(res.msg)
    }
  } else {
    const res = await formStore.login(username.value, selectedRole.value, password.value)
    if (res.success) {
      ElMessage.success(`欢迎您，${username.value}`)
      router.push(selectedRole.value === 'doctor' ? '/workbench' : '/patient/home')
    } else {
      ElMessage.error(res.msg)
    }
  }
  loading.value = false
}
</script>

<style scoped>
/*  核心背景：深色科技底色 */
.login-container { 
  height: 100vh; 
  display: flex; 
  justify-content: center; 
  align-items: center; 
  background-color: #020617; /* 深邃午夜蓝 */
  position: relative;
  overflow: hidden;
}

/* 科技网格叠加层 */
.grid-overlay {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  z-index: 1;
  /* 边缘渐隐效果，让视线聚焦在中央 */
  mask-image: radial-gradient(circle at center, black 30%, transparent 80%);
  -webkit-mask-image: radial-gradient(circle at center, black 30%, transparent 80%);
}

/* 动态极光流光效果 */
.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  z-index: 0;
  opacity: 0.6;
}

.glow-1 {
  width: 500px; height: 500px;
  background: #0284c7;
  top: -100px; left: -100px;
  animation: float 10s infinite alternate ease-in-out;
}

.glow-2 {
  width: 400px; height: 400px;
  background: #0ea5e9;
  bottom: -50px; right: -50px;
  animation: float 12s infinite alternate-reverse ease-in-out;
}

.glow-3 {
  width: 300px; height: 300px;
  background: #38bdf8;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  animation: pulse 8s infinite alternate ease-in-out;
}

@keyframes float {
  0% { transform: translate(0, 0); }
  100% { transform: translate(60px, 40px); }
}

@keyframes pulse {
  0% { opacity: 0.3; transform: translate(-50%, -50%) scale(0.8); }
  100% { opacity: 0.7; transform: translate(-50%, -50%) scale(1.1); }
}

/*  登录卡片*/
.login-box { 
  width: 450px; 
  /* 半透明白色背景 */
  background: rgba(255, 255, 255, 0.85); 
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: 40px; 
  border-radius: 24px; 
  /* 细白边框增加晶莹感 */
  border: 1px solid rgba(255, 255, 255, 0.5); 
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); 
  z-index: 10;
  position: relative;
  animation: slideUp 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(40px) scale(0.95); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.login-header { text-align: center; margin-bottom: 24px; }
.login-header h1 { 
  color: #0f172a; 
  margin-bottom: 8px; 
  font-size: 28px; 
  font-weight: 800;
  letter-spacing: 1px;
}
.login-header p { color: #475569; font-size: 14px; margin: 0; }

/* 角色选择卡片 */
.role-selector { display: flex; gap: 16px; justify-content: center; }
.role-card { 
  flex: 1; 
  text-align: center; 
  padding: 16px; 
  border: 2px solid #e2e8f0; 
  border-radius: 16px; 
  background: rgba(255, 255, 255, 0.6);
  cursor: pointer; 
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
}
.role-card:hover { 
  border-color: #7dd3fc; 
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.1);
}
.role-card.active { 
  border-color: #0ea5e9; 
  background: #f0f9ff; 
  box-shadow: 0 8px 20px rgba(2, 132, 199, 0.15); 
  transform: translateY(-2px);
}
.role-card .icon { font-size: 32px; margin-bottom: 8px; transition: transform 0.3s; }
.role-card.active .icon { transform: scale(1.1); }
.role-card h3 { margin: 0; color: #1e293b; font-size: 15px; font-weight: 600; }

/* 测试账号提示 */
.test-hint { 
  background: rgba(241, 245, 249, 0.7); 
  padding: 12px; 
  border-radius: 12px; 
  font-size: 12px; 
  color: #64748b; 
  margin-top: 12px; 
  line-height: 1.6; 
  border: 1px dashed #cbd5e1;
}
.test-hint p { margin: 0; }


:deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.7);
  box-shadow: 0 0 0 1px #cbd5e1 inset;
}
:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px #0ea5e9 inset;
}

/* ================= 科技渐变艺术字特效 ================= */

.login-header h1 { 
  /* 定义渐变颜色：深蓝 -> 亮青 -> 紫色*/
  background: linear-gradient(135deg, #0ea5e9 0%, #38bdf8 40%, #818cf8 100%);
  
  /*将背景裁剪为文字形状 */
  -webkit-background-clip: text;
  background-clip: text;
  
  /* 文字透明，露出底部的渐变色 */
  color: transparent;
  -webkit-text-fill-color: transparent;
  
  /* 字体与排版微调 */
  font-size: 34px; /* 稍微调大一点，更有冲击力 */
  font-weight: 900; /* 使用最粗的字体 */
  font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', sans-serif; /* 优先苹果字体，其次微软雅黑 */
  letter-spacing: 2px; /* 增加字间距，更显呼吸感 */
  margin-bottom: 8px; 
  
  /*添加一层极细微的发光阴影，让文字立体起来 */
  filter: drop-shadow(0 4px 12px rgba(14, 165, 233, 0.3));
  
  /* 加入入场动画 */
  animation: textReveal 1s ease-out;
}

/* 副标题做一点轻微的弱化处理 */
.login-header p { 
  color: #64748b; 
  font-size: 14px; 
  font-weight: 500;
  letter-spacing: 1px;
  margin: 0; 
}

/* 文字浮现动画 */
@keyframes textReveal {
  from {
    opacity: 0;
    letter-spacing: 10px; /* 从大间距收缩回来 */
    filter: blur(4px);
  }
  to {
    opacity: 1;
    letter-spacing: 2px;
    filter: blur(0);
  }
}
</style>