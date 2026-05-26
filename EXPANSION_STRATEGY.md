# 数字人文叙事项目 (Digital Humanities Narrative) 扩展战略蓝图

本项目目前已经具备了一个非常坚实的工程底座（Pydantic 数据模型、模块化的 Pipeline、CLI 与 Streamlit 双交互界面）。为了将其打造成一个**行业顶尖的数字人文/AI 辅助文学分析平台**，建议按照以下四大核心维度进行扩展：

---

## 维度一：从“规则驱动”升级为“大模型 (LLM) 驱动” 🧠

目前项目中的关系抽取（`relations.py`）和性格刻画（`profiler.py`）主要依赖**关键词词典**和**正则表达式**。古典文学（如《红楼梦》）往往充满隐喻、反讽和复杂的上下文，规则匹配容易出现漏判或误判。

### 扩展方案：
引入 `LangChain` 或 `Instructor` 库，直接利用 LLM（如 GPT-4o, Claude 3.5, 或本地的 DeepSeek）输出结构化的 Pydantic 模型。

**代码落地示例：**
```python
import instructor
from openai import OpenAI
from src.models import Relation

client = instructor.from_openai(OpenAI(api_key="YOUR_API_KEY"))

def extract_relations_with_llm(text: str) -> list[Relation]:
    # 直接让大模型输出我们定义好的 Pydantic 模型
    relations = client.chat.completions.create(
        model="gpt-4o",
        response_model=list[Relation],
        messages=[
            {"role": "system", "content": "你是一个数字人文专家，请抽取文本中的人物关系。"},
            {"role": "user", "content": text}
        ]
    )
    return relations
```
**优势**：彻底解决隐式关系抽取问题（如：文本没有写“喜欢”，但通过动作描写大模型能推断出“爱慕”关系）。

---

## 维度二：引入图数据库 (Graph Database) 构建真正的大型知识图谱 🕸️

目前我们使用 `NetworkX` 在内存中计算网络。当处理《红楼梦》全本或《三国演义》全本（数千个人物，数万条边）时，内存计算无法持久化，也无法进行高级查询。

### 扩展方案：
引入 **Neo4j** 图数据库，并结合 **GraphRAG** 技术。

**代码落地示例：**
1. 将提取出来的 `Relation` 写入 Neo4j：
```cypher
// Cypher 写入示例
MERGE (a:Character {name: '贾宝玉'})
MERGE (b:Character {name: '林黛玉'})
MERGE (a)-[r:INTERACTS_WITH {type: 'social', sentiment: 0.9, context: '一起看书'}]->(b)
```
2. **高级图谱问答 (GraphRAG)**：
用户提问：“贾母对黛玉的态度是如何随着时间变化的？”
系统可以通过 Neo4j 找出所有连接 `贾母` 和 `林黛玉` 的时间线节点，再交给 LLM 生成精准的答案。

---

## 维度三：引入时间序列与动态网络分析 (Temporal Network) ⏳

文学作品是随时间发展的，人物的关系不是静态的（例如：宝玉和宝钗的关系在第一回和第八十回完全不同）。

### 扩展方案：
现在的项目是将整本书合并处理。我们需要将其**切分为章节 (Chapters)** 或**时间窗口 (Time Windows)**。
1. 重写 `Pipeline.run()`，使其支持输入 `Dict[chapter_name, text]`。
2. 为每一回生成一个 `nx.Graph`。
3. 计算人物中心性随章节的变化曲线（例如：画出王熙凤的“权力指数”随回目增加先上升、后在抄家时暴跌的折线图）。

---

## 维度四：古汉语/文言文专有 NLP 模型的引入 📜

目前项目使用了 `spaCy` 的现代中文模型 (`zh_core_web_sm`)。古典文学和现代汉语在语法上有很大差异，导致专有名词（如官职：巡盐御史、节度使；地点：荣国府、大观园）识别率低。

### 扩展方案：
集成专门针对古汉语训练的模型，例如：
* **[HanLP](https://github.com/hankcs/HanLP)**: 提供极强的古典文学 NER 支持。
* **[Jiagu (甲骨)](https://github.com/ownthink/Jiagu)**: 针对文言文优化的分词和信息抽取工具。
* **HuggingFace 上的古文 BERT 模型**（如 `ethanyt/guwenbert-base`），替换掉我们在 `ner.py` 中的 `transformers` 默认模型。

---

## 维度五：前端与可视化体验的飞跃 🎨

目前的 Streamlit 界面和 CLI 已经很棒，但要作为一个公开发布的产品（SaaS），可以进一步升级。

### 扩展方案：
1. **后端**：使用 `FastAPI` 包装 `Pipeline`，提供 RESTful API。
2. **前端**：使用 `Vue3` 或 `React`。
3. **可视化**：引入 `3D-Force-Graph` (基于 WebGL 的 3D 力导向图)，实现极其震撼的 3D 星空图谱交互效果（用户可以旋转、缩放、点击节点查看人物小传）。
4. **地理空间叙事 (GIS)**：如果分析《三国演义》或《西游记》，可以引入地图可视化（如 Folium 或 ECharts Map），将人物的活动轨迹投射到中国古代地图上。

---

## 总结：演进路线图建议

*   **短期（1-2周）**：将目前的 `NetworkX` 图谱改为支持按“章节”输出动态演化数据，并用 ECharts 画出折线图。
*   **中期（1个月）**：接入 OpenAI / DeepSeek API，替换掉 `relations.py` 中生硬的正则匹配，实现“语义级”的关系和性格抽取。
*   **长期（3个月）**：搭建 FastAPI + Neo4j 后端，实现基于图谱的 RAG（GraphRAG）对话系统，用户可以像和红学专家聊天一样，向系统提问小说里的隐藏线索。