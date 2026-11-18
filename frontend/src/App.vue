<template>
  <router-view></router-view>
</template>

<style>
body, html {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
  -webkit-font-smoothing: antialiased;
}

:root {
  --primary-color: #0ea5e9;
  --bg-color: #f0f4f8;
  --text-main: #1e293b;
  --text-sub: #64748b;
  --card-shadow: 0 8px 32px rgba(14, 165, 233, 0.08);
  --card-radius: 16px;
}

/* ==================================================
   核心美化：纯 CSS 科技网格 + 动态呼吸光晕背景
   ================================================== */
body {
  background-color: #f4f7fb;
  background-image: 
   
    linear-gradient(rgba(14, 165, 233, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(14, 165, 233, 0.035) 1px, transparent 1px),
    
    radial-gradient(circle at 10% 10%, rgba(14, 165, 233, 0.1) 0%, transparent 40%),
    
    radial-gradient(circle at 90% 90%, rgba(16, 185, 129, 0.08) 0%, transparent 40%),
    
    radial-gradient(circle at 90% 10%, rgba(139, 92, 246, 0.06) 0%, transparent 40%);
  
  background-size: 
    40px 40px, 
    40px 40px, 
    100% 100%, 
    100% 100%, 
    100% 100%;
  
  background-attachment: fixed;
  background-position: center;
}

/* 增加一层缓慢移动的超大光晕，模拟呼吸感 */
body::before {
  content: "";
  position: fixed;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at 50% 50%, rgba(14, 165, 233, 0.05) 0%, transparent 60%);
  animation: bgFloat 20s ease-in-out infinite alternate;
  z-index: -1;
  pointer-events: none;
}

@keyframes bgFloat {
  0% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(5%, 5%) scale(1.05); }
  100% { transform: translate(-5%, -5%) scale(1); }
}

/* ==================================================
   其他全局样式
   ================================================== */
.el-main, .layout-container, .patient-home {
  background-color: transparent !important; /* 让底色透出来 */
}

/* 统一输入框圆角 */
.el-input__wrapper, .el-textarea__inner {
  border-radius: 8px !important;
  box-shadow: 0 0 0 1px #e2e8f0 inset !important;
}
.el-button {
  border-radius: 8px !important;
  font-weight: 500 !important;
}

/* 滚动条美化 */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
::-webkit-scrollbar-track { background: transparent; }
</style>