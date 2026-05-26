"""叙事生成器

基于分析结果生成故事摘要和完整叙事文本。
"""

import json
from typing import Any, Dict

class LLMNarrativeGenerator:
    """基于大模型的叙事生成器"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate_summary(self, analysis_results: dict[str, Any]) -> dict[str, Any]:
        """使用大模型生成高质量的故事摘要"""
        # 提取关键信息给大模型
        network = analysis_results.get("network_analysis", {})
        profiles = analysis_results.get("profiles", [])
        events = analysis_results.get("events", [])
        
        main_chars = [p.get("name") for p in profiles if p.get("role_in_story") in ["protagonist", "supporting"]][:5]
        key_events = [e.get("description", e.get("raw_text", ""))[:100] for e in events[:10]]
        
        prompt = f"""
你是一个数字人文叙事分析专家。请根据以下提取的文本信息，生成一个高度浓缩的故事摘要。

核心人物: {main_chars}
关键事件(节选): {key_events}

请输出 JSON 格式，包含以下字段:
{{
  "title": "你为这个故事起的一个吸引人的标题",
  "time_span": "故事的时间跨度(如果未知写'未知')",
  "themes": ["主题1", "主题2", "主题3"],
  "plot_summary": "100字以内的核心剧情总结"
}}
"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            data = json.loads(response.choices[0].message.content)
            
            # 为了兼容现有接口，映射回旧的数据结构
            return {
                "title": data.get("title", "未命名故事"),
                "setting": {
                    "time_span": data.get("time_span", "未知"),
                    "num_characters": len(profiles),
                    "num_events": len(events),
                    "setting_type": "文学叙事"
                },
                "characters": [{"name": p.get("name"), "role": p.get("role_in_story"), "personality": p.get("personality_summary")} for p in profiles],
                "themes": data.get("themes", []),
                "plot_summary": data.get("plot_summary", "")
            }
        except Exception as e:
            print(f"  [LLM Generator Error] {e}")
            return {"title": "大模型生成失败", "setting": {"time_span": "未知", "num_characters": 0, "num_events": 0}}

    def generate_story(
        self,
        analysis_results: dict[str, Any],
        style: str = "dramatic",
    ) -> str:
        """使用大模型生成完整叙事文本"""
        network = analysis_results.get("network_analysis", {})
        profiles = analysis_results.get("profiles", [])
        events = analysis_results.get("events", [])
        destiny = analysis_results.get("destiny_predictions", {})
        
        main_chars = [p.get("name") for p in profiles if p.get("role_in_story") in ["protagonist", "supporting"]][:8]
        key_events = [e.get("raw_text", "")[:150] for e in events[:20]]
        
        destiny_str = "\n".join([f"{name}: {d.get('overall_outlook')} - {d.get('summary')}" for name, d in destiny.items()][:5])

        prompt = f"""
你是一位顶级的数字人文小说重构专家。请根据以下由 AI 提取的小说碎片信息，重新撰写一篇结构完整、引人入胜的叙事报告。

风格要求: {style} (dramatic: 戏剧化、充满张力; academic: 严肃、结构化分析; concise: 极简摘要)

【核心人物】
{main_chars}

【关键情节碎片】
{key_events}

【AI推演命运结局】
{destiny_str}

请使用 Markdown 格式输出。如果是 dramatic 风格，请像写小说梗概一样跌宕起伏，分章节或幕次(如：第一幕、第二幕)来写，最后给出结局点评。不要输出多余的解释。
"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"大模型生成故事失败: {e}"

class NarrativeGenerator:
    """叙事生成器

    将分析结果（人物、关系、情节）合成为可读的叙事文本。
    支持摘要、完整故事和人物小传三种输出形式。
    """

    # 角色类型说明
    ROLE_DESCRIPTIONS = {
        "protagonist": "主角 —— 故事的核心人物，事件的推动者",
        "supporting": "重要配角 —— 与主角关系密切，推动情节发展",
        "minor": "次要角色 —— 在特定场景中出现",
        "background": "背景角色 —— 偶尔提及",
    }

    # 阶段中文名
    STAGE_NAMES = {
        "exposition": "开端",
        "rising_action": "发展",
        "climax": "高潮",
        "falling_action": "收束",
        "resolution": "结局",
    }

    def generate_summary(self, analysis_results: dict[str, Any]) -> dict[str, Any]:
        """生成故事摘要

        Args:
            analysis_results: 汇总的分析结果，应包含：
                - network_analysis: 网络分析结果
                - profiles: 人物画像列表
                - events: 事件列表
                - causal_chains: 因果链
                - narrative_arc: 叙事弧线

        Returns:
            结构化摘要字典
        """
        return {
            "title": self._generate_title(analysis_results),
            "setting": self._describe_setting(analysis_results),
            "characters": self._describe_characters(
                analysis_results.get("profiles", [])
            ),
            "plot": self._summarize_plot(
                analysis_results.get("events", []),
                analysis_results.get("causal_chains", []),
            ),
            "themes": self._identify_themes(analysis_results),
        }

    def generate_story(
        self,
        analysis_results: dict[str, Any],
        style: str = "dramatic",
    ) -> str:
        """生成完整故事文本

        Args:
            analysis_results: 汇总分析结果
            style: 风格 - "dramatic" 戏剧化 / "concise" 简洁 / "academic" 学术

        Returns:
            故事文本
        """
        styles = {
            "dramatic": self._generate_dramatic,
            "concise": self._generate_concise,
            "academic": self._generate_academic,
        }

        generator = styles.get(style, self._generate_dramatic)
        return generator(analysis_results)

    def generate_character_bio(
        self, profile: dict[str, Any]
    ) -> str:
        """生成单个人物的小传

        Args:
            profile: CharacterProfiler 输出的人物画像

        Returns:
            人物小传文本
        """
        name = profile.get("name", "未知")
        role = profile.get("role_in_story", "background")
        personality = profile.get("personality_summary", "")
        traits = profile.get("traits", {})
        emotions = profile.get("emotions", {})
        style_data = profile.get("communication_style", {})

        lines = [f"## 《{name} 人物小传》", ""]

        # 身份定位
        role_desc = self.ROLE_DESCRIPTIONS.get(role, role)
        lines.append(f"**故事角色**：{role_desc}")
        lines.append("")

        # 性格刻画
        lines.append(f"**性格画像**：{personality}")
        lines.append("")

        # 特质雷达（文本版）
        if traits:
            lines.append("**性格特质分布**：")
            sorted_traits = sorted(traits.items(), key=lambda x: x[1], reverse=True)
            for trait, score in sorted_traits:
                bar = "█" * int(score * 20)
                lines.append(f"  {trait}: {bar} ({score:.2f})")
            lines.append("")

        # 沟通风格
        if style_data:
            lines.append("**沟通风格**：")
            lines.append(f"  - 平均发言长度：{style_data.get('verbosity', 0)} 字")
            lines.append(f"  - 发言频率：{style_data.get('frequency', 0)} 次")
            lines.append(f"  - 主动发起：{style_data.get('initiation', 0)} 次")
            lines.append(f"  - 回应他人：{style_data.get('responsiveness', 0)} 次")
            lines.append("")

        # 情感特征
        if emotions:
            valence = emotions.get("valence", "neutral")
            dominant = emotions.get("dominant", "neutral")
            emotion_names = {
                "positive": "积极", "negative": "消极", "anger": "愤怒",
                "fear": "忧虑", "joy": "喜悦", "sadness": "悲伤",
            }
            lines.append(f"**情感倾向**：整体{emotion_names.get(valence, valence)}，以{emotion_names.get(dominant, dominant)}为主")

        return "\n".join(lines)

    def _generate_title(self, analysis: dict[str, Any]) -> str:
        """生成故事标题"""
        network = analysis.get("network_analysis", {})
        main_char = network.get("main_character", "未知")
        bridge_char = network.get("bridge_character", "")

        if bridge_char and bridge_char != main_char:
            return f"《{main_char}与{bridge_char}——一段数字叙事》"
        return f"《{main_char}的故事——数字叙事重构》"

    def _describe_setting(self, analysis: dict[str, Any]) -> dict[str, Any]:
        """描述故事设定"""
        events = analysis.get("events", [])
        profiles = analysis.get("profiles", [])

        # 时间跨度
        if events:
            times = [e.get("time", {}).get("timestamp") for e in events if e.get("time")]
            times = [t for t in times if t]
            if times:
                time_span = f"{min(times).strftime('%Y-%m-%d')} 至 {max(times).strftime('%Y-%m-%d')}"
            else:
                time_span = "未知"
        else:
            time_span = "未知"

        return {
            "time_span": time_span,
            "num_characters": len(profiles),
            "num_events": len(events),
            "setting_type": (
                "职场叙事" if any("项目" in e.get("raw_text", "") for e in events)
                else "社交叙事"
            ),
        }

    def _describe_characters(self, profiles: list[dict[str, Any]]) -> list[dict[str, str]]:
        """描述所有人物"""
        descriptions = []
        for profile in profiles:
            descriptions.append({
                "name": profile.get("name", "?"),
                "role": profile.get("role_in_story", "unknown"),
                "personality": profile.get("personality_summary", ""),
            })
        return descriptions

    def _summarize_plot(
        self,
        events: list[dict[str, Any]],
        causal_chains: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """总结情节"""
        turning_points = [
            cc for cc in causal_chains if cc.get("is_turning_point")
        ]

        return {
            "total_events": len(events),
            "turning_points": len(turning_points),
            "key_events": [
                cc["event"].get("description", "")
                for cc in turning_points[:3]
            ],
        }

    def _identify_themes(self, analysis: dict[str, Any]) -> list[str]:
        """识别故事主题"""
        themes = []
        events = analysis.get("events", [])
        causal_chains = analysis.get("causal_chains", [])

        all_text = " ".join(e.get("raw_text", "") for e in events)

        theme_keywords = {
            "权力与斗争": ["竞争", "权力", "争夺", "冲突", "斗争"],
            "合作与共赢": ["合作", "共赢", "配合", "协作", "团队"],
            "成长与突破": ["学习", "进步", "突破", "成长", "改进"],
            "情感与羁绊": ["情感", "友谊", "信任", "支持", "关心"],
            "危机与应对": ["危机", "紧急", "问题", "困难", "挑战"],
            "创新与变革": ["创新", "变革", "新方案", "改变", "转型"],
        }

        for theme, keywords in theme_keywords.items():
            if any(kw in all_text for kw in keywords):
                themes.append(theme)

        return themes if themes else ["日常生活"]

    # ---- 风格生成器 ----

    def _generate_dramatic(self, analysis: dict[str, Any]) -> str:
        """戏剧化风格故事"""
        summary = self.generate_summary(analysis)
        arc = analysis.get("narrative_arc", {})
        profiles = analysis.get("profiles", [])
        chains = analysis.get("causal_chains", [])

        parts = []
        parts.append(f"# {summary['title']}")
        parts.append("")
        parts.append(f"> 时间跨度：{summary['setting']['time_span']} | "
                     f"人物：{summary['setting']['num_characters']}人 | "
                     f"事件：{summary['setting']['num_events']}件")
        parts.append("")

        # 按叙事弧线阶段展开
        for stage_key in ["exposition", "rising_action", "climax", "falling_action", "resolution"]:
            stage_events = arc.get(stage_key, [])
            if not stage_events:
                continue

            stage_name = self.STAGE_NAMES.get(stage_key, stage_key)
            parts.append(f"## {stage_name}")
            parts.append("")

            for event in stage_events[:5]:  # 每阶段最多 5 个事件
                chars = "、".join(event.get("characters", [])) or "——"
                desc = event.get("description", "")
                text = event.get("raw_text", "")

                # 找到该事件在因果链中的信息
                is_turning = False
                for cc in chains:
                    if cc.get("event", {}).get("raw_text") == text:
                        is_turning = cc.get("is_turning_point", False)
                        break

                marker = "🔑 " if is_turning else ""
                parts.append(f"{marker}**{chars}**：{desc}")
                if len(text) > 120:
                    text = text[:120] + "..."
                parts.append(f"  > {text}")
                parts.append("")

        # 人物介绍
        parts.append("## 人物谱")
        parts.append("")
        for p in profiles[:10]:
            name = p.get("name", "?")
            role = p.get("role_in_story", "")
            personality = p.get("personality_summary", "")
            role_name = {
                "protagonist": "★ 主角",
                "supporting": "● 重要配角",
                "minor": "○ 配角",
                "background": "· 背景人物",
            }.get(role, role)
            parts.append(f"### {role_name}：{name}")
            parts.append(f"{personality}")
            parts.append("")

        # 主题
        themes = summary.get("themes", [])
        if themes:
            parts.append("## 主题")
            parts.append("")
            parts.append("、".join(f"「{t}」" for t in themes))

        return "\n".join(parts)

    def _generate_concise(self, analysis: dict[str, Any]) -> str:
        """简洁风格故事"""
        summary = self.generate_summary(analysis)
        setting = summary["setting"]
        characters = summary["characters"]
        themes = summary.get("themes", [])

        lines = [
            f"# {summary['title']}",
            "",
            f"**时间**：{setting['time_span']} | "
            f"**人物**：{setting['num_characters']}人 | "
            f"**事件**：{setting['num_events']}件",
            "",
            "## 主要人物",
            "",
        ]

        for c in characters:
            role_name = {"protagonist": "主角", "supporting": "配角",
                         "minor": "次要", "background": "背景"}.get(c["role"], c["role"])
            lines.append(f"- **{c['name']}**（{role_name}）：{c['personality'][:60]}")

        if themes:
            lines.append("")
            lines.append(f"**主题**：{' · '.join(themes)}")

        return "\n".join(lines)

    def _generate_academic(self, analysis: dict[str, Any]) -> str:
        """学术风格报告"""
        summary = self.generate_summary(analysis)
        network = analysis.get("network_analysis", {})

        lines = [
            f"# 数字人文叙事分析报告",
            "",
            f"## 1. 概要",
            f"- 标题：{summary['title']}",
            f"- 时间跨度：{summary['setting']['time_span']}",
            f"- 人物数量：{summary['setting']['num_characters']}",
            f"- 事件数量：{summary['setting']['num_events']}",
            "",
            f"## 2. 网络分析",
            f"- 主角（度中心性）：{network.get('main_character', 'N/A')}",
            f"- 桥梁人物（介数中心性）：{network.get('bridge_character', 'N/A')}",
            f"- 网络密度：{network.get('density', 0):.3f}",
            f"- 边数：{network.get('num_relations', 0)}",
            f"- 社区数：{len(network.get('communities', []))}",
            "",
            f"## 3. 人物分析",
        ]

        for c in summary["characters"]:
            lines.append(f"### 3.1 {c['name']}")
            lines.append(f"- 角色：{self.ROLE_DESCRIPTIONS.get(c['role'], c['role'])}")
            lines.append(f"- 性格：{c['personality']}")
            lines.append("")

        themes = summary.get("themes", [])
        if themes:
            lines.append("## 4. 主题分析")
            lines.append(f"识别主题：{'、'.join(themes)}")

        return "\n".join(lines)
