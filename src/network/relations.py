"""人物关系抽取器

从文本中识别并分类人物之间的关系。
"""

from typing import Any


class RelationshipExtractor:
    """人物关系抽取器

    通过关键词模式匹配和共现分析，从文本中抽取人物关系。
    支持层级、协作、冲突、社交四种关系类型。
    """

    def __init__(self):
        # 关系类型定义
        self.relation_patterns: dict[str, dict[str, Any]] = {
            "hierarchical": {
                "patterns": [
                    "是.*的下属", "向.*汇报", "管理", "领导",
                    "负责", "安排", "任命", "上级", "下属",
                ],
                "keywords": ["经理", "主管", "下属", "汇报", "领导", "上级", "安排"],
                "description": "层级关系",
            },
            "collaborative": {
                "patterns": [
                    "和.*一起", "与.*合作", "和.*讨论", "共同",
                    "配合", "协助", "协作",
                ],
                "keywords": ["合作", "讨论", "开会", "一起", "配合", "协同"],
                "description": "协作关系",
            },
            "conflict": {
                "patterns": [
                    "和.*争论", "与.*冲突", "反对", "不同意",
                    "指责", "批评", "质疑", "矛盾",
                ],
                "keywords": ["争论", "冲突", "反对", "不同意", "批评", "指责"],
                "description": "冲突关系",
            },
            "social": {
                "patterns": [
                    "和.*吃饭", "与.*聚会", "和.*聊天", "一起.*玩",
                    "约", "见面", "拜访",
                ],
                "keywords": ["吃饭", "聚会", "聊天", "朋友", "见面", "约"],
                "description": "社交关系",
            },
        }

    def extract_relations(
        self, text: str, characters: list[str]
    ) -> list[dict[str, Any]]:
        """从文本中抽取人物关系

        Args:
            text: 输入文本
            characters: 人物列表

        Returns:
            关系列表，每条包含 source, target, type, context, position
        """
        relations: list[dict[str, Any]] = []
        window_size = 100  # 字符窗口

        # 滑动窗口检测共现
        step = 20
        for i in range(0, max(len(text) - window_size, 1), step):
            window = text[i : i + window_size]

            # 检测窗口中的人物
            chars_in_window = [c for c in characters if c in window]
            if len(chars_in_window) < 2:
                continue

            # 检测关系类型
            relation_type = self._detect_relation_type(window)

            # 为窗口中的每对人物创建关系
            for j in range(len(chars_in_window)):
                for k in range(j + 1, len(chars_in_window)):
                    relations.append({
                        "source": chars_in_window[j],
                        "target": chars_in_window[k],
                        "type": relation_type,
                        "context": window.strip()[:200],
                        "position": i,
                    })

        # 去重：相同人物对只保留首次出现
        seen_pairs: set[tuple[str, str]] = set()
        unique_relations = []
        for rel in relations:
            pair = tuple(sorted([rel["source"], rel["target"]]))
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                unique_relations.append(rel)

        return unique_relations

    def _detect_relation_type(self, text: str) -> str:
        """检测窗口内的主要关系类型

        按关键词匹配数最多确定类型。
        """
        scores: dict[str, int] = {}
        for rel_type, config in self.relation_patterns.items():
            keywords = config.get("keywords", [])
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[rel_type] = score

        if scores:
            return max(scores, key=scores.get)
        return "association"  # 默认：普通关联

    def extract_relations_with_sentiment(
        self, text: str, characters: list[str]
    ) -> list[dict[str, Any]]:
        """抽取关系并附带情感分析

        Args:
            text: 输入文本
            characters: 人物列表

        Returns:
            包含 sentiment 字段的关系列表
        """
        relations = self.extract_relations(text, characters)

        # 简单情感分析
        positive_words = {"满意", "高兴", "成功", "好", "棒", "赞", "感谢", "支持"}
        negative_words = {"不满", "生气", "失败", "差", "糟", "问题", "担心", "反对"}

        for rel in relations:
            context = rel.get("context", "")
            pos_count = sum(1 for w in positive_words if w in context)
            neg_count = sum(1 for w in negative_words if w in context)
            total = pos_count + neg_count
            if total == 0:
                rel["sentiment"] = 0.0  # 中性
            else:
                rel["sentiment"] = (pos_count - neg_count) / total
            # 归一化到 [0, 1]
            rel["sentiment"] = (rel["sentiment"] + 1) / 2

        return relations

    def describe_relation(self, relation_type: str) -> str:
        """获取关系类型的中文描述"""
        for rt, config in self.relation_patterns.items():
            if rt == relation_type:
                return config.get("description", relation_type)
        return "关联关系"
