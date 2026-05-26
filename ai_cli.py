"""数字人文叙事 AI CLI (Command Line Interface)

一个优雅的、基于命令行的 AI 叙事分析工具。
由大语言模型（模拟）驱动，在终端中提供极其美观的排版、动画与分析报告。
"""

import time
import os
import json
import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.layout import Layout
from rich import print as rprint

from src.pipeline import NarrativePipeline
from src.base.character_dict import get_character_dict, get_character_mapping
from src.network import LLMRelationshipExtractor, RelationshipExtractor
from src.character import LLMCharacterProfiler, CharacterProfiler
from src.narrative import LLMNarrativeGenerator, NarrativeGenerator
from src.models import NarrativeAnalysisResult, NetworkStats, DestinyPrediction

# 加载环境变量
load_dotenv()

app = typer.Typer(help="🤖 数字人文叙事 AI 分析引擎 CLI")
console = Console(record=True)  # 启用 record 以支持导出 HTML/Text

DEFAULT_TEXT = """宝玉和黛玉在大观园里散步，宝钗也走了过来。
王熙凤管理着贾府的大小事务，贾母非常信任她。
贾政对宝玉很严厉，经常训斥他不务正业。
林黛玉身体虚弱，经常咳嗽，宝玉很担心她。
薛宝钗性格温和，大家都很喜欢她。
王熙凤和贾琏是夫妻，但她和贾蓉也有暧昧关系。
贾母是贾府的最高权威，所有人都尊敬她。
袭人是宝玉的贴身丫鬟，细心照顾着他的起居。
贾宝玉和林黛玉经常在一起看书写诗。
贾宝玉对贾政很害怕，每次见父亲都紧张。
薛宝钗劝宝玉要好好读书，考取功名。
林黛玉因为宝玉和宝钗的关系而暗自伤心。
贾母决定让宝玉娶宝钗为妻。
林黛玉听到宝玉要娶宝钗的消息后病重。
贾宝玉在婚礼当天发现新娘是宝钗而不是黛玉。
贾府因为朝廷查抄而家道中落。
贾宝玉最终出家做了和尚。
王熙凤因为操劳过度而去世。"""

