"""数字人文叙事分析流水线

将所有模块串联为端到端分析流程。
"""

from typing import Any, Optional, Dict
from datetime import datetime

from .base import NamedEntityRecognizer, CharacterAliasResolver, ChineseTextProcessor
from .network import RelationshipExtractor, LLMRelationshipExtractor, CharacterNetworkBuilder, NetworkVisualizer
from .plot import TimelineExtractor, CausalChainAnalyzer
from .character import CharacterProfiler, LLMCharacterProfiler, RelationshipDynamicsAnalyzer
from .narrative import DestinyPredictor, NarrativeGenerator, LLMNarrativeGenerator
from .models import NarrativeAnalysisResult, DestinyPrediction


class NarrativePipeline:
    """数字人文叙事分析流水线

    端到端处理流程：
    0. 简繁转换 → 1. 人物识别 → 2. 别名合并 → 3. 关系抽取 → 4. 网络构建
    → 5. 时间线提取 → 6. 因果分析 → 7. 人物刻画
    → 8. 关系动态 → 9. 命运预测 → 10. 故事生成
    """

    def __init__(
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
        """
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
        """
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
        self.destiny_predictor = DestinyPredictor()

    def run(self, texts: list[str], verbose: bool = True) -> NarrativeAnalysisResult:
        """执行完整分析流水线

        Args:
            texts: 文本列表
            verbose: 是否打印进度

        Returns:
            完整的 NarrativeAnalysisResult 对象
        """
        # ---- Phase 0: 文本预处理 ----
        converted_texts = texts
        if self.convert_traditional:
            if verbose:
                print("[Phase 0/5] 繁体→简体转换...")
            converted_texts = [self.text_processor.traditional_to_simplified(t) for t in texts]

        # ---- Phase 1: 基础提取 ----
        if verbose:
            print("[Phase 1/5] 人物识别与别名合并...")

        all_text = "\n".join(converted_texts)
        raw_characters = self.ner.extract_characters(all_text)

        # 别名合并
        if self.explicit_mapping:
            alias_groups = [{"canonical_name": k, "aliases": v} for k, v in self.explicit_mapping.items()]
        else:
            alias_groups = self.alias_resolver.resolve_aliases(all_text, raw_characters)
            
        characters = self.alias_resolver.merge_aliases(raw_characters, alias_groups)

        # 统一文本中的称呼（将别名替换为规范名）
        alias_map = {}
        for group in alias_groups:
            canonical = group["canonical_name"]
            for alias in group["aliases"]:
                if alias != canonical:
                    alias_map[alias] = canonical
                
        # 按别名长度降序排序
        sorted_aliases = sorted(alias_map.keys(), key=len, reverse=True)
        
        def replace_aliases(text: str) -> str:
            # 一个简单的多遍替换策略，避免嵌套替换问题
            for alias in sorted_aliases:
                canonical = alias_map[alias]
                # 先把规范名替换为占位符，防止被子串替换
                placeholder = f"__CANONICAL_{hash(canonical)}__"
                text = text.replace(canonical, placeholder)
                text = text.replace(alias, canonical)
                text = text.replace(placeholder, canonical)
            return text

        all_text = replace_aliases(all_text)
        converted_texts = [replace_aliases(t) for t in converted_texts]

        if verbose:
            print(f"  识别到 {len(characters)} 个独立人物（原始 {len(raw_characters)} 个实体）")

        # ---- Phase 2: 关系网络 ----
        if verbose:
            print("[Phase 2/5] 关系抽取与网络构建...")

        relations = self.relation_extractor.extract_relations_with_sentiment(
            all_text, characters
        )

        G = self.network_builder.build_network(relations)
        network_analysis = self.network_builder.analyze_network()

        if verbose:
            print(f"  提取 {len(relations)} 条关系，网络密度 {network_analysis.density:.3f}")

        # ---- Phase 3: 情节重构 ----
        if verbose:
            print("[Phase 3/5] 时间线与因果分析...")

        events = self.timeline_extractor.extract_events(converted_texts, characters)

        causal_chains = self.causal_analyzer.analyze_causal_chains(events)

        narrative_arc = self.causal_analyzer.build_narrative_arc(events)

        if verbose:
            timed_events = [e for e in events if e.time]
            print(f"  提取 {len(events)} 个事件（{len(timed_events)} 个有时间信息）")

        # ---- Phase 4: 人物刻画 ----
        if verbose:
            print("[Phase 4/5] 人物性格与关系动态...")

        profiles = self.profiler.profile_all(characters, converted_texts)

        if verbose:
            main_char = network_analysis.main_character or "?"
            print(f"  完成 {len(profiles)} 个人物刻画，主角: {main_char}")

        # ---- Phase 5: 叙事生成 ----
        if verbose:
            print("[Phase 5/5] 命运预测与故事生成...")

        destiny_results: Dict[str, DestinyPrediction] = {}
        for profile in profiles:
            destiny_results[profile.name] = self.destiny_predictor.predict_destiny(
                profile, narrative_arc
            )
            
        # 组装结果对象以传递给生成器
        result = NarrativeAnalysisResult(
            num_texts=len(texts),
            characters=characters,
            raw_characters=raw_characters,
            alias_groups=alias_groups,
            events=events,
            relations=relations,
            network_analysis=network_analysis,
            profiles=profiles,
            causal_chains=causal_chains,
            narrative_arc=narrative_arc,
            destiny_predictions=destiny_results
        )

        # 这里 NarrativeGenerator 需要一个字典，为了兼容我们先将其 dump
        result_dict = result.model_dump()
        story = self.narrative_generator.generate_story(result_dict, style="dramatic")
        summary = self.narrative_generator.generate_summary(result_dict)
        
        result.story = story
        result.summary = summary

        if verbose:
            print(f"  故事生成完毕，标题: {summary.get('title', '未知')}")
            print("分析完成！")

        return result

    def quick_analysis(self, texts: list[str]) -> dict[str, Any]:
        """快速分析（无输出），返回精简结果"""
        results = self.run(texts, verbose=False)

        return {
            "num_texts": results["num_texts"],
            "num_characters": len(results["characters"]),
            "characters": results["characters"],
            "main_character": results["network_analysis"].get("main_character"),
            "num_events": len(results["events"]),
            "profiles": [
                {
                    "name": p["name"],
                    "role": p["role_in_story"],
                    "summary": p.get("personality_summary", ""),
                }
                for p in results["profiles"]
            ],
            "network_density": results["network_analysis"].get("density", 0),
            "themes": results["summary"].get("themes", []),
        }

    def visualize_network(
        self, output_path: str = "character_network.html", interactive: bool = True
    ) -> str:
        """生成网络可视化

        Args:
            output_path: 输出路径
            interactive: True 使用自包含 HTML，False 使用 matplotlib 静态图

        Returns:
            输出文件路径
        """
        self.visualizer.set_graph(self.network_builder.G)
        if interactive:
            return self.visualizer.to_standalone_html(output_path)
        else:
            return self.visualizer.to_matplotlib(output_path)
