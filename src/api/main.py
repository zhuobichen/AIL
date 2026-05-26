import os
import uuid
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from src.pipeline import NarrativePipeline
from src.base.character_dict import get_character_dict, get_character_mapping
from src.network import LLMRelationshipExtractor, RelationshipExtractor
from src.character import LLMCharacterProfiler, CharacterProfiler
from src.narrative import LLMNarrativeGenerator, NarrativeGenerator

load_dotenv()

app = FastAPI(
    title="数字人文叙事 AI API (To-C Edition)",
    description="面向文学爱好者的 AI 驱动的小说世界观解析与可视化平台 API",
    version="1.0.0"
)

# 允许跨域请求，方便前端联调
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 内存中的任务存储 (MVP阶段使用，生产环境应使用 Redis/PostgreSQL)
tasks_db: Dict[str, Dict[str, Any]] = {}

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: float
    message: str
    book_name: str
    created_at: float
    completed_at: Optional[float] = None
    results: Optional[Dict[str, Any]] = None

def run_analysis_task(task_id: str, text: str, book_name: str):
    """后台异步任务：运行叙事分析流水线"""
    try:
        tasks_db[task_id]["status"] = "processing"
        tasks_db[task_id]["message"] = "正在初始化 AI 引擎..."
        
        # 将文本拆分为段落
        paragraphs = [p.strip() for p in text.split('\n') if len(p.strip()) > 5]
        
        # 初始化 Pipeline
        llm_api_key = os.getenv("DEEPSEEK_API_KEY")
        if llm_api_key:
            relation_extractor = LLMRelationshipExtractor(api_key=llm_api_key)
            profiler = LLMCharacterProfiler(api_key=llm_api_key)
            narrative_generator = LLMNarrativeGenerator(api_key=llm_api_key)
        else:
            relation_extractor = RelationshipExtractor()
            profiler = CharacterProfiler()
            narrative_generator = NarrativeGenerator()
            
        pipeline = NarrativePipeline(
            relation_extractor=relation_extractor,
            profiler=profiler,
            narrative_generator=narrative_generator,
            character_names=get_character_dict(book_name),
            convert_traditional=True,
            strict_dict_mode=True,
            explicit_mapping=get_character_mapping(book_name)
        )
        
        tasks_db[task_id]["message"] = "正在深度阅读文本并进行实体与关系抽取 (这可能需要较长时间)..."
        tasks_db[task_id]["progress"] = 10.0
        
        # 运行分析 (这里如果需要真实进度条，需重构 pipeline.run 支持 callback，目前为了 MVP 简化处理)
        # TODO: 注入进度回调 callback 给 pipeline
        results = pipeline.run(paragraphs, verbose=False)
        
        tasks_db[task_id]["status"] = "completed"
        tasks_db[task_id]["progress"] = 100.0
        tasks_db[task_id]["message"] = "分析完成"
        tasks_db[task_id]["completed_at"] = time.time()
        # 转换 results 为 dict
        tasks_db[task_id]["results"] = results.model_dump()
        
    except Exception as e:
        tasks_db[task_id]["status"] = "failed"
        tasks_db[task_id]["message"] = f"分析失败: {str(e)}"
        print(f"Task {task_id} failed: {e}")

@app.post("/api/v1/tasks/upload", response_model=TaskStatusResponse)
async def upload_and_analyze(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    book: str = Form("hongloumeng")
):
    """上传文本文件并创建分析任务"""
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported currently.")
        
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = content.decode("gbk")
        except:
            raise HTTPException(status_code=400, detail="Failed to decode file. Please ensure it is UTF-8 or GBK encoded.")
    
    task_id = str(uuid.uuid4())
    current_time = time.time()
    
    tasks_db[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0.0,
        "message": "任务已创建，等待调度",
        "book_name": book,
        "created_at": current_time,
    }
    
    background_tasks.add_task(run_analysis_task, task_id, text, book)
    
    return TaskStatusResponse(**tasks_db[task_id])

@app.get("/api/v1/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """获取指定任务的状态与进度"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task_info = tasks_db[task_id].copy()
    # 如果任务未完成，不返回完整的 results 以减少网络传输
    if task_info["status"] != "completed":
        task_info["results"] = None
        
    return TaskStatusResponse(**task_info)

@app.get("/api/v1/tasks/{task_id}/results")
async def get_task_results(task_id: str):
    """获取指定任务的完整分析结果"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if tasks_db[task_id]["status"] != "completed":
        raise HTTPException(status_code=400, detail="Task is not completed yet")
        
    return tasks_db[task_id]["results"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
