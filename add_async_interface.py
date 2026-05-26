import sys

with open('src/interfaces.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_str = """class BaseCharacterProfiler(ABC):
    \"\"\"人物画像器抽象基类\"\"\"
    @abstractmethod
    def profile_all(self, characters: list[str], text: str, relations: list[Relation]) -> Dict[str, CharacterProfile]:
        pass"""

new_str = """class BaseCharacterProfiler(ABC):
    \"\"\"人物画像器抽象基类\"\"\"
    @abstractmethod
    def profile_all(self, characters: list[str], text: str, relations: list[Relation]) -> Dict[str, CharacterProfile]:
        pass
        
    @abstractmethod
    async def profile_all_async(self, characters: list[str], text: str, relations: list[Relation]) -> Dict[str, CharacterProfile]:
        pass"""

content = content.replace(old_str, new_str)
with open('src/interfaces.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Added async interface to profiler")