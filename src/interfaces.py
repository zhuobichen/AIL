"""
系统核心接口定义 (Interfaces)

提供抽取器、画像器、生成器等核心组件的抽象基类，
实现依赖倒置原则 (DIP)，解耦流水线与具体实现。
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from .models import Relation, CharacterProfile

class BaseRelationshipExtractor(ABC):
    """关系抽取器抽象基类"""
    @abstractmethod
    def extract_relations_with_sentiment(self, text: str, characters: list[str]) -> List[Relation]:
        pass

class BaseCharacterProfiler(ABC):
    """人物画像器抽象基类"""
    @abstractmethod
    def profile_all(self, characters: list[str], text: str, relations: list[Relation]) -> Dict[str, CharacterProfile]:
        pass
        
    @abstractmethod
    async def profile_all_async(self, characters: list[str], text: str, relations: list[Relation]) -> Dict[str, CharacterProfile]:
        pass

class BaseNarrativeGenerator(ABC):
    """叙事生成器抽象基类"""
    @abstractmethod
    def generate_story(self, network_stats: Any, profiles: Dict[str, CharacterProfile], events: list[Any]) -> str:
        pass
