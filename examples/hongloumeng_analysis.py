"""红楼梦数字人文叙事分析

使用完整的红楼梦文本（120回）测试叙事分析流水线。
"""

import sys
import os
import re
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline import NarrativePipeline
from src.base.character_dict import HONGLOUMENG_CHARACTERS


def load_and_clean(filepath: str) -> str:
    """加载并清理 Gutenberg 红楼梦文本"""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    # 找到正文开始和结束
    start_marker = "*** START OF THE PROJECT GUTENBERG EBOOK"
    end_marker = "*** END OF THE PROJECT GUTENBERG EBOOK"

    start_idx = text.find(start_marker)
    end_idx = text.find(end_marker)

    if start_idx >= 0:
        # 跳到 START 标记之后
        text = text[start_idx + len(start_marker):]
    if end_idx >= 0:
        text = text[:end_idx]

    # 去掉标题行和分隔线
    text = re.sub(r"\*{3,}.*?\*{3,}", "", text)
    text = re.sub(r"-{10,}", "", text)
    text = re.sub(r"\r\n", "\n", text)

    # 压缩多余空行
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def split_chapters(text: str) -> list[dict]:
    """按章回分割文本

    Returns:
        [{"chapter": 1, "title": "甄士隐梦幻识通灵", "text": "..."}, ...]
    """
    # 匹配 "第X回　标题" 格式
    pattern = r"第([一二三四五六七八九十百]+)回[　\s]+([^\n]+)"
    matches = list(re.finditer(pattern, text))

    chapters = []
    chinese_nums = "零一二三四五六七八九十百"

    for i, match in enumerate(matches):
        chapter_title = match.group(2).strip()

        # 确定每回文本范围
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        chapter_text = text[start:end].strip()

        chapters.append({
            "chapter": i + 1,
            "title": chapter_title,
            "text": chapter_text,
            "char_count": len(chapter_text),
        })

    return chapters


def split_into_paragraphs(text: str, min_length: int = 20) -> list[str]:
    """将文本分割为有意义的段落"""
    # 按句号、问号、感叹号分割
    paragraphs = []
    current = ""

    for char in text:
        current += char
        if char in "。？！" and len(current) >= min_length:
            paragraphs.append(current.strip())
            current = ""

    if len(current) >= min_length:
        paragraphs.append(current.strip())

    # 合并太短的段落
    merged = []
    buffer = ""
    for p in paragraphs:
        if len(buffer) + len(p) < 200:
            buffer += p
        else:
            if buffer:
                merged.append(buffer)
            buffer = p
    if buffer:
        merged.append(buffer)

    return merged


def print_analysis_report(results: dict):
    """打印分析报告"""
    print()
    print("=" * 70)
    print("  《红楼梦》数字人文叙事分析报告")
    print("=" * 70)

    # 基本统计
    network = results["network_analysis"]
    print(f"\n[基本统计]:")
    print(f"  文本段数: {results['num_texts']}")
    print(f"  识别人物: {len(results['characters'])} 人")
    print(f"  原始实体: {len(results['raw_characters'])} 个")
    print(f"  关系数量: {len(results['relations'])} 条")
    print(f"  事件数量: {len(results['events'])} 个")
    print(f"  网络密度: {network.get('density', 0):.4f}")

    # 网络分析
    print(f"\n[人物网络分析]:")
    print(f"  主角（度中心性）: {network.get('main_character')}")
    print(f"  桥梁人物（介数中心性）: {network.get('bridge_character')}")
    print(f"  社区数量: {len(network.get('communities', []))}")

    if network.get("communities"):
        for i, comm in enumerate(network.get("communities", [])[:5]):
            members = "、".join(list(comm)[:5])
            print(f"  社区{i+1}: {members}...")

    # 度中心性 Top 10
    deg = network.get("degree_centrality", {})
    if deg:
        top10 = sorted(deg.items(), key=lambda x: x[1], reverse=True)[:10]
        print(f"\n  度中心性 Top 10:")
        for name, score in top10:
            bar = "#" * int(score * 50)
            print(f"    {name}: {score:.4f} {bar}")

    # 人物画像
    print(f"\n[人物画像]:")
    profiles = results["profiles"]
    for p in profiles[:15]:
        name = p["name"]
        role = {"protagonist": "★主角", "supporting": "●配角",
                "minor": "○次要", "background": "·背景"}.get(
            p.get("role_in_story", ""), p.get("role_in_story", "")
        )
        summary = p.get("personality_summary", "")[:80]
        print(f"  {role}: {name} - {summary}")

    # 关系动态
    print(f"\n[关系动态]:")
    dynamics = results.get("relationship_dynamics", {})
    for key, data in list(dynamics.items())[:10]:
        chars = data.get("characters", ("?", "?"))
        rel_type = data.get("relationship_type", "?")
        trend = data.get("trend", "?")
        print(f"  {chars[0]} <-> {chars[1]}: {rel_type} (趋势: {trend})")

    # 叙事弧线
    arc = results.get("narrative_arc", {})
    print(f"\n[叙事弧线]:")
    stage_descs = {
        "exposition": "开端", "rising_action": "发展",
        "climax": "高潮", "falling_action": "下降", "resolution": "结局",
    }
    for stage, events in arc.items():
        name = stage_descs.get(stage, stage)
        print(f"  {name}: {len(events)} 个事件")

    # 故事摘要
    summary = results.get("summary", {})
    print(f"\n[故事摘要]:")
    print(f"  标题: {summary.get('title', '')}")
    setting = summary.get("setting", {})
    print(f"  设定: {setting.get('time_span', '?')} | "
          f"{setting.get('num_characters', 0)}人 | "
          f"{setting.get('num_events', 0)}事件")
    print(f"  主题: {'、'.join(summary.get('themes', []))}")

    # 命运预测（主要人物）
    print(f"\n[命运预测（主要人物）]:")
    destiny = results.get("destiny_predictions", {})
    # destiny is {name: prediction_dict}
    main_chars = []
    for name, pred in destiny.items():
        if isinstance(pred, dict) and pred.get("overall_confidence", 0) > 0.3:
            main_chars.append((name, pred))
    main_chars.sort(key=lambda x: x[1].get("overall_confidence", 0), reverse=True)
    main_chars = main_chars[:8]
    for name, pred in main_chars:
        outlook = pred.get("overall_outlook", "?")
        conf = pred.get("overall_confidence", 0)
        outlook_mark = {"positive": "UP", "negative": "DN", "neutral": "--"}.get(outlook, "??")
        print(f"  [{outlook_mark}] {name}: {outlook} (信心: {conf:.2f})")
        for p in pred.get("predictions", [])[:2]:
            print(f"      {p.get('description', '')[:80]}")


