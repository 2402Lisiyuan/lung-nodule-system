<template>
  <div class="knowledge-container">
    <div class="page-header">
      <h2>肺部健康科普大讲堂</h2>
      <p>专业的医学知识，帮助您更好地了解肺结节，科学应对随访。</p>
    </div>

    <!-- AI 专属智能推荐卡片 -->
    <div class="ai-recommend-card">
      <div class="rec-header">
        <span class="ai-badge">✨ AI 专属推荐</span>
        <span class="rec-reason" v-if="latestRisk !== '无记录'">
          检测到您的最新评估为 <strong :class="latestRisk === '高风险' ? 'text-danger' : (latestRisk === '中风险' ? 'text-warning' : 'text-success')">{{ latestRisk }}</strong>
        </span>
        <span class="rec-reason" v-else>
          您还没有评估记录，建议先了解基础保养知识
        </span>
      </div>
      <div class="rec-content">
        <div class="rec-text">
          <span class="typing-dot" v-if="isRecTyping && !recText">|</span>
          {{ recText || 'AI 管家正在根据您的健康档案分析...' }}
        </div>
        <el-button type="primary" round class="rec-btn" @click="openArticle(articles[recommendIndex])">
          去阅读推荐 📖
        </el-button>
      </div>
    </div>

    <!-- 科普文章卡片列表-->
    <el-row :gutter="24" style="margin-top: 20px;">
      <el-col :span="6" v-for="(article, index) in articles" :key="index" style="margin-bottom: 24px;">
       
        <el-card :class="['article-card', { 'is-recommended': index === recommendIndex }]" shadow="hover" :body-style="{ padding: '0px' }" @click="openArticle(article)">
        
          <div class="cover-image" :style="{ background: article.coverBg }">
            <span class="cover-icon">{{ article.icon }}</span>
            <span class="category-tag">{{ article.category }}</span>
           
            <span v-if="index === recommendIndex" class="rec-star">⭐</span>
          </div>
          
          <!-- 内容区 -->
          <div class="card-content">
            <h3 class="article-title">{{ article.title }}</h3>
            <p class="article-summary">{{ article.summary }}</p>
            
            <div class="card-footer">
              <span class="read-count">
                <el-icon><View /></el-icon> {{ article.views }}
              </span>
              <el-button type="primary" link>
                阅读全文
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 底部：AI 快捷引导卡片-->
    <el-card class="ai-banner-card" shadow="never">
      <div class="banner-content">
        <div class="banner-text">
          <h2>还有关于病情的疑问？</h2>
          <p>点击右下角的 AI 肺部健康助理，随时为您解答检查报告、日常饮食及康复问题。</p>
        </div>
        <div class="banner-action">
          <el-button type="primary" size="large" round class="banner-btn">
            唤起 AI 助理
            <el-icon class="el-icon--right"><ChatDotRound /></el-icon>
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 文章详情弹窗 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="currentArticle?.title" 
      width="700px"
      align-center
      class="article-dialog"
    >
      <div v-if="currentArticle" class="dialog-content">
        <div class="dialog-cover" :style="{ background: currentArticle.coverBg }">
          <span class="dialog-cover-icon">{{ currentArticle.icon }}</span>
        </div>
        
        <div class="article-meta">
          <el-tag size="small" type="success" effect="plain">{{ currentArticle.category }}</el-tag>
          <span style="margin-left: 10px; color: #94a3b8; font-size: 13px;">发布于 2026-11-15</span>
        </div>

        <div class="article-body">
          <div v-for="(block, idx) in currentArticle.contentBlocks" :key="idx">
            <h4 v-if="block.type === 'title'">{{ block.text }}</h4>
            <p v-if="block.type === 'text'">{{ block.text }}</p>
            <ul v-if="block.type === 'list'">
              <li v-for="(item, i) in block.items" :key="i">{{ item }}</li>
            </ul>
          </div>
        </div>
        
        <div class="dialog-footer">
          <el-alert
            title="本文仅供健康科普，不能替代专业医生的当面诊断。"
            type="info"
            :closable="false"
            show-icon
          />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { View, ChatDotRound } from '@element-plus/icons-vue'
import { useFormStore } from '../../stores/useFormStore'

const dialogVisible = ref(false)
const currentArticle = ref(null)

// =================  AI 智能推荐核心逻辑 =================
const formStore = useFormStore()
const latestRisk = ref('无记录')
const recText = ref('')
const isRecTyping = ref(false)
const recommendIndex = ref(0)

// 根据风险等级匹配文章索引
const getRecommendIndex = (risk) => {
  if (risk === '高风险') return 7 // 推荐看磨玻璃/临床常见
  if (risk === '中风险') return 3 // 推荐看复查指南
  if (risk === '低风险') return 2 // 推荐心理调适
  return 0 // 无记录推荐饮食
}

