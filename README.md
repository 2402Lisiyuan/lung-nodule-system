# 🫁 智影时序 AI - 肺结节全周期智能随访平台

> **2026 传智杯 AI Web 赛道参赛作品**


## 在线演示 (Live Demo)
为了方便评审专家体验，本项目已部署至阿里云公网服务器：
*   **公网访问地址**：**[http://182.92.133.33/](http://182.92.133.33/)**
*   **医生端测试账号**：`doctor` / 密码：`doctor123`
*   **患者端测试账号**：`patient` / 密码：`patient123`

---

## 项目介绍
肺癌是全球发病率和死亡率最高的恶性肿瘤。传统的单次 CT 评估难以捕捉结节的动态演化规律，且传统 AI 冰冷的数据输出容易引发患者严重的“结节焦虑”。

本项目在团队前期原创的“时序深度学习”算法基础上，进行了**全面的全栈 Web 重构与 AI 升维**。系统采用 Vue3 + FastAPI 构建，深度融合了 DeepSeek 大语言模型，实现了从“影像输入 -> 风险量化 -> AI 通俗解读 -> 全周期医患随访”的业务闭环。

### 核心亮点
1.  **双路时序 3D CNN**：同时输入“当前”与“先前” CT 及时间间隔，自动捕捉结节 3 年的恶性演化趋势（底层算法已通过千例级数据集验证）。
2.  **大模型流式交互 (SSE)**：接入 DeepSeek 大模型，通过 Server-Sent Events 实现丝滑的“打字机”报告解读与医患对话。
3.  **轻量级 RAG 与 Agent**：
    *   自研文档匹配打分算法（RAG），确保 AI 引用医学指南（如 Fleischner 指南）的严谨性。
    *   基于正则路由的 Agent 决策，用户询问特定尺寸时，AI 会自动调用体积计算工具并展示思考过程。
4.  **医患双端人文关怀**：医生端提供高效评估与报告打印；患者端独创“AI 肺康日记”与“二十四节气养生管家”，用科技传递温度。

---

## 技术架构
*   **前端**：Vue 3 (Composition API) + Vite + Element Plus + Pinia + Echarts
*   **后端**：Python 3.9 + FastAPI + Uvicorn
*   **AI 引擎**：DeepSeek-V3 (API 接入)
*   **算法底层**：PyTorch + SimpleITK + NumPy (3D CNN 影像处理)
*   **部署方案**：Docker 容器化 + Nginx 反向代理 (阿里云 ECS)

---


## 团队信息
本次参赛团队：博源铭志队；
参赛队员：李同学、王同学、邓同学

## 项目结构
```text
lung_nodule_system/
├── backend/            # FastAPI 后端服务目录
│   ├── main.py         # API 路由与 SSE 流式处理
│   ├── model.py        # 3D CNN 网络结构
│   ├── utils.py        # 影像读取与预处理
│   ├── Dockerfile      # 容器化构建文件
│   └── requirements.txt
├── frontend/           # Vue3 前端目录
│   ├── src/            # 页面组件 (views) 与组件 (components)
│   └── package.json
└── README.md
