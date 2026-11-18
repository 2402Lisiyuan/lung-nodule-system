from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI
import torch
import os
import shutil
import uuid
import traceback
import asyncio
import pandas as pd
import math
import re
import sqlite3
import hashlib
from datetime import datetime
from dotenv import load_dotenv

from model import load_model
from utils import (
    load_nifti, normalize_hu, physical_to_voxel,
    extract_patch_around_center, compute_nodule_volume
)

# 加载 .env 文件中的环境变量
load_dotenv()

app = FastAPI(title="智影时序 API")

# ==========================================
# 1. 全局配置与变量
# ==========================================
# 优先从环境变量读取 API Key
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = None
UPLOAD_DIR = "uploads"
DB_PATH = "lung_health.db"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ==========================================
# 2. 数据库初始化与配置
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT UNIQUE, password TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS records
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, date TEXT, 
                  risk_level TEXT, risk_prob REAL, volume_mm3 REAL,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')

    def add_test_user(username, password, role):
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        if not c.fetchone():
            hashed = hashlib.md5(password.encode()).hexdigest()
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed, role))

    add_test_user("doctor", "doctor123", "doctor")
    add_test_user("patient", "patient123", "patient")
    conn.commit()
    conn.close()


init_db()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================
# 3. RAG 知识库配置
# ==========================================
# 模拟将医学指南切分成文档块 (Chunks)
RAG_DOCUMENTS = [
    {"id": 1, "tag": "复查",
     "content": "Fleischner 2017指南：直径 6-8mm 的实性结节建议在 6-12 个月后复查 CT；直径 > 8mm 建议 3 个月后复查或 PET-CT。"},
    {"id": 2, "tag": "手术",
     "content": "Fleischner 2017指南：对于部分实性结节，若实性成分明显增加，或恶性风险极高且直径 > 15mm，建议胸外科评估手术指征。"},
    {"id": 3, "tag": "体积",
     "content": "临床共识：结节体积倍增时间（VDT）是评估良恶性的关键指标，恶性结节的 VDT 通常在 100-400 天之间。"},
    {"id": 4, "tag": "饮食",
     "content": "肺部健康饮食建议：多吃富含维生素C和抗氧化剂的新鲜蔬果（如西兰花、番茄、梨等），避免辛辣刺激、油腻食物，戒烟限酒。"},
    {"id": 5, "tag": "运动",
     "content": "肺结节患者可进行适度的有氧运动，如太极拳、慢走、游泳，每周3-5次，每次30分钟，避免剧烈憋气运动。"},
    {"id": 6, "tag": "挂号",
     "content": "如果您发现结节增长迅速或伴有咯血、胸痛症状，建议立刻前往三甲医院的【胸外科】或【呼吸内科】就诊。"},
    {"id": 7, "tag": "情绪",
     "content": "发现肺结节不要过度恐慌，90%以上的结节都是良性的。保持良好心态，规律作息，按医嘱复查即可。"}
]


def retrieve_rag_context(question: str) -> str:
    """
    RAG 检索：基于关键词匹配打分排序，模拟向量检索的相似度机制
    """
    scored_docs = []
    for doc in RAG_DOCUMENTS:
        score = 0
        # 如果 tag 在问题中，基础分 +10
        if doc["tag"] in question:
            score += 10
        # 计算文档内容与问题的字符重合度作为相似度
        for char in question:
            if char in doc["content"]:
                score += 0.1
        if score > 0:
            scored_docs.append((score, doc["content"]))

    # 按照分数降序排列，取 Top-2 的文档片段作为上下文
    scored_docs.sort(key=lambda x: x[0], reverse=True)
    top_docs = [doc[1] for doc in scored_docs[:2]]

    return "\n".join(top_docs) if top_docs else ""


# ==========================================
# 4. 跨域配置与模型加载
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    global model
    weights_path = "pretrained_large.pth"
    try:
        if os.path.exists(weights_path):
            model = load_model(weights_path).to(device)
        else:
            model = load_model(None).to(device)
        model.eval()
        print(f"✅ 模型加载成功，使用设备: {device}")
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")


# ==========================================
# 5. 鉴权与历史记录接口
# ==========================================
@app.post("/api/auth/login")
def login(username: str = Form(...), password: str = Form(...), role: str = Form(...)):
    hashed_pw = hashlib.md5(password.encode()).hexdigest()
    conn = get_db();
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND role=?", (username, role))
    user = c.fetchone();
    conn.close()
    if user and user['password'] == hashed_pw:
        return {"status": "success", "user_id": user['id'], "username": user['username'], "role": user['role']}
    raise HTTPException(status_code=401, detail="账号或密码错误")