def main():
    print("=" * 70)
    print("  《红楼梦》数字人文叙事分析")
    print("=" * 70)

    # 1. 加载文本
    print("\n[1/4] 加载并清理文本...")
    filepath = os.path.join(os.path.dirname(__file__), "hongloumeng_full.txt")
    text = load_and_clean(filepath)
    cn_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    print(f"  清理后文本: {len(text)} 字符, {cn_chars} 汉字")

    # 2. 按章回分割，取前 N 回
    print("\n[2/4] 按章回分割文本...")
    chapters = split_chapters(text)
    print(f"  共 {len(chapters)} 回")
    for ch in chapters[:5]:
        print(f"    第{ch['chapter']}回: {ch['title']} ({ch['char_count']}字)")
    print(f"    ...")

    # 取前 20 回进行分析（人物关系已经足够丰富）
    CHAPTER_LIMIT = 20
    selected = chapters[:CHAPTER_LIMIT]
    print(f"\n  选取前 {CHAPTER_LIMIT} 回进行分析")

    # 3. 将每回分割为段落后作为输入
    print(f"\n[3/4] 分割段落...")
    all_paragraphs = []
    for ch in selected:
        paras = split_into_paragraphs(ch["text"])
        # 给每段加上回目标记
        tagged = [f"【第{ch['chapter']}回】{p}" for p in paras]
        all_paragraphs.extend(tagged)

    print(f"  共 {len(all_paragraphs)} 个段落")

    # 4. 运行流水线（启用简繁转换 + 人名词典）
    print(f"\n[4/4] 运行分析流水线（词典: {len(HONGLOUMENG_CHARACTERS)} 人名, 简繁转换: 开启）...")
    pipeline = NarrativePipeline(
        character_names=HONGLOUMENG_CHARACTERS,
        convert_traditional=True,
    )
    results = pipeline.run(all_paragraphs, verbose=True)

    # 5. 打印报告
    print_analysis_report(results)

    # 6. 保存完整故事
    story_path = os.path.join(os.path.dirname(__file__), "hongloumeng_story.md")
    with open(story_path, "w", encoding="utf-8") as f:
        f.write(results["story"])
    print(f"\n  完整故事已保存到: {story_path}")

    # 7. 保存完整结果 JSON（排除超长文本字段）
    print(f"\n[保存结果]...")
    save_results = {
        "num_texts": results["num_texts"],
        "num_characters": len(results["characters"]),
        "characters": results["characters"][:100],
        "relations_count": len(results["relations"]),
        "events_count": len(results["events"]),
        "network_analysis": results["network_analysis"],
        "profiles": [
            {k: v for k, v in p.items() if k != "communication_style"}
            for p in results["profiles"][:50]
        ],
        "summary": results["summary"],
    }
    json_path = os.path.join(os.path.dirname(__file__),
                             "hongloumeng_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(save_results, f, ensure_ascii=False, indent=2,
                  default=str)
    print(f"  分析结果已保存到: {json_path}")

    # 8. 生成交互式网络图
    try:
        vis_path = os.path.join(os.path.dirname(__file__),
                                "hongloumeng_network.html")
        net_path = pipeline.visualize_network(vis_path, interactive=True)
        print(f"  交互式网络图已保存到: {net_path}")
    except Exception as e:
        print(f"  (网络图生成跳过: {e})")

    print("\n" + "=" * 70)
    print("  分析完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
