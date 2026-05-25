"""命运预测器

基于叙事模式匹配和性格特质分析，预测人物命运走向。
"""

from typing import Any


class DestinyPredictor:
    """命运预测器

    通过匹配经典叙事模式、分析性格-命运关联，对人物未来走向进行概率性预测。
    """

    def __init__(self):
        # 经典叙事模式库
        self.narrative_patterns: dict[str, dict[str, Any]] = {
            "rise_and_fall": {
                "pattern": [
                    "initial_success",
                    "growing_pride",
                    "critical_mistake",
                    "downfall",
                ],
                "example": "项羽 - 从破釜沉舟到垓下之围",
                "description": "崛起与陨落型：从成功走向因骄傲导致的失败",
            },
            "redemption_arc": {
                "pattern": [
                    "mistake",
                    "suffering",
                    "realization",
                    "redemption",
                ],
                "example": "廉颇 - 负荆请罪",
                "description": "救赎弧线型：犯错后通过反省获得救赎",
            },
            "tragic_hero": {
                "pattern": [
                    "noble_intent",
                    "fatal_flaw",
                    "inevitable_doom",
                ],
                "example": "哈姆雷特 - 延宕的复仇",
                "description": "悲剧英雄型：因性格缺陷走向注定的失败",
            },
            "underdog_triumph": {
                "pattern": [
                    "obscurity",
                    "opportunity",
                    "struggle",
                    "victory",
                ],
                "example": "刘邦 - 从亭长到汉高祖",
                "description": "逆袭型：从低微出身走向成功",
            },
            "steady_growth": {
                "pattern": [
                    "foundation",
                    "challenge",
                    "learning",
                    "mastery",
                ],
                "example": "持续成长型：通过不断学习克服挑战",
                "description": "稳步成长型：逐步积累经验与能力",
            },
            "fall_from_grace": {
                "pattern": [
                    "high_status",
                    "betrayal",
                    "loss",
                    "exile",
                ],
                "example": "林冲 - 从八十万禁军教头到落草",
                "description": "沉沦型：因外部打击从高处跌落",
            },
        }

        # 性格-命运关联规则
        self.trait_destiny_rules = [
            {
                "condition": lambda t: t.get("leadership", 0) > 0.6 and t.get("emotional_stability", 0) < 0.3,
                "type": "risk",
                "description": "强势领导风格 + 情绪不稳定 → 可能导致团队冲突或决策失误",
                "probability": 0.65,
            },
            {
                "condition": lambda t: t.get("leadership", 0) > 0.5 and t.get("agreeableness", 0) > 0.4,
                "type": "opportunity",
                "description": "领导力 + 合作精神 → 有望成为优秀的团队领导者",
                "probability": 0.75,
            },
            {
                "condition": lambda t: t.get("creativity", 0) > 0.5 and t.get("conscientiousness", 0) > 0.4,
                "type": "opportunity",
                "description": "创造力 + 执行力 → 项目成功率高，有望获得突破",
                "probability": 0.80,
            },
            {
                "condition": lambda t: t.get("extraversion", 0) > 0.5 and t.get("agreeableness", 0) < 0.2,
                "type": "risk",
                "description": "外向但缺乏合作性 → 可能被视为过于强势或孤立",
                "probability": 0.55,
            },
            {
                "condition": lambda t: t.get("conscientiousness", 0) > 0.5 and t.get("emotional_stability", 0) > 0.4,
                "type": "opportunity",
                "description": "尽责 + 情绪稳定 → 可靠的执行者，长期发展稳健",
                "probability": 0.85,
            },
            {
                "condition": lambda t: t.get("assertiveness", 0) > 0.5 and t.get("emotional_stability", 0) < 0.2,
                "type": "risk",
                "description": "过于坚持己见 + 情绪敏感 → 可能引发对抗或孤立",
                "probability": 0.60,
            },
        ]

    def predict_destiny(
        self,
        character_profile: dict[str, Any],
        narrative_arc: dict[str, list[dict[str, Any]]] | None = None,
    ) -> dict[str, Any]:
        """预测人物命运

        Args:
            character_profile: CharacterProfiler 输出的人物画像
            narrative_arc: CausalChainAnalyzer 输出的叙事弧线（可选）

        Returns:
            命运预测结果
        """
        predictions: list[dict[str, Any]] = []

        # 1. 叙事模式匹配
        if narrative_arc:
            matched = self._match_narrative_pattern(narrative_arc)
            if matched:
                pattern = self.narrative_patterns[matched]
                predictions.append({
                    "category": "narrative_pattern",
                    "pattern": matched,
                    "example": pattern["example"],
                    "description": pattern["description"],
                    "confidence": 0.7,
                })

        # 2. 性格特质预测
        trait_predictions = self._predict_based_on_traits(character_profile)
        predictions.extend(trait_predictions)

        # 3. 综合评估
        overall = self._overall_assessment(predictions)

        return {
            "character": character_profile.get("name", "未知"),
            "predictions": predictions,
            "overall_outlook": overall["outlook"],
            "overall_confidence": overall["confidence"],
            "summary": overall["summary"],
        }

    def _match_narrative_pattern(
        self, narrative_arc: dict[str, list[dict[str, Any]]]
    ) -> str | None:
        """匹配叙事模式"""
        best_match = None
        best_score = 0.0

        for pattern_name, pattern_data in self.narrative_patterns.items():
            score = self._calculate_pattern_fit(narrative_arc, pattern_data["pattern"])
            if score > best_score:
                best_score = score
                best_match = pattern_name

        return best_match if best_score > 0.3 else None

    def _calculate_pattern_fit(
        self,
        arc: dict[str, list[dict[str, Any]]],
        pattern_stages: list[str],
    ) -> float:
        """计算叙事弧线与模式的匹配度"""
        # 基于事件数量分布与模式阶段数的相似度
        arc_lengths = [len(arc.get(s, [])) for s in arc]
        total = sum(arc_lengths)
        if total == 0:
            return 0.0

        # 检查是否每个阶段都有事件（除了 resolution 可能为空）
        filled_stages = sum(1 for l in arc_lengths[:4] if l > 0)
        return min(filled_stages / 4, 1.0) * 0.5 + 0.2

    def _predict_based_on_traits(
        self, profile: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """基于性格特质预测"""
        traits = profile.get("traits", {})
        predictions = []

        for rule in self.trait_destiny_rules:
            try:
                if rule["condition"](traits):
                    predictions.append({
                        "category": "trait_based",
                        "type": rule["type"],
                        "description": rule["description"],
                        "probability": rule["probability"],
                    })
            except Exception:
                continue

        return predictions

    def _overall_assessment(self, predictions: list[dict[str, Any]]) -> dict[str, Any]:
        """综合评估"""
        if not predictions:
            return {
                "outlook": "neutral",
                "confidence": 0.3,
                "summary": "信息不足，无法做出有信心的预测。",
            }

        risks = [p for p in predictions if p.get("type") == "risk"]
        opportunities = [p for p in predictions if p.get("type") == "opportunity"]

        if len(opportunities) > len(risks):
            outlook = "positive"
            summary = "整体趋势积极向好，有多项有利因素支撑。"
        elif len(risks) > len(opportunities):
            outlook = "negative"
            summary = "面临较多挑战和风险，需要谨慎应对。"
        else:
            outlook = "neutral"
            summary = "机遇与挑战并存，走向取决于关键决策。"

        avg_confidence = (
            sum(p.get("probability", 0.5) for p in predictions) / len(predictions)
        )

        return {
            "outlook": outlook,
            "confidence": round(avg_confidence, 2),
            "summary": summary,
        }