@app.post("/api/auth/register")
def register(username: str = Form(...), password: str = Form(...), role: str = Form(...)):
    hashed_pw = hashlib.md5(password.encode()).hexdigest()
    conn = get_db();
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_pw, role))
        conn.commit()
        return {"status": "success", "message": "注册成功"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="该账号已存在")
    finally:
        conn.close()


@app.get("/api/history")
def get_history(user_id: int):
    conn = get_db();
    c = conn.cursor()
    c.execute("SELECT * FROM records WHERE user_id=? ORDER BY id DESC", (user_id,))
    rows = c.fetchall();
    conn.close()
    return [{"id": r["id"], "date": r["date"], "risk_level": r["risk_level"], "risk_prob": r["risk_prob"],
             "volume_mm3": r["volume_mm3"]} for r in rows]


@app.post("/api/history")
def add_history(user_id: int = Form(...), risk_level: str = Form(...), risk_prob: float = Form(...),
                volume_mm3: float = Form(...)):
    conn = get_db();
    c = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO records (user_id, date, risk_level, risk_prob, volume_mm3) VALUES (?, ?, ?, ?, ?)",
              (user_id, date_str, risk_level, risk_prob, volume_mm3))
    conn.commit();
    conn.close()
    return {"status": "success"}


# ==========================================
# 6. 影像上传与双路推理接口
# ==========================================
@app.post("/api/upload")
def upload_file(file: UploadFile = File(...)):
    try:
        file_extension = os.path.splitext(file.filename)[1]
        if file_extension == '.gz' and file.filename.endswith('.nii.gz'): file_extension = '.nii.gz'
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"status": "success", "filename": unique_filename, "original_name": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@app.post("/api/upload_annotations")
def upload_annotations(file: UploadFile = File(...)):
    try:
        df = pd.read_csv(file.file)
        annotations = {}
        for _, row in df.iterrows():
            uid = str(row['seriesuid'])
            if uid not in annotations: annotations[uid] = []
            annotations[uid].append(
                {'coordX': float(row['coordX']), 'coordY': float(row['coordY']), 'coordZ': float(row['coordZ']),
                 'diameter_mm': float(row.get('diameter_mm', 0))})
        return {"status": "success", "annotations": annotations, "total": len(df)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV解析失败: {str(e)}")


@app.post("/api/predict")
def predict(file_cur: str = Form(...), file_pri: str = Form(...), cur_coord_x: float = Form(...),
            cur_coord_y: float = Form(...), cur_coord_z: float = Form(...), pri_coord_x: float = Form(...),
            pri_coord_y: float = Form(...), pri_coord_z: float = Form(...), months: int = Form(...)):
    try:
        path_cur = os.path.join(UPLOAD_DIR, file_cur);
        path_pri = os.path.join(UPLOAD_DIR, file_pri)
        if not os.path.exists(path_cur) or not os.path.exists(path_pri): raise HTTPException(status_code=404,
                                                                                             detail="找不到 CT 文件")

        vol_cur, spacing_cur, affine_cur = load_nifti(path_cur)
        voxel_cur = physical_to_voxel((cur_coord_x, cur_coord_y, cur_coord_z), affine_cur, vol_cur.shape)
        patch_cur = extract_patch_around_center(normalize_hu(vol_cur), voxel_cur, 64)
        vol_mm3, _ = compute_nodule_volume(patch_cur, spacing_cur)

        vol_pri, spacing_pri, affine_pri = load_nifti(path_pri)
        voxel_pri = physical_to_voxel((pri_coord_x, pri_coord_y, pri_coord_z), affine_pri, vol_pri.shape)
        patch_pri = extract_patch_around_center(normalize_hu(vol_pri), voxel_pri, 64)

        patch_cur_t = torch.tensor(patch_cur, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(device)
        patch_pri_t = torch.tensor(patch_pri, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(device)
        time_t = torch.tensor([[months / 12.0]], dtype=torch.float32).to(device)

        with torch.no_grad():
            risk = model(patch_cur_t, patch_pri_t, time_t).item()
        if str(risk) == 'nan' or risk is None: risk = 0.5

        risk_level = "高风险" if risk >= 0.6 else ("中风险" if risk >= 0.3 else "低风险")
        return {"risk_prob": round(risk, 4), "risk_level": risk_level, "volume_mm3": round(vol_mm3, 2),
                "status": "success"}
    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


# ==========================================
# 7. 医生端 AI 解释接口 (Agent + RAG)
# ==========================================
@app.post("/api/ai_explain")
async def ai_explain(risk_level: str = Form(...), risk_prob: float = Form(...), volume_mm3: float = Form(...),
                     question: str = Form("")):
    forbidden_keywords = ["开药", "吃什么药", "头孢", "确诊为", "包治"]
    for word in forbidden_keywords:
        if word in question:
            async def safety_response():
                msg = "⚠️ 系统安全提示：作为 AI 助手，我无法为您开具处方药或做出最终确诊。请遵从医嘱。\n\n"
                for char in msg: yield char; await asyncio.sleep(0.02)

            return StreamingResponse(safety_response(), media_type="text/event-stream")

    if not question:
        prompt = f"你是一位拥有20年临床经验的胸外科主任医师。请根据以下 AI 影像分析结果，生成一段通俗易懂的解读。\n【结果】风险等级：{risk_level}，概率：{risk_prob * 100:.1f}%，体积：{volume_mm3} mm³。\n【要求】不要过度引起恐慌，给出复查建议。字数150字左右。"

        async def generate_basic():
            try:
                if not DEEPSEEK_API_KEY:
                    mock_text = f"您好，该结节目前评估为【{risk_level}】。请不必过度焦虑，建议前往门诊。"
                    for char in mock_text: yield char; await asyncio.sleep(0.05)
                else:
                    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
                    response = client.chat.completions.create(model="deepseek-chat",
                                                              messages=[{"role": "user", "content": prompt}],
                                                              stream=True)
                    for chunk in response:
                        if chunk.choices[0].delta.content: yield chunk.choices[0].delta.content
            except Exception:
                yield "\n[系统提示] AI 休息中。"
            disclaimer = "\n\n---\n*⚕️ 免责声明：以上解读由 AI 生成，仅供参考。*"
            for char in disclaimer: yield char; await asyncio.sleep(0.01)

        return StreamingResponse(generate_basic(), media_type="text/event-stream")

    tool_result = None
    agent_status = ""
    rag_context = retrieve_rag_context(question)  # 调用升级后的 RAG

    size_match = re.search(r'(\d+(?:\.\d+)?)\s*mm', question, re.IGNORECASE)
    if size_match:
        size_mm = float(size_match.group(1))
        calc_volume = (4 / 3) * math.pi * (size_mm / 2) ** 3
        tool_result = f"患者假设结节直径为 {size_mm}mm，经内部数学工具计算，其理论体积约为 {calc_volume:.1f} mm³。"
        agent_status = f" **[Agent 决策]** 识别到尺寸参数，已自主调用【体积计算工具】...\n\n"

    async def generate_agent():
        if agent_status:
            for char in agent_status: yield char; await asyncio.sleep(0.02)
        if rag_context:
            prefix = "**[已检索到权威指南，回答基于 RAG 增强]**\n\n"
            for char in prefix: yield char; await asyncio.sleep(0.02)

        try:
            if not DEEPSEEK_API_KEY:
                mock_text = f"针对您的问题：“{question}”，"
                if tool_result: mock_text += f"(系统计算：{tool_result}) "
                mock_text += "建议您带好片子与主治医生面谈。"
                for char in mock_text: yield char; await asyncio.sleep(0.05)
            else:
                client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
                prompt_parts = [f"当前患者肺结节评估为【{risk_level}】，实际体积 {volume_mm3} mm³。"]
                if rag_context: prompt_parts.append(f"\n【权威指南参考】\n{rag_context}\n请优先基于指南回答。")
                if tool_result: prompt_parts.append(f"\n【工具计算结果】\n{tool_result}")
                prompt_parts.append(f"\n患者提问：“{question}”\n请用专业、耐心、安抚的语气回答。不要给出绝对诊断。")
                final_prompt = "\n".join(prompt_parts)

                response = client.chat.completions.create(model="deepseek-chat",
                                                          messages=[{"role": "user", "content": final_prompt}],
                                                          stream=True)
                for chunk in response:
                    if chunk.choices[0].delta.content is not None:
                        yield chunk.choices[0].delta.content
        except Exception:
            yield f"\n[系统提示] 网络繁忙，AI 医生暂时休息。"

        disclaimer = "\n\n---\n*⚕️ 免责声明：以上解读由人工智能大模型生成，仅供参考，不能替代专业医师诊断。*"
        for char in disclaimer: yield char; await asyncio.sleep(0.01)

    return StreamingResponse(generate_agent(), media_type="text/event-stream")


# ==========================================
# 8. 患者端 AI 健康助理接口
# ==========================================
@app.post("/api/patient_ai_chat")
async def patient_ai_chat(question: str = Form(...)):
    rag_context = retrieve_rag_context(question)  # 调用升级后的 RAG
    prompt = f"""
    你是一位亲切的肺部健康管家。请用通俗易懂、极具人文关怀的语气回答患者的健康咨询。
    【医学知识库参考】：{rag_context if rag_context else '无'}
    患者提问：“{question}”
    要求：避免使用生涩的医学术语，给予患者心理安慰，不要开具处方药。
    """

    async def generate():
        try:
            if not DEEPSEEK_API_KEY:
                mock_text = "您好，建议您保持良好心态，多吃润肺食物。如有不适请及时就医。"
                for char in mock_text: yield char; await asyncio.sleep(0.05)
            else:
                client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
                response = client.chat.completions.create(model="deepseek-chat",
                                                          messages=[{"role": "user", "content": prompt}], stream=True)
                for chunk in response:
                    if chunk.choices[0].delta.content is not None:
                        yield chunk.choices[0].delta.content
        except Exception:
            yield "\n[系统提示] 健康管家暂时休息，请稍后再试。"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ==========================================
# 9. 患者端 AI 健康日记分析接口
# ==========================================
@app.post("/api/diary_analysis")
async def diary_analysis(diary_text: str = Form(...)):
    # 如果日记里提到了某些症状，RAG 可以检索相关的安慰和建议
    rag_context = retrieve_rag_context(diary_text)

    prompt = f"""
    你是一位温柔、专业的肺部健康管家。
    患者今天记录了自己的身体状况：“{diary_text}”。

    【医学知识库参考】：{rag_context if rag_context else '无'}

    请根据患者的描述，给出针对性的健康建议和情绪安抚。
    要求：
    1. 语气要温暖、亲切，像家人一样。
    2. 如果患者有轻微症状（如咳嗽），给一些生活小建议；如果症状严重，提醒及时就医。
    3. 避免使用过于专业的医学术语。
    4. 字数控制在 150 字左右。
    """

    async def generate_diary():
        try:
            if not DEEPSEEK_API_KEY:
                mock_text = "看到您的日记啦，今天也要保持好心情哦！如果有不舒服，记得多喝温水，注意休息。"
                for char in mock_text: yield char; await asyncio.sleep(0.05)
            else:
                client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    stream=True
                )
                for chunk in response:
                    if chunk.choices[0].delta.content is not None:
                        yield chunk.choices[0].delta.content
        except Exception:
            yield "\n[系统提示] 日记管家暂时休息，请稍后再试。"

    return StreamingResponse(generate_diary(), media_type="text/event-stream")

# ==========================================
# 10. 患者端 AI 科普文章智能推荐接口
# ==========================================
from pydantic import BaseModel

class RecommendReq(BaseModel):
    risk_level: str = "无记录"
    user_id: int = 0

@app.post("/api/recommend_knowledge")
async def recommend_knowledge(req: RecommendReq):
    # 核心规则匹配逻辑 (根据风险等级推荐对应的文章索引，对应你前端的数组顺序)
    # 0:饮食, 1:运动, 2:心理, 3:复查, 4:影像, 5:吸烟, 6:遗传, 7:磨玻璃
    if req.risk_level == "高风险":
        target_idx = 7 # 推荐看磨玻璃/临床常见
        rule_text = "您的最新评估显示风险较高，建议优先了解磨玻璃结节（GGO）的临床处理原则，避免过度恐慌。"
    elif req.risk_level == "中风险":
        target_idx = 3 # 推荐看复查指南
        rule_text = "中风险结节需要密切关注，请重点阅读复查指南，了解何时需要立刻就医。"
    elif req.risk_level == "低风险":
        target_idx = 2 # 推荐心理调适
        rule_text = "低风险结节无需焦虑，90%以上都是良性。建议看看心理调适指南，放下包袱。"
    else:
        target_idx = 0 # 无记录，推荐饮食
        rule_text = "您还没有评估记录。建议从饮食调养开始，三分治七分养，为肺部健康打好基础。"

    prompt = f"""
    患者当前的肺结节 AI 评估结果为：{req.risk_level}。
    系统初步建议他阅读第 {target_idx} 篇文章。
    请以“AI 健康管家”的口吻，结合他的风险等级，写一段 40-60 字的推荐语，语气要温暖、专业，引导他去阅读。
    """

    async def generate_rec():
        try:
            if not DEEPSEEK_API_KEY:
                yield rule_text
            else:
                client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
                response = client.chat.completions.create(
                    model="deepseek-chat", messages=[{"role": "user", "content": prompt}], stream=True
                )
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
        except Exception:
            yield rule_text

    # 返回格式：流式文本 + 推荐的文章索引 (通过自定义头部或简单拼接返回，这里为了简单直接组合返回)
    # 更优雅的做法是前端发请求拿流式文本，索引直接在前端根据风险判断，这里为了演示大模型能力，文本走流式。
    # 由于 FastAPI 的 StreamingResponse 不好同时返回 JSON 和流，我们在前端通过风险等级先算好索引。
    return StreamingResponse(generate_rec(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)