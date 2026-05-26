import sys

with open('src/pipeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_str = """    def __init__(
        self,
        ner_backend: str = "spacy",
        base_time: Optional[datetime] = None,
        character_names: Optional[list[str]] = None,
        convert_traditional: bool = False,
        strict_dict_mode: bool = False,
        explicit_mapping: Optional[dict[str, list[str]]] = None,
        llm_api_key: Optional[str] = None,
    ):
        \"\"\"
        Args:
            ner_backend: NER 后端 ("spacy" 或 "transformers")
            base_time: 时间线基准时间
            character_names: 自定义人物名称白名单
            convert_traditional: 是否做繁→简转换
            strict_dict_mode: 是否仅使用白名单词典提取人物
            explicit_mapping: 显式别名映射表
            llm_api_key: 用于启用大模型分析的 API Key
        \"\"\"
        self.ner = NamedEntityRecognizer(
            backend=ner_backend,
            character_names=character_names,
            strict_dict_mode=strict_dict_mode,
        )
        self.alias_resolver = CharacterAliasResolver()
        if llm_api_key:
            self.relation_extractor = LLMRelationshipExtractor(api_key=llm_api_key)
            self.profiler = LLMCharacterProfiler(api_key=llm_api_key)
            self.narrative_generator = LLMNarrativeGenerator(api_key=llm_api_key)
        else:
            self.relation_extractor = RelationshipExtractor()
            self.profiler = CharacterProfiler()
            self.narrative_generator = NarrativeGenerator()
            
        self.network_builder = CharacterNetworkBuilder()
        self.visualizer = NetworkVisualizer()
        self.timeline_extractor = TimelineExtractor(base_time=base_time)
        self.text_processor = ChineseTextProcessor()
        self.convert_traditional = convert_traditional
        self.explicit_mapping = explicit_mapping
        self.causal_analyzer = CausalChainAnalyzer()
        self.dynamics_analyzer = RelationshipDynamicsAnalyzer()
        self.destiny_predictor = DestinyPredictor()"""

new_str = """    def __init__(
        self,
        relation_extractor=None,
        profiler=None,
        narrative_generator=None,
        ner_backend: str = "spacy",
        base_time: Optional[datetime] = None,
        character_names: Optional[list[str]] = None,
        convert_traditional: bool = False,
        strict_dict_mode: bool = False,
        explicit_mapping: Optional[dict[str, list[str]]] = None,
    ):
        \"\"\"
        Args:
            relation_extractor: 注入的关系抽取器实例 (符合 BaseRelationshipExtractor 接口)
            profiler: 注入的人物画像器实例 (符合 BaseCharacterProfiler 接口)
            narrative_generator: 注入的叙事生成器实例 (符合 BaseNarrativeGenerator 接口)
            ner_backend: NER 后端 ("spacy" 或 "transformers")
            base_time: 时间线基准时间
            character_names: 自定义人物名称白名单
            convert_traditional: 是否做繁→简转换
            strict_dict_mode: 是否仅使用白名单词典提取人物
            explicit_mapping: 显式别名映射表
        \"\"\"
        # 依赖注入 (Dependency Injection)
        # 如果未提供实例，则默认使用基于规则/词频的实现
        self.relation_extractor = relation_extractor or RelationshipExtractor()
        self.profiler = profiler or CharacterProfiler()
        self.narrative_generator = narrative_generator or NarrativeGenerator()

        self.ner = NamedEntityRecognizer(
            backend=ner_backend,
            character_names=character_names,
            strict_dict_mode=strict_dict_mode,
        )
        self.alias_resolver = CharacterAliasResolver()
            
        self.network_builder = CharacterNetworkBuilder()
        self.visualizer = NetworkVisualizer()
        self.timeline_extractor = TimelineExtractor(base_time=base_time)
        self.text_processor = ChineseTextProcessor()
        self.convert_traditional = convert_traditional
        self.explicit_mapping = explicit_mapping
        self.causal_analyzer = CausalChainAnalyzer()
        self.dynamics_analyzer = RelationshipDynamicsAnalyzer()
        self.destiny_predictor = DestinyPredictor()"""

content = content.replace(old_str, new_str)

with open('src/pipeline_fixed.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Replaced pipeline.py init logic.')