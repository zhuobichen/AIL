"""数字人文叙事分析领域模型定义

使用 Pydantic 定义核心数据结构，提供强类型校验和自动序列化。
"""

from typing import List, Dict, Optional, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field

# ==========================================
# 1. 基础模型 (Base Models)
# ==========================================

class TimeInfo(BaseModel):
    """时间信息"""
    type: str = Field(..., description="时间类型：absolute 绝对时间，relative 相对时间")
    text: str = Field(..., description="原始文本表述")
    timestamp: Optional[datetime] = Field(None, description="解析后的时间戳")
    reference: Optional[str] = Field(None, description="相对时间的参照词（如：昨天）")


class Event(BaseModel):
    """叙事事件"""
    description: str = Field(..., description="事件摘要描述")
    raw_text: str = Field(..., description="原始文本段落")
    characters: List[str] = Field(default_factory=list, description="参与该事件的人物列表")
    time: Optional[TimeInfo] = Field(None, description="事件发生的时间")


class Relation(BaseModel):
    """人物关系互动"""
    source: str = Field(..., description="发起方/主体")
    target: str = Field(..., description="接收方/客体")
    type: str = Field(default="unknown", description="关系类型，例如：朋友、死敌、师徒等")
    context_snippet: str = Field(default="", description="原著中能体现这段关系的简短原文片段")
    context: str = Field(default="", description="提取该关系的上下文文本")
    chunk_index: int = Field(default=-1, description="所属文本块的顺序索引，用于时间轴演化分析")
    position: int = Field(default=0, description="在文本中的位置索引")
    sentiment: Literal['positive', 'negative', 'neutral'] = Field(default='neutral', description="情感极性：敌对/亲密/中立")
    time: Optional[TimeInfo] = Field(None, description="互动发生的时间")
    location: str = Field(default="", description="关系发生的地点/场景")

# ==========================================
# 2. 人物画像模型 (Character Profiles)
# ==========================================

class Traits(BaseModel):
    """大五人格及扩展特质 (归一化到 0-1)"""
    leadership: float = 0.0
    creativity: float = 0.0
    agreeableness: float = 0.0
    conscientiousness: float = 0.0
    extraversion: float = 0.0
    emotional_stability: float = 0.0
    assertiveness: float = 0.0
    cooperativeness: float = 0.0

class EmotionProfile(BaseModel):
    """人物情感特征"""
    dominant: str = Field(default="neutral", description="主导情感")
    valence: str = Field(default="neutral", description="情感效价 (positive, negative, neutral)")
    distribution: Dict[str, int] = Field(default_factory=dict, description="各种情感词的出现频次")

class CommunicationStyle(BaseModel):
    """沟通风格"""
    verbosity: float = 0.0
    frequency: int = 0
    initiation: int = 0
    responsiveness: int = 0

class CharacterProfile(BaseModel):
    """人物完整画像"""
    name: str = Field(..., description="人物规范名称")
    role_in_story: str = Field(default="background", description="在故事中的角色地位 (protagonist, supporting, minor, background)")
    personality_summary: str = Field(default="", description="性格自然语言总结")
    total_mentions: int = Field(default=0, description="被提及的总次数")
    presence_ratio: float = Field(default=0.0, description="出场率")
    traits: Traits = Field(default_factory=Traits)
    emotions: EmotionProfile = Field(default_factory=EmotionProfile)
    communication_style: CommunicationStyle = Field(default_factory=CommunicationStyle)
    locations: List[str] = Field(default_factory=list, description="该人物常出现的地点")

# ==========================================
# 3. 网络分析模型 (Network Analysis)
# ==========================================

class NetworkStats(BaseModel):
    """社交网络统计指标"""
    num_characters: int = 0
    num_relations: int = 0
    density: float = 0.0
    main_character: Optional[str] = None
    bridge_character: Optional[str] = None
    communities: List[List[str]] = Field(default_factory=list, description="社区划分列表")
    degree_centrality: Dict[str, float] = Field(default_factory=dict)
    betweenness_centrality: Dict[str, float] = Field(default_factory=dict)

# ==========================================
# 4. 情节与命运模型 (Plot & Destiny)
# ==========================================

class CausalChain(BaseModel):
    """因果链节点"""
    event: Event
    index: int
    causes: List[Event] = Field(default_factory=list)
    effects: List[Event] = Field(default_factory=list)
    is_turning_point: bool = False

class NarrativeArc(BaseModel):
    """叙事弧线 (五幕剧结构)"""
    exposition: List[Event] = Field(default_factory=list)
    rising_action: List[Event] = Field(default_factory=list)
    climax: List[Event] = Field(default_factory=list)
    falling_action: List[Event] = Field(default_factory=list)
    resolution: List[Event] = Field(default_factory=list)

class DestinyPrediction(BaseModel):
    """单个人物命运预测结果"""
    character: str
    overall_outlook: Literal['positive', 'negative', 'neutral'] = Field(..., description="总体走向 (positive, negative, neutral)")
    overall_confidence: float = Field(..., description="预测置信度")
    summary: str = Field(..., description="命运预测总结")
    predictions: List[Dict[str, Any]] = Field(default_factory=list, description="具体的预测细项")

# ==========================================
# 5. 全局流水线结果 (Pipeline Result)
# ==========================================

class NetworkAnalysis(BaseModel):
    degree_centrality: Dict[str, float]
    betweenness_centrality: Dict[str, float]
    communities: List[List[str]]
    main_character: str
    density: float = 0.0
    graph_data: Dict
    temporal_graphs: Optional[List[Dict]] = Field(default=None, description="按时间/章节序列演化的图谱快照")

class NarrativeAnalysisResult(BaseModel):
    """端到端流水线输出总模型"""
    num_texts: int
    characters: List[str]
    raw_characters: List[str]
    alias_groups: List[Dict[str, Any]]
    
    events: List[Event]
    relations: List[Relation]
    
    network_analysis: NetworkAnalysis
    profiles: List[CharacterProfile]
    
    causal_chains: List[CausalChain]
    narrative_arc: NarrativeArc
    destiny_predictions: Dict[str, DestinyPrediction]
    
    story: str = ""
    summary: Dict[str, Any] = Field(default_factory=dict)