const fetchAiRecommend = async () => {
  // 1. 从 Pinia 获取最新评估记录
  if (formStore.historyRecords.length > 0) {
    latestRisk.value = formStore.historyRecords[0].risk_level
  }
  
  // 2. 设定要高亮的文章索引
  recommendIndex.value = getRecommendIndex(latestRisk.value)

  // 3. 请求大模型生成个性化推荐语 (流式渲染)
  isRecTyping.value = true
  recText.value = ''
  try {
    const response = await fetch('/api/recommend_knowledge', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ risk_level: latestRisk.value, user_id: formStore.userId || 0 })
    })
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      recText.value += decoder.decode(value, { stream: true })
    }
  } catch (error) {
    recText.value = 'AI 正在为您挑选最合适的科普文章...'
  } finally {
    isRecTyping.value = false
  }
}

// 8 篇科普文章数据 
const articles = [
  {
    title: '肺结节患者的饮食调养：三分治，七分养',
    category: '饮食指南',
    icon: '🍎',
    views: 1240,
    coverBg: 'linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%)',
    summary: '科学的饮食能有效提升免疫力。哪些食物该多吃？哪些要忌口？本文为您详细解答。',
    contentBlocks: [
      { type: 'title', text: '1. 润肺止咳的食物推荐' },
      { type: 'text', text: '中医认为“白色入肺”。日常饮食中可适当多吃一些滋阴润肺的食物，如雪梨、百合、银耳、山药、白萝卜等。' },
      { type: 'title', text: '2. 优质蛋白不可少' },
      { type: 'text', text: '免疫细胞的生成离不开蛋白质。建议多摄入瘦肉、鱼类、鸡蛋、豆制品等优质蛋白，增强对抗疾病的能力。' },
      { type: 'title', text: '3. 严格忌口与禁忌' },
      { type: 'text', text: '坚决戒烟是保护肺部的第一原则。同时，应尽量避免辛辣、油炸、烧烤等刺激性食物，建议戒酒。' }
    ]
  },
  {
    title: '适合肺结节患者的日常运动指南',
    category: '运动康复',
    icon: '🏃',
    views: 986,
    coverBg: 'linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%)',
    summary: '适当运动能增强心肺功能，但肺结节患者应避免剧烈憋气运动。推荐几款适合的锻炼方式。',
    contentBlocks: [
      { type: 'title', text: '1. 推荐的低强度运动' },
      { type: 'text', text: '推荐进行太极拳、八段锦、慢走、瑜伽等舒缓的有氧运动，能增强心肺功能，改善睡眠。' },
      { type: 'title', text: '2. 运动频率与时长' },
      { type: 'text', text: '建议每周进行 3-5 次运动，每次 30-40 分钟左右。以微微出汗、心率不超过（170-年龄）为宜。' },
      { type: 'title', text: '3. 运动中的自我监测' },
      { type: 'text', text: '如果在运动过程中出现胸痛、胸闷、气促，应立即停止运动并休息，如不缓解需及时就医。' }
    ]
  },
  {
    title: '面对肺结节，如何做好心理建设与情绪疏导',
    category: '心理调适',
    icon: '🧘',
    views: 2315,
    coverBg: 'linear-gradient(135deg, #fdf4ff 0%, #fae8ff 100%)',
    summary: '发现肺结节后，焦虑和恐慌是正常的。但长期负面情绪不利于免疫系统。学会这几点，放下心理包袱。',
    contentBlocks: [
      { type: 'title', text: '1. 正确认识肺结节：90% 是良性的' },
      { type: 'text', text: '在低剂量CT发现的结节中，超过 90% 都是良性的（如炎症、疤痕）。发现结节并不等于得了肺癌。' },
      { type: 'title', text: '2. 焦虑对免疫系统的负面影响' },
      { type: 'text', text: '长期处于恐惧、焦虑状态，会导致皮质醇水平升高，抑制免疫系统功能，反而不利于疾病控制。' },
      { type: 'title', text: '3. 转移注意力，回归正常生活' },
      { type: 'text', text: '遵医嘱定期复查即可，在非复查期间，尽量将注意力转移到工作、家庭和爱好上。' }
    ]
  },
  {
    title: '肺结节复查指南：什么情况需要立刻去医院？',
    category: '复查指导',
    icon: '🏥',
    views: 3102,
    coverBg: 'linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%)',
    summary: '随访是应对肺结节的最好方式。但如果在随访期间出现某些异常症状，请不要等复查时间，立刻就医。',
    contentBlocks: [
      { type: 'title', text: '1. 常规复查时间表' },
      { type: 'text', text: '医生会根据结节大小和形态制定随访计划。低风险结节通常建议 6-12 个月复查一次。' },
      { type: 'title', text: '2. 必须立刻就医的紧急信号' },
      { type: 'list', items: ['咯血：痰液中带有鲜红色血丝或血块。', '剧烈胸痛：突然出现的持续性胸部疼痛。', '不明原因发热：持续发热且抗感染治疗无效。', '声音嘶哑：无缘无故出现声音嘶哑且加重。'] },
      { type: 'title', text: '3. 复查时的注意事项' },
      { type: 'text', text: '每次复查，请务必携带以前的片子和报告。对比以前的影像，才能判断结节是否长大。' }
    ]
  },
  {
    title: '低剂量CT辐射大吗？多久做一次才安全？',
    category: '影像检查',
    icon: '🩻',
    views: 1890,
    coverBg: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
    summary: '很多患者担心CT辐射会导致结节恶变。实际上，低剂量CT的辐射量非常低，处于绝对安全范围内。',
    contentBlocks: [
      { type: 'title', text: '1. 什么是低剂量CT (LDCT)？' },
      { type: 'text', text: '低剂量CT的辐射剂量约为常规CT的 1/5 到 1/10。一次LDCT的辐射量大约相当于您乘坐一次长途飞机或在自然环境中生活几个月的本底辐射。' },
      { type: 'title', text: '2. 随访的权衡：利大于弊' },
      { type: 'text', text: '相比于极微小的辐射风险，通过低剂量CT及早发现早期肺癌、及时干预所带来的生存获益是巨大的。' }
    ]
  },
  {
    title: '吸烟与肺结节：现在戒烟还来得及吗？',
    category: '生活方式',
    icon: '🚭',
    views: 2543,
    coverBg: 'linear-gradient(135deg, #f1f5f9 0%, #cbd5e1 100%)',
    summary: '吸烟是导致肺癌的头号元凶。对于肺结节患者而言，戒烟不仅是为了自己，也是为了家人的健康。',
    contentBlocks: [
      { type: 'title', text: '1. 戒烟永远不晚' },
      { type: 'text', text: '无论您吸烟多少年，只要开始戒烟，肺部的纤毛就会慢慢恢复清洁功能，心血管风险也会逐渐降低。' },
      { type: 'title', text: '2. 二手烟的危害同样不容忽视' },
      { type: 'text', text: '家里有肺结节患者，家属也应尽量避免在室内吸烟。二手烟同样含有数十种致癌物质。' }
    ]
  },
  {
    title: '肺结节会遗传吗？家人需要做检查吗？',
    category: '家族健康',
    icon: '👨‍👩‍👧',
    views: 1120,
    coverBg: 'linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%)',
    summary: '肺癌具有一定的家族聚集性。如果直系亲属查出过肺癌或多发肺结节，建议40岁后开始定期筛查。',
    contentBlocks: [
      { type: 'title', text: '1. 肺癌的家族遗传倾向' },
      { type: 'text', text: '医学研究表明，如果直系亲属（父母、兄弟姐妹）中有肺癌患者，那么个人患肺癌的风险会比普通人高出1.5到2倍。' },
      { type: 'title', text: '2. 高危人群的筛查建议' },
      { type: 'text', text: '建议有肺癌家族史、长期吸烟史、或长期处于二手烟/粉尘环境的人群，从40岁起每年进行一次低剂量肺部CT筛查。' }
    ]
  },
  {
    title: '检查出磨玻璃结节（GGO），必须马上手术吗？',
    category: '临床常见',
    icon: '🔬',
    views: 4321,
    coverBg: 'linear-gradient(135deg, #ffe4e6 0%, #fecdd3 100%)',
    summary: '磨玻璃结节（GGO）往往是早期肺腺癌的“慢动作版”，它们生长极其缓慢，通常不需要立刻开刀。',
    contentBlocks: [
      { type: 'title', text: '1. GGO是一种“懒癌”' },
      { type: 'text', text: '许多纯磨玻璃结节即使最终证实为恶性，也往往处于非常早期的阶段，生长速度极慢，随访观察几年都不会发生转移。' },
      { type: 'title', text: '2. 定期复查比急于手术更重要' },
      { type: 'text', text: '如果医生建议您随访，说明目前的结节对您没有即时威胁。盲目切除可能会损失更多的健康肺组织，反而降低生活质量。' },
      { type: 'title', text: '3. 什么时候需要干预？' },
      { type: 'text', text: '当复查发现结节持续增大、密度变实（出现实性成分且增加）时，医生才会建议您考虑微创手术切除。' }
    ]
  }
]

