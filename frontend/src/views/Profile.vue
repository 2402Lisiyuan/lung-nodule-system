<template>
  <div class="profile-container">
    <el-card class="soft-card" style="max-width: 600px; margin: 0 auto;">
      <template #header>
        <div class="card-header"><span>👤 个人中心</span></div>
      </template>
      
      <div class="user-info">
        <el-avatar :size="80" :src="formStore.role === 'doctor' ? 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png' : 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'" />
        <h2>{{ formStore.doctorName }}</h2>
        <el-tag :type="formStore.role === 'doctor' ? 'primary' : 'success'">
          {{ formStore.role === 'doctor' ? '医生账号' : '患者账号' }}
        </el-tag>
        <p class="uid">系统内部 ID: {{ formStore.userId }}</p>
      </div>

      <el-divider />

      <div class="data-stats">
        <h3>我的数据概况</h3>
        <p>历史评估报告总数：<strong>{{ formStore.historyRecords.length }}</strong> 份</p>
        <p>数据存储位置：<strong>云端加密数据库 (SQLite)</strong></p>
      </div>

      <el-divider />

      <div class="security-note">
        <h3>🔒 隐私与安全</h3>
        <p style="font-size: 13px; color: #64748b; line-height: 1.6;">
          您的健康数据已绑定专属账号。系统采用严格的数据隔离机制，医生只能查看自己管理的历史记录，患者只能查看自己的评估报告，确保医疗隐私绝对安全。
        </p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { useFormStore } from '../stores/useFormStore'
const formStore = useFormStore()
</script>

<style scoped>
.profile-container { padding: 40px 20px; }
.soft-card { border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.6); box-shadow: var(--card-shadow); background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(10px); }
.card-header { font-weight: 600; font-size: 18px; color: var(--text-main); }
.user-info { text-align: center; margin: 20px 0; }
.user-info h2 { margin: 16px 0 8px 0; color: var(--text-main); }
.uid { font-size: 12px; color: #94a3b8; margin-top: 8px; }
.data-stats h3, .security-note h3 { color: #0ea5e9; font-size: 16px; margin-bottom: 16px; }
.data-stats p { color: #334155; line-height: 2; margin: 0; }
</style>