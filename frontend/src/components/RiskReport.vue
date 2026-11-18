<template>
  <div class="result-content" id="print-area">
    <div class="action-bar">
      <el-button type="primary" plain size="small" @click="show3DDialog = true">🧊 查看 3D 结节重建</el-button>
      <el-button type="success" plain size="small" @click="handlePrint">🖨️ 打印 / 导出 PDF 报告</el-button>
    </div>

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
      <div ref="chartRef" style="width: 100%; height: 260px;"></div>
    </div>

    <el-dialog v-model="show3DDialog" title="肺部结节 3D 重建视图" width="600px" align-center>
      <div class="three-d-placeholder">
        <div class="sphere-animation"></div>
        <p style="margin-top: 20px; color: #64748b; font-size: 14px; text-align: center;">
          基于 CT 影像序列与 Marching Cubes 算法生成的等值面三维重建。<br>
          <strong>（演示环境为体积等比例模拟球体）</strong>
        </p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'

const props = defineProps({ result: Object })
const chartRef = ref(null)
const show3DDialog = ref(false)
let myChart = null

const renderChart = () => {
  nextTick(() => {
    if (chartRef.value && props.result) {
      if (!myChart) myChart = echarts.init(chartRef.value)
      const baseRisk = props.result.risk_prob * 100
      
      const option = {
        title: { text: '未来3年风险演化趋势', left: 'center', textStyle: { fontSize: 14, color: '#1e293b' } },
        tooltip: { trigger: 'axis' },
        xAxis: { 
          type: 'category', data: ['当前', '1年后', '2年后', '3年后'],
          axisLabel: { color: '#64748b' },
          axisLine: { lineStyle: { color: '#cbd5e1' } }
        },
        yAxis: { 
          type: 'value', min: 0, max: 100, axisLabel: { formatter: '{value}%', color: '#64748b' },
          splitLine: { lineStyle: { color: '#f1f5f9' } }
        },
        series: [{ 
          data: [baseRisk, baseRisk * 1.1, baseRisk * 1.25, baseRisk * 1.4].map(v => Math.min(v, 100).toFixed(1)), 
          type: 'line', smooth: true, itemStyle: { color: '#e53935' }, 
          areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(229,57,53,0.4)' }, { offset: 1, color: 'rgba(229,57,53,0.05)' }]) } 
        }]
      }
      myChart.setOption(option)
    }
  })
}

const handlePrint = () => { ElMessage.success('正在调起打印预览...'); setTimeout(() => { window.print() }, 300) }

watch(() => props.result, () => { renderChart() }, { deep: true })
onMounted(() => { renderChart() })
onUnmounted(() => { if (myChart) myChart.dispose() })
</script>

<style scoped>
.risk-card { text-align: center; padding: 40px 20px; border-radius: 16px; color: white; margin-bottom: 24px; }
.bg-danger { background: linear-gradient(135deg, #ff7a7a, #e53935); box-shadow: 0 10px 24px rgba(229, 57, 53, 0.2); }
.bg-warning { background: linear-gradient(135deg, #fbbf24, #f59e0b); box-shadow: 0 10px 24px rgba(245, 158, 11, 0.2); }
.bg-success { background: linear-gradient(135deg, #34d399, #059669); box-shadow: 0 10px 24px rgba(5, 150, 105, 0.2); }
.risk-card h2 { margin: 0; font-size: 24px; font-weight: 500; letter-spacing: 1px; }
.risk-card .probability { font-size: 72px; font-weight: 700; margin: 10px 0; }
.risk-card p { margin: 0; font-size: 15px; opacity: 0.9; }

.data-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }
.data-item { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; display: flex; flex-direction: column; gap: 8px; }
.data-label { font-size: 13px; color: #64748b; }
.data-value { font-size: 24px; font-weight: 700; color: #1e293b; }

.chart-container { border: 1px solid #f1f5f9; border-radius: 12px; padding: 10px; background: white; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }

.action-bar { display: flex; justify-content: flex-end; gap: 12px; margin-bottom: 16px; }
.three-d-placeholder { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 300px; background: radial-gradient(circle, #f8fafc 0%, #e2e8f0 100%); border-radius: 12px; overflow: hidden; }
.sphere-animation { width: 120px; height: 120px; background: radial-gradient(circle at 30% 30%, #7dd3fc, #0284c7, #0f172a); border-radius: 50%; box-shadow: inset -20px -20px 40px rgba(0,0,0,0.6), 0 20px 30px rgba(0,0,0,0.2); animation: spin 8s linear infinite; }
@keyframes spin { 0% { transform: rotateY(0deg) rotateX(15deg); } 100% { transform: rotateY(360deg) rotateX(15deg); } }

@media print {
  :global(.el-col-8), :global(.el-header), :global(.el-card__header), .action-bar { display: none !important; }
  :global(.el-col-16) { width: 100% !important; max-width: 100% !important; flex: 0 0 100% !important; }
  :global(.main-content) { padding: 0 !important; }
  .soft-card { box-shadow: none !important; border: none !important; background: white !important; }
}
</style>