def run_analysis(texts: list[str], book_name: str = "hongloumeng") -> NarrativeAnalysisResult:
    """运行流水线并带终端动画"""
    results = None
    
    with Progress(
        SpinnerColumn(spinner_name="dots2"),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        
        # 步骤 1: 初始化
        task1 = progress.add_task(f"[cyan]初始化 AI 分析引擎与知识库 ({book_name})...", total=None)
        
        # 尝试从环境变量获取 DeepSeek API Key
        llm_api_key = os.getenv("DEEPSEEK_API_KEY")
        if llm_api_key:
            progress.console.print("[dim green]✓ 已检测到 DEEPSEEK_API_KEY，将启用大模型增强抽取[/dim green]")
            # 外部实例化并注入依赖
            relation_extractor = LLMRelationshipExtractor(api_key=llm_api_key)
            profiler = LLMCharacterProfiler(api_key=llm_api_key)
            narrative_generator = LLMNarrativeGenerator(api_key=llm_api_key)
        else:
            relation_extractor = RelationshipExtractor()
            profiler = CharacterProfiler()
            narrative_generator = NarrativeGenerator()
            
        pipeline = NarrativePipeline(
            relation_extractor=relation_extractor,
            profiler=profiler,
            narrative_generator=narrative_generator,
            character_names=get_character_dict(book_name),
            convert_traditional=True,
            strict_dict_mode=True,
            explicit_mapping=get_character_mapping(book_name)
        )
        time.sleep(1) # 模拟思考停顿
        progress.update(task1, completed=True, visible=False)
        
        # 步骤 2: 实体抽取
        task2 = progress.add_task("[magenta]正在深度阅读文本并进行实体与关系抽取...", total=None)
        results = pipeline.run(texts, verbose=False)
        time.sleep(1.5)
        progress.update(task2, completed=True, visible=False)
        
    return results

def render_network_table(network_stats: NetworkStats):
    """渲染网络分析表格"""
    table = Table(title="🕸️ 核心人物社交网络指标", show_header=True, header_style="bold cyan")
    table.add_column("人物", style="bold")
    table.add_column("度中心性 (活跃度)", justify="right")
    table.add_column("介数中心性 (桥梁)", justify="right")
    table.add_column("社区归属", justify="center")

    degree = network_stats.degree_centrality
    betweenness = network_stats.betweenness_centrality
    communities = network_stats.communities

    # 找出前 8 名最活跃的人物
    top_chars = sorted(degree.items(), key=lambda x: x[1], reverse=True)[:8]
    
    for char, deg in top_chars:
        bet = betweenness.get(char, 0.0)
        # 查找社区
        comm_id = "-"
        for i, comm in enumerate(communities):
            if char in comm:
                comm_id = f"社区 {i+1}"
                break
                
        table.add_row(
            f"👑 {char}" if char == network_stats.main_character else char,
            f"{deg:.3f}",
            f"{bet:.3f}",
            comm_id
        )
    console.print(table)

def render_destiny_panels(destiny_predictions: dict[str, DestinyPrediction]):
    """渲染命运预测卡片"""
    console.print("\n[bold magenta]🔮 AI 命运与结局推演[/bold magenta]")
    
    # 筛选出高置信度的预测
    high_conf_preds = [
        (name, pred) for name, pred in destiny_predictions.items() 
        if pred.overall_confidence > 0.4
    ]
    # 按置信度排序取前 4 个
    high_conf_preds = sorted(high_conf_preds, key=lambda x: x[1].overall_confidence, reverse=True)[:4]

    for name, pred in high_conf_preds:
        outlook = pred.overall_outlook
        color = "green" if outlook == "positive" else "red" if outlook == "negative" else "yellow"
        icon = "📈" if outlook == "positive" else "📉" if outlook == "negative" else "➖"
        
        content = f"**综合判定**: {icon} {outlook.upper()} (置信度: {pred.overall_confidence:.2f})\n\n"
        content += f"*{pred.summary}*\n\n"
        
        for p in pred.predictions[:2]:
            content += f"- **{p.get('category', '推演')}**: {p.get('description', '')}\n"
            
        panel = Panel(
            Markdown(content),
            title=f"[bold {color}]{name} 的命运简报[/bold {color}]",
            border_style=color,
            expand=False
        )
        console.print(panel)

@app.command()
def demo():
    """运行《红楼梦》大观园内置示例"""
    console.print(Panel.fit(
        "[bold cyan]AI 正在接入《红楼梦》知识库...[/bold cyan]\n"
        "分析目标：从零散的 18 句短文本中，自动重构贾府人物图谱与命运走向。",
        title="🤖 数字人文叙事 AI",
        border_style="cyan"
    ))
    
    paragraphs = [p.strip() for p in DEFAULT_TEXT.split('\n') if p.strip()]
    
    # 运行分析
    results = run_analysis(paragraphs)
    
    # 清屏并展示结果
    console.clear()
    console.rule("[bold green]✅ AI 叙事分析完成[/bold green]")
    
    # 1. 网络指标
    render_network_table(results.network_analysis)
    
    # 2. 命运预测
    render_destiny_panels(results.destiny_predictions)
    
    # 3. 故事重构
    console.print("\n[bold yellow]📖 AI 结构化故事重构[/bold yellow]")
    story_md = results.story
    console.print(Panel(Markdown(story_md), border_style="yellow"))
    
    # 优雅处理：自动导出分析报告
    export_dir = "outputs"
    os.makedirs(export_dir, exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    html_path = os.path.join(export_dir, f"report_{timestamp}.html")
    json_path = os.path.join(export_dir, f"data_{timestamp}.json")
    
    # 导出富文本 HTML（包含所有颜色和表格）
    console.save_html(html_path)
    
    # 导出原始 JSON 数据供下游使用
    with open(json_path, "w", encoding="utf-8") as f:
        # 使用 pydantic 的 model_dump_json
        f.write(results.model_dump_json(indent=2))
        
    console.print(f"\n[bold green]✅ 报告已完整保存，防止终端截断：[/bold green]")
    console.print(f"  📄 网页版阅读报告: [link=file://{os.path.abspath(html_path)}]{html_path}[/link]")
    console.print(f"  💾 结构化数据导出: [link=file://{os.path.abspath(json_path)}]{json_path}[/link]")
    
    console.print("\n[dim]提示: AI CLI 测试完毕。[/dim]")

@app.command()
def analyze(
    file_path: str, 
    output_name: str = typer.Option(None, "--output", "-o", help="自定义输出文件前缀"),
    book: str = typer.Option("hongloumeng", "--book", "-b", help="指定书籍词典 (如 hongloumeng, longzu, sanguo)"),
):
    """分析指定的文本文件"""
    import os
    if not os.path.exists(file_path):
        console.print(f"[bold red]错误：文件 {file_path} 不存在！[/bold red]")
        raise typer.Exit(code=1)
        
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
        
    paragraphs = [p.strip() for p in text.split('\n') if len(p.strip()) > 5]
    console.print(f"[cyan]已加载文本，共 {len(paragraphs)} 个有效段落。使用的知识库词典: {book}[/cyan]")
    
    # 成本估算与安全拦截
    total_chars = len(text)
    estimated_tokens = int(total_chars * 1.5)  # 中文 token 估算
    # 假设价格 (DeepSeek 为例，价格很低，但 GPT-4 较高)
    estimated_cost = (estimated_tokens / 1000000) * 1.0  # 假设 1元/百万 token
    
    if total_chars > 100000:
        console.print(f"\n[bold yellow]⚠️ 警告：检测到超长文本 ({total_chars} 字)！[/bold yellow]")
        console.print(f"  - 预估 Token 消耗：约 {estimated_tokens:,} tokens")
        console.print(f"  - 预估分析耗时：约 {int(total_chars / 50000)} ~ {int(total_chars / 20000)} 分钟")
        console.print("  - [dim]注：系统已开启本地缓存与断点续传，中途断开进度不会丢失。[/dim]")
        
        confirm = typer.confirm("是否确认继续执行深度分析？")
        if not confirm:
            console.print("[red]已取消分析。[/red]")
            raise typer.Exit()
            
    results = run_analysis(paragraphs, book_name=book)
    
    console.clear()
    console.rule(f"[bold green]✅ {os.path.basename(file_path)} 分析完成[/bold green]")
    render_network_table(results.network_analysis)
    render_destiny_panels(results.destiny_predictions)
    
    console.print("\n[bold yellow]📖 AI 结构化故事重构[/bold yellow]")
    console.print(Panel(Markdown(results.story), border_style="yellow"))
    
    # 自动保存
    export_dir = "outputs"
    os.makedirs(export_dir, exist_ok=True)
    
    prefix = output_name if output_name else os.path.splitext(os.path.basename(file_path))[0]
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    html_path = os.path.join(export_dir, f"{prefix}_{timestamp}.html")
    json_path = os.path.join(export_dir, f"{prefix}_{timestamp}.json")
    
    console.save_html(html_path)
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(results.model_dump_json(indent=2))
        
    console.print(f"\n[bold green]✅ 报告已完整保存，防止终端截断：[/bold green]")
    console.print(f"  📄 网页版阅读报告: [link=file://{os.path.abspath(html_path)}]{html_path}[/link]")
    console.print(f"  💾 结构化数据导出: [link=file://{os.path.abspath(json_path)}]{json_path}[/link]")

if __name__ == "__main__":
    app()
