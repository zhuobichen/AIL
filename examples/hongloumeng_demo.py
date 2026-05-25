"""红楼梦示例：从片段还原贾府人物关系

演示完整的数字人文叙事分析流水线。
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline import NarrativePipeline


def main():
    print("=" * 60)
    print("  数字人文叙事分析 —— 《红楼梦》贾府示例")
    print("=" * 60)
    print()

    # 示例文本（模拟从红楼梦片段中提取的内容）
    hongloumeng_texts = [
        "宝玉和黛玉在大观园里散步，宝钗也走了过来。",
        "王熙凤管理着贾府的大小事务，贾母非常信任她。",
        "贾政对宝玉很严厉，经常训斥他不务正业。",
        "林黛玉身体虚弱，经常咳嗽，宝玉很担心她。",
        "薛宝钗性格温和，大家都很喜欢她。",
        "王熙凤和贾琏是夫妻，但她和贾蓉也有暧昧关系。",
        "贾母是贾府的最高权威，所有人都尊敬她。",
        "袭人是宝玉的贴身丫鬟，细心照顾着他的起居。",
        "晴雯性格刚烈，和袭人性格完全不同。",
        "贾宝玉和林黛玉经常在一起看书写诗。",
        "贾宝玉对贾政很害怕，每次见父亲都紧张。",
        "王夫人是贾宝玉的母亲，对儿子非常疼爱。",
        "薛宝钗劝宝玉要好好读书，考取功名。",
        "林黛玉因为宝玉和宝钗的关系而暗自伤心。",
        "贾母决定让宝玉娶宝钗为妻。",
        "林黛玉听到宝玉要娶宝钗的消息后病重。",
        "贾宝玉在婚礼当天发现新娘是宝钗而不是黛玉。",
        "贾府因为朝廷查抄而家道中落。",
        "贾宝玉最终出家做了和尚。",
        "王熙凤因为操劳过度而去世。",
    ]

    # 创建流水线
    pipeline = NarrativePipeline()

    # 执行分析
    results = pipeline.run(hongloumeng_texts, verbose=True)
    print()

    # 打印故事
    print("=" * 60)
    print("  生成的故事")
    print("=" * 60)
    print()
    print(results["story"])
    print()

    # 打印网络分析摘要
    print("=" * 60)
    print("  网络分析")
    print("=" * 60)
    network = results["network_analysis"]
    print(f"  人物数: {network['num_characters']}")
    print(f"  关系数: {network['num_relations']}")
    print(f"  网络密度: {network['density']:.3f}")
    print(f"  主角: {network['main_character']}")
    print(f"  桥梁人物: {network['bridge_character']}")
    print(f"  社区数: {len(network.get('communities', []))}")
    print()

    # 打印命运预测
    print("=" * 60)
    print("  命运预测")
    print("=" * 60)
    for name, destiny in results["destiny_predictions"].items():
        outlook = destiny.get("overall_outlook", "?")
        conf = destiny.get("overall_confidence", 0)
        summary = destiny.get("summary", "")
        print(f"  {name}: {outlook} (信心: {conf:.2f})")
        print(f"    {summary[:80]}")
    print()

    # 生成可视化（需要 pyvis）
    try:
        vis_path = pipeline.visualize_network(
            "hongloumeng_network.html", interactive=True
        )
        print(f"  交互式网络图已保存到: {vis_path}")
    except ImportError:
        print("  (跳过可视化：未安装 pyvis)")


if __name__ == "__main__":
    main()
