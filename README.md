# 数字人文叙事 AI 分析引擎

> 基于大语言模型的叙事文本分析：人物关系网络抽取与可视化、人物画像与叙事生成。

## 功能

- **人物关系网络**：从文本中抽取人物关系，生成交互式关系图（vis-network）
- **人物画像**：LLM 驱动的角色分析
- **叙事生成**：AI 叙事报告与命运推演

## 入口

| 入口 | 说明 |
|------|------|
| `ai_cli.py` | 终端 CLI（typer + rich，美观排版） |
| `app.py` | Streamlit Web 界面 |
| `examples/` | 示例分析（如名著人物关系网络） |

## 技术栈

Python（Streamlit / NetworkX / Typer）+ 前端 React（Vite + TypeScript）。

## 示例

```bash
python ai_cli.py --help
streamlit run app.py
```
