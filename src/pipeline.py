"""数字人文叙事分析流水线

将所有模块串联为端到端分析流程。
"""

from typing import Any, Optional
from datetime import datetime

from .base import NamedEntityRecognizer, CharacterAliasResolver, ChineseTextProcessor
from .network import RelationshipExtractor, CharacterNetworkBuilder, NetworkVisualizer
from .plot import TimelineExtractor, CausalChainAnalyzer
from .character import CharacterProfiler, RelationshipDynamicsAnalyzer
from .narrative import DestinyPredictor, NarrativeGenerator


class NarrativePipeline:
    """数字人文叙事分析流水线

    端到端处理流程：
    0. 简繁转换 → 1. 人物识别 → 2. 别名合并 → 3. 关系抽取 → 4. 网络构建
    → 5. 时间线提取 → 6. 因果分析 → 7. 人物刻画
    → 8. 关系动态 → 9. 命运预测 → 10. 故事生成
    """

    def __init__(
        self,
        ner_backend: str = "spacy",
        base_time: Optional[datetime] = None,
        character_names: Optional[list[str]] = None,
        convert_traditional: bool = False,
    ):
        """
        Args:
            ner_backend: NER 后端 ("spacy" 或 "transformers")
            base_time: 时间线基准时间
            character_names: 自定义人物名称白名单
            convert_traditional: 是否做繁→简转换
        """
        self.ner = NamedEntityRecognizer(
            backend=ner_backend,
            character_names=character_names,
        )
        self.alias_resolver = CharacterAliasResolver()
        self.relation_extractor = RelationshipExtractor()
        self.network_builder = CharacterNetworkBuilder()
        self.visualizer = NetworkVisualizer()
        self.timeline_extractor = TimelineExtractor(base_time=base_time)
        self.text_processor = ChineseTextProcessor()
        self.convert_traditional = convert_traditional
        self.causal_analyzer = CausalChainAnalyzer()
        self.profiler = CharacterProfiler()
        self.dynamics_analyzer = RelationshipDynamicsAnalyzer()
        self.destiny_predictor = DestinyPredictor()
        self.narrative_generator = NarrativeGenerator()

    def run(self, texts: list[str], verbose: bool = True) -> dict[str, Any]:
        """执行完整分析流水线

        Args:
            texts: 文本列表
            verbose: 是否打印进度

        Returns:
            完整的分析结果字典
        """
        results: dict[str, Any] = {"texts": texts, "num_texts": len(texts)}

        # ---- Phase 0: 文本预处理 ----
        if self.convert_traditional:
            if verbose:
                print("[Phase 0/5] 繁体→简体转换...")
            texts = [self.text_processor.traditional_to_simplified(t) for t in texts]
            results["texts_converted"] = texts

        # ---- Phase 1: 基础提取 ----
        if verbose:
            print("[Phase 1/5] 人物识别与别名合并...")

        all_text = "\n".join(texts)
        raw_characters = self.ner.extract_characters(all_text)
        results["raw_characters"] = raw_characters

        # 别名合并
        alias_groups = self.alias_resolver.resolve_aliases(all_text, raw_characters)
        characters = self.alias_resolver.merge_aliases(raw_characters, alias_groups)
        results["characters"] = characters
        results["alias_groups"] = alias_groups

        if verbose:
            print(f"  识别到 {len(characters)} 个独立人物（原始 {len(raw_characters)} 个实体）")

        # ---- Phase 2: 关系网络 ----
        if verbose:
            print("[Phase 2/5] 关系抽取与网络构建...")

        relations = self.relation_extractor.extract_relations_with_sentiment(
            all_text, characters
        )
        results["relations"] = relations

        G = self.network_builder.build_network(relations)
        network_analysis = self.network_builder.analyze_network()
        results["network_analysis"] = network_analysis

        if verbose:
            print(f"  提取 {len(relations)} 条关系，网络密度 {network_analysis.get('density', 0):.3f}")

        # ---- Phase 3: 情节重构 ----
        if verbose:
            print("[Phase 3/5] 时间线与因果分析...")

        events = self.timeline_extractor.extract_events(texts, characters)
        results["events"] = events

        causal_chains = self.causal_analyzer.analyze_causal_chains(events)
        results["causal_chains"] = causal_chains

        narrative_arc = self.causal_analyzer.build_narrative_arc(events)
        results["narrative_arc"] = narrative_arc

        if verbose:
            timed_events = [e for e in events if e.get("time")]
            print(f"  提取 {len(events)} 个事件（{len(timed_events)} 个有时间信息）")

        # ---- Phase 4: 人物刻画 ----
        if verbose:
            print("[Phase 4/5] 人物性格与关系动态...")

        profiles = self.profiler.profile_all(characters, texts)
        results["profiles"] = profiles

        dynamics = self.dynamics_analyzer.analyze_from_relations(relations)
        results["relationship_dynamics"] = dynamics

        if verbose:
            main_char = network_analysis.get("main_character", "?")
            print(f"  完成 {len(profiles)} 个人物刻画，主角: {main_char}")

        # ---- Phase 5: 叙事生成 ----
        if verbose:
            print("[Phase 5/5] 命运预测与故事生成...")

        destiny_results = {}
        for profile in profiles:
            destiny_results[profile["name"]] = self.destiny_predictor.predict_destiny(
                profile, narrative_arc
            )
        results["destiny_predictions"] = destiny_results

        story = self.narrative_generator.generate_story(results, style="dramatic")
        results["story"] = story

        summary = self.narrative_generator.generate_summary(results)
        results["summary"] = summary

        if verbose:
            print(f"  故事生成完毕，标题: {summary['title']}")
            print("分析完成！")

        return results

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
