<template>
  <el-card class="box-card">
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <span>历史评估档案中心</span>
        <el-button type="danger" plain size="small" @click="clearAll">清空历史</el-button>
      </div>
    </template>
    
    <el-empty v-if="historyRecords.length === 0" description="暂无历史评估记录" />
    
    <el-table v-else :data="historyRecords" style="width: 100%" stripe>
      <el-table-column prop="date" label="评估时间" width="180" />
      <el-table-column prop="risk_level" label="风险等级" width="120">
        <template #default="scope">
          <el-tag :type="scope.row.risk_level === '高风险' ? 'danger' : (scope.row.risk_level === '中风险' ? 'warning' : 'success')">
            {{ scope.row.risk_level }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="风险概率" width="120">
        <template #default="scope">
          <strong>{{ (scope.row.risk_prob * 100).toFixed(1) }}%</strong>
        </template>
      </el-table-column>
      <el-table-column prop="volume_mm3" label="结节体积 (mm³)" width="150" />
      <el-table-column label="操作">
        <template #default="scope">
          <el-button size="small" type="primary" link @click="viewDetail(scope.row)">查看报告</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { useFormStore } from '../stores/useFormStore'
import { ElMessage, ElMessageBox } from 'element-plus'

const formStore = useFormStore()
const { historyRecords } = storeToRefs(formStore)

const clearAll = () => {
  ElMessageBox.confirm('确定要清空所有患者历史记录吗？', '警告', { type: 'warning' }).then(() => {
    formStore.clearHistory()
    ElMessage.success('已清空')
  })
}

const viewDetail = (row) => {
  ElMessageBox.alert(`
    <div style="line-height:1.8">
      <p><b>风险概率：</b>${(row.risk_prob * 100).toFixed(1)}%</p>
      <p><b>风险等级：</b>${row.risk_level}</p>
      <p><b>结节体积：</b>${row.volume_mm3} mm³</p>
    </div>
  `, 'AI 诊断报告详情', { dangerouslyUseHTMLString: true })
}
</script>