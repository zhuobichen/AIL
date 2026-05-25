"""中文文本预处理：简繁转换、分词辅助"""

from typing import Optional


class ChineseTextProcessor:
    """中文文本预处理器

    提供简繁转换功能，提升 NLP 模型对繁体中文文本的处理效果。
    """

    def __init__(self):
        self._converter = None
        self._init_attempted = False

    def _ensure_converter(self):
        """延迟加载 OpenCC 转换器"""
        if self._converter is not None:
            return
        if self._init_attempted:
            return
        self._init_attempted = True
        try:
            from opencc import OpenCC
            self._converter = OpenCC("t2s")  # 繁体→简体
        except ImportError:
            pass  # 回退：不做转换

    def traditional_to_simplified(self, text: str) -> str:
        """繁体→简体转换

        Args:
            text: 输入文本（可能含繁体中文）

        Returns:
            简体中文文本
        """
        self._ensure_converter()
        if self._converter is None:
            return text
        try:
            return self._converter.convert(text)
        except Exception:
            return text

    @staticmethod
    def count_chinese_chars(text: str) -> int:
        """统计中文字符数"""
        return sum(1 for c in text if "\u4e00" <= c <= "\u9fff")

    @staticmethod
    def contains_chinese(text: str) -> bool:
        """检查是否包含中文"""
        return any("\u4e00" <= c <= "\u9fff" for c in text)
