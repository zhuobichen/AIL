import json
import os
from typing import List, Dict, Any
from pydantic import BaseModel
from openai import AsyncOpenAI
from src.rag.knowledge_base import RAGKnowledgeBase

class SandboxRequest(BaseModel):
    task_id: str
    book: str
    what_if: str
    characters: List[str]
    num_turns: int = 3

class Message(BaseModel):
    character: str
    content: str
    action: str = ""

class SandboxResponse(BaseModel):
    script: List[Message]
    summary: str

class MultiAgentSandbox:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com/v1"
        )
        self.rag_db = RAGKnowledgeBase()
        
    async def simulate(self, req: SandboxRequest, profiles: Dict[str, Any], graph_data: Dict[str, Any]) -> SandboxResponse:
        # 1. 组装角色设定 (Profiles)
        char_profiles = {}
        for char in req.characters:
            if char in profiles:
                p = profiles[char]
                char_profiles[char] = f"性格：{', '.join(p.get('personality_traits', []))}\n简介：{p.get('description', '')}"
        
        # 2. 组装图谱关系 (Graph Context)
        relation_context = {}
        nodes = [n["id"] for n in graph_data.get("nodes", [])]
        for char in req.characters:
            relation_context[char] = []
            if char in nodes:
                edges = [e for e in graph_data.get("links", []) if e["source"] == char or e["target"] == char]
                for e in edges:
                    other = e["target"] if e["source"] == char else e["source"]
                    if other in req.characters:
                        sentiment = e.get("sentiment", "neutral")
                        relation_context[char].append(f"你与 {other} 的关系是 {e.get('type')} ({sentiment})")

        # 3. 组装 RAG 背景知识
        snippets = self.rag_db.search(query=" ".join(req.characters) + " " + req.what_if, book_name=req.book, top_k=3)
        rag_context = "\n".join([s.get('text', '') for s in snippets]) if snippets else "暂无背景知识"

        # 4. 链式记忆流多回合推演 (Memory Stream Loop)
        script_objs = []
        conversation_history = ""
        
        # 为了让对话有来有回，我们随机或者轮流让角色发言
        turn_order = req.characters * req.num_turns # e.g. [A, B, A, B, A, B]
        
        print(f"\n[Sandbox] 开始链式推演，共 {len(turn_order)} 步...")
        
        for i, current_char in enumerate(turn_order):
            print(f"  - 正在推演 {current_char} 的第 {i+1} 步行动...")
            
            # 构建专门针对 current_char 的 Agent Prompt
            char_prompt = f"""你正在扮演小说《{req.book}》中的角色：【{current_char}】。
请你完全沉浸在这个角色中，基于以下设定和当前情境，作出符合你人设的发言和动作。

【你的性格与设定】：
{char_profiles.get(current_char, "未知")}

【你对其他在场角色的看法】：
{chr(10).join(relation_context.get(current_char, []))}

【当前所处的平行世界假设(What-If)】：
{req.what_if}

【相关世界观与背景知识】：
{rag_context}

【之前的对话记忆(Memory Stream)】：
{conversation_history if conversation_history else "(对话刚刚开始，你是第一个发言的。)"}

请结合上面的记忆流，紧接上一句话，给出你作为【{current_char}】的自然回应。
必须输出合法的 JSON 对象，包含两个字段：
1. content: 你的说话内容。
2. action: 你的神态、心理活动或肢体动作描写。

示例：
{{"content": "师兄，如果我们当初...", "action": "低着头，不敢看对方的眼睛"}}
"""
            try:
                response = await self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": char_prompt}],
                    temperature=0.7, 
                    response_format={"type": "json_object"}
                )
                content = response.choices[0].message.content
                data = json.loads(content)
                
                msg_content = data.get("content", "")
                msg_action = data.get("action", "")
                
                script_objs.append(Message(
                    character=current_char,
                    content=msg_content,
                    action=msg_action
                ))
                
                # 更新全局链式记忆流
                conversation_history += f"[{current_char}] (动作:{msg_action}) 说：\"{msg_content}\"\n"
                
            except Exception as e:
                print(f"  [Sandbox Error] {current_char} 推演失败: {e}")
                continue

        # 5. 导演总结 (Director Summary)
        summary_prompt = f"""你是一个沙盘导演。请基于以下刚刚发生的推演对话，写一段100字左右的剧情小结。
假设前提：{req.what_if}
对话记录：
{conversation_history}

直接输出总结文本即可。"""
        
        try:
            summary_response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": summary_prompt}],
                temperature=0.5
            )
            summary = summary_response.choices[0].message.content
        except Exception as e:
            summary = "总结生成失败。"

        return SandboxResponse(
            script=script_objs,
            summary=summary
        )
