"""人物别名识别与消歧"""

import re
from typing import Any


class CharacterAliasResolver:
    """人物别名识别器

    识别同一人物的不同称呼方式，如：
    - 全名 → 称谓（张三 → 张经理）
    - 全名 → 昵称（张三 → 三哥）
    - 全名 → 简称（张三 → 张工）
    """

    def __init__(self):
        # 常见称谓后缀
        self.title_suffixes = [
            "经理", "主管", "总监", "总", "工", "老师",
            "博士", "教授", "主任", "局长", "处长", "科长",
            "哥", "姐", "叔", "姨", "伯", "爷", "奶",
        ]

        # 昵称前缀模式
        self.nickname_prefixes = ["小", "老", "阿"]

        # 姓氏（常见中文姓氏）
        self.common_surnames = set(
            "李王张刘陈杨赵黄周吴徐孙胡朱高林何郭马罗"
            "梁宋郑谢韩唐冯于董萧程曹袁邓许傅沈曾彭"
            "吕苏卢蒋蔡贾丁魏薛叶阎余潘杜戴夏钟汪田"
            "任姜范方石姚谭廖邹熊金陆郝孔白崔康毛邱"
            "秦江史顾侯邵孟龙万段雷钱汤尹易常武乔"
            "贺赖龚文"
        )

    def resolve_aliases(
        self, text: str, entities: list[str]
    ) -> list[dict[str, Any]]:
        """识别并合并别名

        Args:
            text: 原始文本（用于上下文分析）
            entities: 人物实体列表

        Returns:
            别名组列表，每组包含 canonical_name 和 aliases
        """
        if not entities:
            return []

        # 找出全名人物（长度 >= 2）
        full_names = [e for e in entities if len(e) >= 2]
        alias_groups: list[dict[str, Any]] = []

        for entity in full_names:
            if len(entity) < 2:
                continue

            surname = entity[0]
            given_name = entity[1:]

            aliases: list[str] = []
            for other in entities:
                if other == entity:
                    continue
                if other in aliases:
                    continue

                # 1. 姓氏 + 称谓
                if self._is_title_alias(other, surname):
                    aliases.append(other)

                # 2. 昵称模式：小X、老X、阿X
                elif self._is_nickname_alias(other, given_name):
                    aliases.append(other)

                # 3. X哥、X姐、X总 等
                elif self._is_honorific_alias(other, given_name):
                    aliases.append(other)

                # 4. 同姓检测：同一句话中，姓氏相同且距离近
                elif self._is_same_surname_context(text, entity, other):
                    aliases.append(other)

            if aliases:
                alias_groups.append({
                    "canonical_name": entity,
                    "aliases": list(set(aliases)),
                })

        return alias_groups

    def _is_title_alias(self, name: str, surname: str) -> bool:
        """检查是否是"姓氏+称谓"模式的别名"""
        if not name.startswith(surname):
            return False
        rest = name[len(surname):]
        return rest in self.title_suffixes

    def _is_nickname_alias(self, name: str, given_name: str) -> bool:
        """检查是否是昵称模式的别名"""
        if len(name) < 2:
            return False

        # 小X
        if name.startswith("小") and name[1:] == given_name:
            return True
        if name.startswith("小") and name[1:] == given_name[0]:
            return True

        # 老X
        if name.startswith("老") and name[1:] == given_name[-1] if given_name else False:
            return True

        # 阿X
        if name.startswith("阿") and name[1:] == given_name:
            return True

        return False

    def _is_honorific_alias(self, name: str, given_name: str) -> bool:
        """检查是否是尊称模式的别名"""
        # X哥/X姐/X爷/X总
        patterns = [
            f"{given_name}{suffix}"
            for suffix in ["哥", "姐", "爷", "总", "叔", "姨"]
        ]
        return name in patterns

    def _is_same_surname_context(
        self, text: str, full_name: str, other: str
    ) -> bool:
        """基于上下文判断同姓是否指同一人"""
        if not full_name or not other:
            return False
        if full_name[0] != other[0]:
            return False

        # 在文本中查找两者出现位置
        idx_full = text.find(full_name)
        idx_other = text.find(other)

        if idx_full < 0 or idx_other < 0:
            return False

        # 距离在 100 字符以内
        if abs(idx_full - idx_other) > 100:
            return False

        # 检查中间是否有其他同姓名字
        between = text[
            min(idx_full, idx_other) : max(idx_full, idx_other)
        ]
        # 如果在中间没有出现全名且两者间距离近，可能是同一人
        if len(between) < 30:
            return True

        return False

    def merge_aliases(
        self, entities: list[str], alias_groups: list[dict[str, Any]]
    ) -> list[str]:
        """将别名合并为规范名称列表

        Args:
            entities: 原始实体列表
            alias_groups: resolve_aliases 的输出

        Returns:
            合并后的人物名称列表
        """
        # 构建别名→规范名的映射
        alias_map: dict[str, str] = {}
        for group in alias_groups:
            canonical = group["canonical_name"]
            for alias in group["aliases"]:
                alias_map[alias] = canonical

        merged = []
        for entity in entities:
            merged.append(alias_map.get(entity, entity))

        return list(set(merged))

    def resolve_in_text(self, text: str, entities: list[str]) -> dict[str, str]:
        """对文本中的实体做别名解析，返回替换映射

        Args:
            text: 原始文本
            entities: 实体列表

        Returns:
            {别名: 规范名} 的映射字典
        """
        groups = self.resolve_aliases(text, entities)
        mapping: dict[str, str] = {}
        for group in groups:
            canonical = group["canonical_name"]
            for alias in group["aliases"]:
                mapping[alias] = canonical
        return mapping
