import sys

with open('src/character/profiler.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_str = """    def profile_all(self, characters: list[str], text: str, relations: list[Relation]) -> Dict[str, CharacterProfile]:
        \"\"\"对所有核心人物进行大模型画像\"\"\"
        profiles = {}
        for char in characters:
            try:
                # 提取与该人物相关的上下文 (简化处理，实际应基于文本片段)
                char_relations = [r for r in relations if r.source == char or r.target == char]
                
                prompt = f\"\"\"
                分析小说人物: {char}。
                已知他/她的关系网络：{char_relations}。
                请结合这些信息，输出该人物的心理画像。
                \"\"\"
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                profiles[char] = CharacterProfile(
                    name=char,
                    traits=["LLM_Extracted"],
                    role="Main",
                    sentiment_bias=0.5
                )
            except Exception as e:
                print(f"Error profiling {char}: {e}")
        return profiles"""

new_str = """    def profile_all(self, characters: list[str], text: str, relations: list[Relation]) -> Dict[str, CharacterProfile]:
        \"\"\"同步调用方式 (为了向后兼容)\"\"\"
        import asyncio
        return asyncio.run(self.profile_all_async(characters, text, relations))

    async def profile_all_async(self, characters: list[str], text: str, relations: list[Relation]) -> Dict[str, CharacterProfile]:
        \"\"\"对所有核心人物进行大模型并发画像\"\"\"
        import asyncio
        from openai import AsyncOpenAI
        
        # 使用异步客户端
        async_client = AsyncOpenAI(api_key=self.client.api_key, base_url=self.client.base_url)
        profiles = {}
        
        async def fetch_profile(char: str):
            try:
                char_relations = [r for r in relations if r.source == char or r.target == char]
                # 选取前 10 条关系防止 Prompt 过长
                char_relations = char_relations[:10]
                
                prompt = f\"\"\"
你是一个文学分析专家。请分析小说人物: {char}。
已知他/她的关系片段：{char_relations}。
请结合这些信息，推测该人物的性格特点。输出 JSON 格式:
{{
    "traits": ["勇敢", "孤僻"],
    "role": "主角/配角",
    "sentiment_bias": 0.8
}}
\"\"\"
                response = await async_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                import json
                data = json.loads(response.choices[0].message.content)
                return char, CharacterProfile(
                    name=char,
                    traits=data.get("traits", []),
                    role=data.get("role", "Unknown"),
                    sentiment_bias=float(data.get("sentiment_bias", 0.5))
                )
            except Exception as e:
                print(f"  [LLM Profiler Error for {char}] {e}")
                return char, None

        print(f"  [LLM] 正在并发刻画 {len(characters)} 位核心人物的心理画像...")
        # 并发执行所有 API 请求
        tasks = [fetch_profile(char) for char in characters]
        results = await asyncio.gather(*tasks)
        
        for char, profile in results:
            if profile:
                profiles[char] = profile
                
        return profiles"""

if old_str in content:
    content = content.replace(old_str, new_str)
    with open('src/character/profiler_fixed2.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Replaced async profiler logic.')
else:
    print('old_str not found in profiler!')