const openArticle = (article) => {
  currentArticle.value = article
  dialogVisible.value = true
}

// 页面加载时立即触发 AI 智能推荐
onMounted(() => {
  fetchAiRecommend()
})
</script>

<style scoped>
.knowledge-container {
  max-width: 1200px;
  margin: 0 auto;
  padding-bottom: 40px;
}

.page-header {
  text-align: center;
  margin-bottom: 20px;
}
.page-header h2 {
  color: #0f172a;
  font-size: 28px;
  margin-bottom: 10px;
}
.page-header p {
  color: #64748b;
  font-size: 15px;
}

/* ================= AI 推荐卡片样式 ================= */
.ai-recommend-card {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 1px solid #bae6fd;
  border-radius: 16px;
  padding: 20px;
  margin-top: 20px;
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.1);
  position: relative;
  overflow: hidden;
}
.rec-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.ai-badge {
  background: #0ea5e9;
  color: white;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.3);
}
.rec-reason { font-size: 13px; color: #475569; }
.text-danger { color: #ef4444; font-weight: bold; }
.text-warning { color: #f59e0b; font-weight: bold; }
.text-success { color: #10b981; font-weight: bold; }

.rec-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}
.rec-text {
  flex: 1;
  font-size: 15px;
  color: #0f172a;
  line-height: 1.6;
  font-weight: 500;
}
.rec-btn { flex-shrink: 0; box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3); }

/* 光标闪烁动画 */
.typing-dot {
  display: inline-block;
  width: 2px;
  height: 16px;
  background: #0ea5e9;
  animation: blink 1s step-end infinite;
  vertical-align: middle;
}
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

/* ================= 原有文章卡片样式 ================= */
.article-card {
  border-radius: 16px;
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
  overflow: hidden;
  height: 100%;
  background: #ffffff;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  position: relative; /* 为星星标签定位 */
}
.article-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 30px rgba(14, 165, 233, 0.15);
}

/* 被推荐的文章卡片高亮 */
.article-card.is-recommended {
  border: 2px solid #38bdf8;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(14, 165, 233, 0.2);
}
.rec-star {
  position: absolute;
  top: 12px;
  right: 12px;
  font-size: 18px;
  animation: pulse 2s infinite;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
}
@keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.2); } }

