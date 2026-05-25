"""时间线抽取器

从文本中提取时间信息并构建事件时间线。
"""

import re
from datetime import datetime, timedelta
from typing import Any, Optional


class TimelineExtractor:
    """时间线抽取器

    从文本中识别绝对时间和相对时间，提取事件并按时间排序。
    """

    def __init__(self, base_time: Optional[datetime] = None):
        """
        Args:
            base_time: 相对时间的基准时间（默认当前时间）
        """
        self.base_time = base_time or datetime.now()

        # 时间表达式模式
        self.time_patterns: dict[str, Any] = {
            "absolute": [
                r"(\d{4})年(\d{1,2})月(\d{1,2})日",
                r"(\d{4})-(\d{1,2})-(\d{1,2})",
                r"(\d{4})/(\d{1,2})/(\d{1,2})",
                r"(\d{1,2})月(\d{1,2})日",
                r"(\d{4})年",
            ],
            "relative": {
                "昨天": -1,
                "昨天下午": -1,
                "昨天上午": -1,
                "昨晚": -1,
                "今天": 0,
                "今天上午": 0,
                "今天下午": 0,
                "今晚": 0,
                "明天": 1,
                "后天": 2,
                "前天": -2,
                "上周": -7,
                "本周": 0,
                "下周": 7,
                "上个月": -30,
                "下个月": 30,
                "上周五": -3,
                "上上周": -14,
            },
        }

    def set_base_time(self, base_time: datetime):
        """设置相对时间的基准"""
        self.base_time = base_time

    def extract_events(
        self,
        texts: list[str],
        characters: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """从文本列表中提取事件

        Args:
            texts: 文本列表
            characters: 已知人物列表（可选，不传则用简单方法提取）

        Returns:
            按时间排序的事件列表
        """
        events: list[dict[str, Any]] = []

        for text in texts:
            # 提取时间
            time_info = self._extract_time(text)

            # 提取参与者
            participants: list[str] = []
            if characters:
                participants = [c for c in characters if c in text]

            # 提取事件关键词
            description = self._extract_event_description(text)

            events.append({
                "time": time_info,
                "characters": participants,
                "description": description,
                "raw_text": text.strip(),
            })

        # 按时间排序：有时间的排前面，无时间的排后面
        def sort_key(e):
            t = e.get("time")
            if t and t.get("timestamp"):
                return (0, t["timestamp"])
            return (1, datetime.max)

        events.sort(key=sort_key)
        return events

    def _extract_time(self, text: str) -> Optional[dict[str, Any]]:
        """从单段文本中提取时间信息"""
        # 1. 尝试绝对时间
        for pattern in self.time_patterns["absolute"]:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                try:
                    year = month = day = None
                    if len(groups) == 3:
                        year, month, day = map(int, groups)
                    elif len(groups) == 2:
                        month, day = map(int, groups)
                        year = self.base_time.year
                    elif len(groups) == 1:
                        year = int(groups[0])
                        month = day = 1

                    if year and month and day:
                        ts = datetime(year, month, day)
                        return {
                            "type": "absolute",
                            "timestamp": ts,
                            "text": match.group(),
                        }
                except ValueError:
                    continue

        # 2. 尝试相对时间
        for rel_word, offset in self.time_patterns["relative"].items():
            if rel_word in text:
                target_time = self.base_time + timedelta(days=offset)
                return {
                    "type": "relative",
                    "reference": rel_word,
                    "timestamp": target_time,
                    "text": rel_word,
                }

        return None

    def _extract_event_description(self, text: str) -> str:
        """从文本中提取事件描述

        尝试使用 jieba 分词提取关键动词短语，失败则返回文本前段。
        """
        try:
            import jieba
            words = list(jieba.cut(text))
            # 找动词附近的短语
            for i, w in enumerate(words):
                if len(w) >= 2:
                    # 取动词前后各一个词
                    start = max(0, i - 1)
                    end = min(len(words), i + 3)
                    phrase = "".join(words[start:end])
                    if len(phrase) >= 4:
                        return phrase
        except ImportError:
            pass

        # 回退：返回前 80 个字符作为摘要
        return text[:80].replace("\n", " ") + ("..." if len(text) > 80 else "")

    def get_timeline_summary(self, events: list[dict[str, Any]]) -> list[str]:
        """生成可读的时间线摘要

        Args:
            events: extract_events 的输出

        Returns:
            格式化的时间线条目列表
        """
        lines = []
        for i, event in enumerate(events, 1):
            time_info = event.get("time", {})
            if time_info and time_info.get("timestamp"):
                ts = time_info["timestamp"]
                time_str = ts.strftime("%Y年%m月%d日")
            else:
                time_str = "未知时间"

            chars = "、".join(event.get("characters", [])) or "未知人物"
            desc = event.get("description", "")

            lines.append(f"[{i}] {time_str} | {chars} | {desc}")

        return lines
