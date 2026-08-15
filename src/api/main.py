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

# 全局单例 RAG 知识库，避免重复冷启动
rag_db_instance = None

def get_rag_db():
    global rag_db_instance
    if rag_db_instance is None:
        from src.rag.knowledge_base import RAGKnowledgeBase
        rag_db_instance = RAGKnowledgeBase()
    return rag_db_instance

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

from src.simulation.sandbox import SandboxRequest, MultiAgentSandbox

@app.post("/api/v1/simulation/run")
async def run_simulation(req: SandboxRequest):
    if req.task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task_data = tasks_db[req.task_id]
    if task_data["status"] != "completed":
        raise HTTPException(status_code=400, detail="Task is not completed yet")
        
    profiles_list = task_data["results"].get("profiles", [])
    profiles_dict = {p["name"]: p for p in profiles_list}
    graph_data = task_data["results"].get("network_analysis", {}).get("graph_data", {})
    
    # 将沙盘实例化，并注入单例的 rag_db
    sandbox = MultiAgentSandbox()
    sandbox.rag_db = get_rag_db()
    
    try:
        res = await sandbox.simulate(req, profiles_dict, graph_data)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    task_id: str
    query: str
    book: str

@app.post("/api/v1/rag/chat")
async def rag_chat(req: ChatRequest):
    try:
        from openai import AsyncOpenAI
        import os
        
        rag_db = get_rag_db()
        snippets = rag_db.search(query=req.query, book_name=req.book, top_k=5)
        
        # 2. 图谱检索 (Graph RAG)
        graph_context = ""
        if req.task_id and req.task_id in tasks_db and tasks_db[req.task_id]["status"] == "completed":
            graph_data = tasks_db[req.task_id]["results"]["network_analysis"]["graph_data"]
            nodes = [n["id"] for n in graph_data.get("nodes", [])]
            # 简单的实体链接：看 query 中命中了哪些人物节点
            matched_entities = [n for n in nodes if n in req.query]
            if matched_entities:
                graph_context = "【图谱知识库检索结果】：\n"
                for entity in matched_entities:
                    # 查找该实体的一度关联边
                    edges = [e for e in graph_data.get("links", []) if e["source"] == entity or e["target"] == entity]
                    # 按照权重排序，取 top 5
                    edges = sorted(edges, key=lambda x: x.get("weight", 0), reverse=True)[:5]
                    if edges:
                        graph_context += f"人物 [{entity}] 的核心关系网：\n"
                        for e in edges:
                            other = e["target"] if e["source"] == entity else e["source"]
                            sentiment_str = "亲密" if e.get("sentiment") == "positive" else "敌对" if e.get("sentiment") == "negative" else "中立"
                            graph_context += f"  - 与 [{other}] 是 {e.get('type', '关联')} 关系 ({sentiment_str})，互动片段：\"{e.get('context_snippet', '')}\"\n"
                graph_context += "\n"
        
        if not snippets and not graph_context:
            return {"answer": "在原著及图谱中未检索到相关内容。", "sources": []}
            
        # 3. 组装上下文
        text_context = "【原著文本检索结果】：\n" + "\n\n".join([f"片段 {i+1}:\n{s['text']}" for i, s in enumerate(snippets)])
        
        combined_context = f"{graph_context}{text_context}"
        
        # 4. 大模型回答
        client = AsyncOpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com/v1"
        )
        
        prompt = f"""你是一个数字人文研究助手。请基于以下基于 GraphRAG (图谱+文本双重检索) 获取的上下文，回答用户的问题。
要求：
1. 必须严格基于提供的图谱关系和原文片段回答，不要编造。
2. 尽可能综合图谱中的宏观关系与文本片段中的微观细节。
3. 如果上下文不足以回答，请明确告知。

{combined_context}

【用户问题】：{req.query}
"""
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        return {
            "answer": response.choices[0].message.content,
            "sources": snippets,
            "graph_entities": matched_entities if 'matched_entities' in locals() else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