.cover-image {
  position: relative;
  width: 100%;
  height: 120px;
  display: flex;
  justify-content: center;
  align-items: center;
}
.cover-icon {
  font-size: 50px;
  filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
}
.category-tag {
  position: absolute;
  top: 12px;
  left: 12px;
  background: rgba(255, 255, 255, 0.85);
  color: #0284c7;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 20px;
  backdrop-filter: blur(4px);
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

.card-content {
  padding: 20px;
  display: flex;
  flex-direction: column;
  flex: 1;
}
.article-title {
  margin: 0 0 10px 0;
  font-size: 15px;
  color: #1e293b;
  font-weight: 600;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 42px;
}
.article-summary {
  margin: 0 0 16px 0;
  font-size: 13px;
  color: #64748b;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #f1f5f9;
  padding-top: 12px;
  margin-top: auto;
}
.read-count {
  font-size: 12px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* ================= 底部 Banner 样式 ================= */
.ai-banner-card {
  margin-top: 20px;
  border-radius: 16px;
  border: none;
  background: linear-gradient(135deg, #0ea5e9, #0284c7);
  box-shadow: 0 10px 30px rgba(14, 165, 233, 0.2);
  overflow: hidden;
}
.banner-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
}
.banner-text h2 {
  color: white;
  margin: 0 0 8px 0;
  font-size: 22px;
}
.banner-text p {
  color: rgba(255, 255, 255, 0.85);
  margin: 0;
  font-size: 14px;
}
.banner-btn {
  background: white;
  color: #0284c7;
  border: none;
  font-weight: 600;
  padding: 12px 24px;
}
.banner-btn:hover {
  background: #f0f9ff;
  color: #0ea5e9;
}

/* ================= 弹窗详情样式 ================= */
.article-dialog :deep(.el-dialog__body) {
  padding: 0 20px 20px 20px;
}
.dialog-cover {
  width: 100%;
  height: 120px;
  border-radius: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 20px;
}
.dialog-cover-icon {
  font-size: 60px;
}
.article-meta {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}
.article-body h4 {
  color: #0f172a;
  margin: 20px 0 10px 0;
  font-size: 16px;
}
.article-body p {
  color: #334155;
  line-height: 1.8;
  font-size: 14px;
  margin: 0 0 10px 0;
}
.article-body ul {
  padding-left: 20px;
  color: #334155;
  line-height: 1.8;
  font-size: 14px;
}
.article-body li {
  margin-bottom: 6px;
}
.dialog-footer {
  margin-top: 30px;
}
</style>