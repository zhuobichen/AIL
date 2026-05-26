# 数字人文叙事分析项目 (Digital-Humanities-Narrative) 优化与演进指南

基于对当前代码库的分析，本项目拥有非常清晰的模块化架构（涵盖了从基础 NLP 处理到网络、情节、人物、叙事生成的完整 Pipeline）。但在算法深度、工程化、可视化和交互性方面，还有很大的优化空间。

以下是参考当前 GitHub 顶级开源项目制定的全方位优化指南。

---

## 1. 核心算法升级：从“规则驱动”走向“大模型驱动”

目前项目中的关系抽取、因果分析、情感分析、性格刻画高度依赖**关键词匹配（词典法）**和**正则表达式**。这种方法在复杂文学文本中容易出现泛化能力差、上下文理解缺失的问题。

### 1.1 引入 LLM（大语言模型）进行深度信息抽取
*   **优化思路**：将 `RelationshipExtractor`、`CausalChainAnalyzer`、`CharacterProfiler` 中的硬编码规则替换为 LLM 提示词工程（Prompt Engineering），或使用专门的信息抽取模型。
*   **参考项目**：
    *   [LangChain](https://github.com/langchain-ai/langchain) / [LlamaIndex](https://github.com/run-llama/llama_index)：用于构建基于大模型的文本分块、实体与关系提取 Pipeline。
    *   [PaddleNLP (UIE)](https://github.com/PaddlePaddle/PaddleNLP)：百度开源的通用信息抽取（Universal Information Extraction）框架，专门针对中文实体、关系、事件抽取进行了优化，准确率远超传统正则和词典。

### 1.2 引入 RAG（检索增强生成）重构“叙事生成器”
*   **优化思路**：目前的 `NarrativeGenerator` 是将提取的信息拼接成模板。可以利用 RAG 技术，将提取的图谱和事件存入向量数据库，让 LLM 根据图谱生成更加自然、富有洞察力的学术报告或人物传记。
*   **参考项目**：[Chroma](https://github.com/chroma-core/chroma) 或 [Milvus](https://github.com/milvus-io/milvus)（向量数据库）。

---

## 2. 数据结构与工程化重构

当前项目使用大量的原生 `dict` 来传递数据（如 `results["network_analysis"]`, `results["profiles"]`），这在项目扩展时会导致类型不安全、字段难以追踪。

### 2.1 引入数据验证框架
*   **优化思路**：使用强类型的数据类来定义 `Character`, `Event`, `Relation`, `NarrativeArc` 等核心领域模型。
*   **参考项目**：[Pydantic](https://github.com/pydantic/pydantic)。这是目前 Python 生态最火的数据验证库（FastAPI 的基石），可以让你在 IDE 中获得完美的类型提示，并在数据传递时自动校验。

### 2.2 异步处理与并行化
*   **优化思路**：分析长篇巨著（如120回红楼梦）时，当前的单线程处理会比较慢。可以使用 `asyncio` 或并行计算框架对不同章节的 NER 和关系抽取进行并行处理。
*   **参考项目**：[Ray](https://github.com/ray-project/ray)（分布式计算框架）或 Python 内置的 `concurrent.futures` / `multiprocessing`。

---

## 3. 图谱存储与高级可视化

目前项目使用 `NetworkX` 在内存中建图，并生成简单的 HTML。对于长篇小说，人物网络极其庞大，需要更专业的图数据处理方案。

### 3.1 引入图数据库持久化
*   **优化思路**：将抽取出的人物（Node）和关系、事件（Edge）持久化到图数据库中。这允许你执行复杂的图查询（如：“找出所有同时与贾宝玉和王熙凤有冲突关系的人”）。
*   **参考项目**：[Neo4j](https://github.com/neo4j/neo4j)（业界最著名的图数据库）及其 Python 驱动。可以参考 [GraphRAG](https://github.com/microsoft/graphrag)（微软开源的基于图谱的 RAG 项目），这是目前数字人文和图谱分析最火的方向。

### 3.2 交互式与动态可视化
*   **优化思路**：目前的网络图是静态的。文学作品的魅力在于“时间演化”，可以引入带有时间轴的动态关系图，展示人物关系随章节的演变。
*   **参考项目**：
    *   [PyEcharts](https://github.com/pyecharts/pyecharts)：对 Apache ECharts 的 Python 封装，支持极其丰富且美观的图表（时间轴图、桑基图、关系图）。
    *   [AntV G6](https://github.com/antvis/G6)：阿里开源的专业图可视化引擎。

---

## 4. 打造开箱即用的 Web UI 产品

目前项目通过运行 Python 脚本在终端输出结果。要让更多非技术背景的人文学者使用，需要提供一个友好的图形界面。

### 4.1 构建交互式 Web 应用
*   **优化思路**：提供一个网页，用户可以上传 `.txt` 小说文件，在网页上直接观看动态生成的网络图、人物画像雷达图和叙事弧线。
*   **参考项目**：
    *   [Streamlit](https://github.com/streamlit/streamlit)：只需几行 Python 代码即可将数据脚本转变为可分享的 Web 应用，目前数据科学界最流行的 UI 库。
    *   [Gradio](https://github.com/gradio-app/gradio)：HuggingFace 官方推荐的交互界面库。

### 4.2 提供 RESTful API 接口
*   **优化思路**：将核心 Pipeline 包装为 API 服务，前后端分离，便于未来接入小程序或更复杂的 Web 前端。
*   **参考项目**：[FastAPI](https://github.com/tiangolo/fastapi)。

---

## 5. 建议的演进路线图 (Roadmap)

如果打算开始动手，建议按照以下阶段进行：

*   **Phase 1：基础设施规范化（1周）**
    *   引入 `Pydantic` 重构所有的 `dict` 数据传递，定义清晰的 `Schema`。
    *   完善 `pytest` 单元测试，确保重构不破坏现有逻辑。
*   **Phase 2：产品化与可视化（2周）**
    *   使用 `Streamlit` 编写一个 `app.py`，允许用户上传文本文件并可视化当前所有分析结果。
    *   引入 `PyEcharts` 替换当前的简单 HTML 图谱生成。
*   **Phase 3：拥抱大模型与图谱（1-2个月，核心突破）**
    *   引入 `LangChain` 或 `OpenAI API`（也可对接国产大模型 API），将 `relations.py` 和 `causal.py` 中的正则表达式替换为大模型抽取。
    *   研究并参考微软的 `GraphRAG`，尝试构建真正意义上的“文学知识图谱”。
