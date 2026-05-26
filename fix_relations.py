import hashlib
import json

with open('src/network/relations.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_cache = """    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_exception_type(Exception)
    )
    def _call_llm_with_retry(self, prompt: str) -> str:
        \"\"\"带重试机制和断点续传缓存的 LLM 调用\"\"\"
        # 使用 Prompt 的 MD5 哈希作为缓存 Key
        prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()
        if prompt_hash in self.cache:
            return self.cache[prompt_hash]
            
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
            timeout=30 # 增加超时保护
        )
        content = response.choices[0].message.content
        self.cache[prompt_hash] = content # 存入缓存
        return content"""

new_cache = """    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_exception_type(Exception)
    )
    def _call_llm_with_retry(self, prompt: str) -> str:
        \"\"\"带重试机制和断点续传缓存的 LLM 调用\"\"\"
        # 使用 Prompt 和模型参数的组合哈希作为缓存 Key，防止未来更换模型时读取了旧缓存
        cache_key_content = f"deepseek-chat_temp0.1_{prompt}"
        prompt_hash = hashlib.md5(cache_key_content.encode('utf-8')).hexdigest()
        
        if prompt_hash in self.cache:
            return self.cache[prompt_hash]
            
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
            timeout=30 # 增加超时保护
        )
        content = response.choices[0].message.content
        
        # 预验证 JSON 格式，如果 LLM 返回了损坏的 JSON，则抛出异常触发重试，并且不存入缓存
        try:
            json.loads(content)
        except json.JSONDecodeError:
            raise ValueError(f"LLM 返回了无效的 JSON 格式: {content[:100]}...")
            
        self.cache[prompt_hash] = content # 存入缓存
        return content"""

content = content.replace(old_cache, new_cache)

with open('src/network/relations_fixed.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Saved to relations_fixed.py")