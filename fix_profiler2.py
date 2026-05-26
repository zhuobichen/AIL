import sys

with open('src/character/profiler.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_str = """class LLMCharacterProfiler:
    \"\"\"基于大模型的人物性格刻画器\"\"\"

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.role_thresholds = {
            "protagonist": 0.3,
            "supporting": 0.2,
            "minor": 0.1,
            "background": 0.0,
        }

    def profile_all(
        self, characters: list[str], texts: list[str]
    ) -> List[CharacterProfile]:"""

new_str = """from ..interfaces import BaseCharacterProfiler

class LLMCharacterProfiler(BaseCharacterProfiler):
    \"\"\"基于大模型的人物性格刻画器\"\"\"

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.api_key = api_key
        self.base_url = base_url
        self.role_thresholds = {
            "protagonist": 0.3,
            "supporting": 0.2,
            "minor": 0.1,
            "background": 0.0,
        }

    def profile_all(self, characters: list[str], texts: list[str], relations: list = None) -> Dict[str, CharacterProfile]:
        \"\"\"同步调用方式 (为了向后兼容)\"\"\"
        import asyncio
        return asyncio.run(self.profile_all_async(characters, texts, relations or []))

    async def profile_all_async(self, characters: list[str], texts: list[str], relations: list = None) -> Dict[str, CharacterProfile]:
        \"\"\"对所有核心人物进行大模型并发画像\"\"\"
        import asyncio
        from openai import AsyncOpenAI
        
        # 使用异步客户端
        async_client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        profiles = {}
        
        # 频率统计
        char_counts = {c: sum(1 for t in texts if c in t) for c in characters}  
        top_chars = sorted(char_counts.keys(), key=lambda x: char_counts[x], reverse=True)[:10]
        
        async def fetch_profile(name: str):
            try:
                character_texts = [t for t in texts if name in t]
                presence_ratio = len(character_texts) / max(len(texts), 1)
                role = self._infer_role(name, character_texts, texts, characters)

                # 将文本拼接，限制长度
                context = "\\n".join(character_texts)[:3000]

                prompt = f\"\"\"
你是一个古典文学数字人文分析专家。请根据以下关于人物【{name}】的文本片段，分析其性格特质和情感倾向。

请输出 JSON 格式，包含以下结构:
{{
  "traits": {{
    "leadership": 0.0到1.0的浮点数,
    "creativity": 0.0到1.0的浮点数,
    "agreeableness": 0.0到1.0的浮点数,
    "conscientiousness": 0.0到1.0的浮点数,
    "extraversion": 0.0到1.0的浮点数,
    "emotional_stability": 0.0到1.0的浮点数,
    "assertiveness": 0.0到1.0的浮点数,
    "cooperativeness": 0.0到1.0的浮点数
  }},
  "emotions": {{
    "dominant": "主导情感(例如: 愤怒, 喜悦, 悲伤, 中立等)",
    "valence": "情感效价(positive, negative, 或 neutral)"
  }},
  "personality_summary": "一段简短的人物性格与行为总结（50字以内）"
}}

文本片段:
{context}
\"\"\"
                response = await async_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.3
                )
                import json
                data = json.loads(response.choices[0].message.content)

                traits_data = data.get("traits", {})
                emotions_data = data.get("emotions", {})

                profile = CharacterProfile(
                    name=name,
                    role_in_story=role,
                    total_mentions=len(character_texts),
                    presence_ratio=presence_ratio,
                    traits=Traits(**{k: float(v) for k, v in traits_data.items() if hasattr(Traits, k)}),
                    emotions=EmotionProfile(
                        dominant=emotions_data.get("dominant", "neutral"),
                        valence=emotions_data.get("valence", "neutral"),
                        distribution={}
                    ),
                    communication_style=CommunicationStyle(),
                    personality_summary=data.get("personality_summary", "大模型分析完成。")
                )
                return name, profile
            except Exception as e:
                print(f"  [LLM Profiler Error for {name}] {e}")
                return name, None

        print(f"  [LLM] 正在并发刻画前 {len(top_chars)} 位核心人物的心理画像...")
        # 并发执行所有 API 请求
        tasks = [fetch_profile(name) for name in top_chars if char_counts[name] > 0]
        results = await asyncio.gather(*tasks)
        
        # 将结果转换为字典
        for name, profile in results:
            if profile:
                profiles[name] = profile
                
        # 填充非前 10 的人物
        for name in characters:
            if name not in profiles:
                role = self._infer_role(name, [t for t in texts if name in t], texts, characters)
                profiles[name] = CharacterProfile(
                    name=name,
                    role_in_story=role,
                    total_mentions=char_counts[name],
                    presence_ratio=char_counts[name] / max(len(texts), 1),      
                    traits=Traits(),
                    emotions=EmotionProfile(),
                    communication_style=CommunicationStyle(),
                    personality_summary="出现次数较少，暂无足够信息。"
                )
                
        return profiles

    def _old_profile_all(
        self, characters: list[str], texts: list[str]
    ) -> List[CharacterProfile]:"""

content = content.replace(old_str, new_str)

old_str2 = """class CharacterProfiler:"""

new_str2 = """class CharacterProfiler(BaseCharacterProfiler):"""

content = content.replace(old_str2, new_str2)

with open('src/character/profiler_fixed3.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Replaced profiler.py with async and interfaces.')