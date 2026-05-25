"""情节因果链分析器

分析事件之间的因果关系，构建叙事弧线。
"""

from typing import Any


class CausalChainAnalyzer:
    """因果链分析器

    识别事件之间的因果、目的、转折关系，构建叙事弧线（开端→发展→高潮→结局）。
    """

    def __init__(self):
        # 因果连接词
        self.causal_markers: dict[str, list[str]] = {
            "cause": ["因为", "由于", "鉴于", "基于", "起因", "源于"],
            "effect": ["所以", "因此", "导致", "造成", "结果", "于是"],
            "purpose": ["为了", "以便", "旨在", "目的是"],
            "contrast": ["但是", "然而", "不过", "可是", "反而", "却"],
            "condition": ["如果", "假如", "要是", "一旦"],
        }

    def analyze_causal_chains(
        self, events: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """分析事件之间的因果关系

        Args:
            events: TimelineExtractor 输出的按时间排序的事件列表

        Returns:
            因果链列表，每项包含 event, causes, effects
        """
        causal_chains: list[dict[str, Any]] = []

        for i, event in enumerate(events):
            # 查找原因（前面的事件）
            causes = self._find_causes(event, events[:i])

            # 查找结果（后面的事件）
            effects = self._find_effects(event, events[i + 1 :])

            # 检测转折点
            is_turning_point = self._is_turning_point(event, events, i)

            causal_chains.append({
                "event": event,
                "index": i,
                "causes": causes,
                "effects": effects,
                "is_turning_point": is_turning_point,
            })

        return causal_chains

    def _find_causes(
        self, event: dict[str, Any], previous_events: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """查找事件的原因"""
        causes: list[dict[str, Any]] = []
        text = event.get("raw_text", "")

        # 1. 检测明确因果连接词
        for marker in self.causal_markers["cause"]:
            if marker in text:
                cause_part = text.split(marker)[-1].split("，")[0]
                keywords = cause_part[:20]
                for prev in reversed(previous_events):
                    prev_text = prev.get("raw_text", "")
                    if keywords and keywords in prev_text:
                        causes.append(prev)
                        break

        # 2. 基于人物和时间邻近性推断
        if not causes:
            # 检查最近 3 个事件
            event_chars = set(event.get("characters", []))
            for prev in reversed(previous_events[-3:]):
                prev_chars = set(prev.get("characters", []))
                if event_chars and prev_chars:
                    if event_chars & prev_chars:
                        causes.append(prev)
                        break

        return causes

    def _find_effects(
        self, event: dict[str, Any], later_events: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """查找事件的结果"""
        effects: list[dict[str, Any]] = []
        text = event.get("raw_text", "")

        # 1. 检测"效果"连接词出现在后续事件中
        for marker in self.causal_markers["effect"]:
            if marker in text:
                keywords = text.split(marker)[-1][:20]
                for later in later_events[:3]:
                    later_text = later.get("raw_text", "")
                    if keywords and keywords in later_text:
                        effects.append(later)
                        break

        # 2. 基于人物和时间邻近性推断
        if not effects:
            event_chars = set(event.get("characters", []))
            for later in later_events[:3]:
                later_chars = set(later.get("characters", []))
                if event_chars and later_chars:
                    if event_chars & later_chars:
                        effects.append(later)
                        break

        return effects

    def _is_turning_point(
        self, event: dict[str, Any], all_events: list[dict[str, Any]], index: int
    ) -> bool:
        """判断事件是否为转折点"""
        text = event.get("raw_text", "")

        # 包含转折连接词
        for marker in self.causal_markers["contrast"]:
            if marker in text:
                return True

        # 人物集合突变（新增或减少 > 50% 的人物）
        if index > 0:
            prev_chars = set(all_events[index - 1].get("characters", []))
            curr_chars = set(event.get("characters", []))
            if prev_chars and curr_chars:
                overlap = len(prev_chars & curr_chars)
                total = len(prev_chars | curr_chars)
                if total > 0 and overlap / total < 0.3:
                    return True

        return False

    def build_narrative_arc(
        self, events: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """构建叙事弧线：将事件分为 5 个阶段

        - exposition (开端): 0-20%
        - rising_action (发展): 20-50%
        - climax (高潮): 50-70%
        - falling_action (下降): 70-90%
        - resolution (结局): 90-100%

        Args:
            events: 按时间排序的事件列表

        Returns:
            包含各阶段事件列表的字典
        """
        n = len(events)

        if n == 0:
            return {
                "exposition": [],
                "rising_action": [],
                "climax": [],
                "falling_action": [],
                "resolution": [],
            }

        weights = [0.2, 0.3, 0.2, 0.2, 0.1]
        boundaries = []
        cumulative = 0
        for w in weights:
            cumulative += w
            boundaries.append(int(n * cumulative))

        return {
            "exposition": events[: boundaries[0]],
            "rising_action": events[boundaries[0] : boundaries[1]],
            "climax": events[boundaries[1] : boundaries[2]],
            "falling_action": events[boundaries[2] : boundaries[3]],
            "resolution": events[boundaries[3] :],
        }

    def describe_arc(self, arc: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
        """生成叙事弧线的可读描述

        Args:
            arc: build_narrative_arc 的输出

        Returns:
            阶段名称 -> 描述的字典
        """
        stage_names = {
            "exposition": "开端（背景介绍）",
            "rising_action": "发展（冲突展开）",
            "climax": "高潮（关键转折）",
            "falling_action": "下降（后果展开）",
            "resolution": "结局（问题解决）",
        }

        descriptions = {}
        for stage, events in arc.items():
            name = stage_names.get(stage, stage)
            if not events:
                descriptions[stage] = f"{name}: 暂无事件"
            else:
                chars = set()
                for e in events:
                    chars.update(e.get("characters", []))
                descriptions[stage] = (
                    f"{name}: {len(events)} 个事件，"
                    f"涉及人物 {', '.join(chars) if chars else '无'}"
                )

        return descriptions
