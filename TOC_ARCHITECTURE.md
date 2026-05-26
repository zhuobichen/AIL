# 数字人文叙事分析 To-C 产品架构设计

## 1. 产品定位与目标用户
- **产品定位**：面向文学爱好者、同人创作者、网文作者及出版行业的“AI 驱动的小说世界观解析与可视化平台”。
- **核心功能**：用户上传小说文件（TXT/EPUB），系统自动提取人物关系、绘制动态社交网络图谱、生成人物性格画像及叙事弧线。
- **商业化（To-C）**：按字数/Token消耗收费（基础免费额度+增值服务），提供高级分析报告（如 CP 互动分析、隐藏剧情预测）下载。

## 2. 系统架构演进 (从单机 CLI 到 Cloud Native)

### 2.1 后端服务 (Backend) - FastAPI
由于底层已重构为纯异步（`asyncio` + `AsyncOpenAI`）并使用 `Pydantic` 进行数据流转，**FastAPI** 是最完美的后端框架。
- **Web 框架**：`FastAPI` (原生支持 Async 和 Pydantic)。
- **任务队列**：由于百万字长文分析需耗时数小时，必须引入异步任务队列。
  - **MVP 阶段**：使用 FastAPI 的 `BackgroundTasks` + 内存/数据库状态记录。
  - **生产阶段**：`Celery` + `Redis` / `RabbitMQ`。
- **持久化存储**：
  - **关系型数据库**：`PostgreSQL` (存储用户信息、任务元数据、订单信息)。
  - **对象存储**：`AWS S3` / 阿里云 OSS (存储用户上传的小说原件及生成的静态 HTML 报告)。
  - **缓存引擎**：现有的 `diskcache` 可平滑迁移至 `Redis`，实现分布式的 LLM 响应缓存。

### 2.2 前端交互 (Frontend) - Next.js / React
- **技术栈**：`Next.js` (React) + `TailwindCSS`。
- **图谱可视化**：
  - `Apache ECharts` 或 `React Flow`，支持动态交互、节点拖拽、力导向布局，替代目前的静态 NetworkX 图。
- **UI/UX 亮点**：
  - **极客风/赛博朋克风** 仪表盘。
  - **实时进度流**：通过 Server-Sent Events (SSE) 或 WebSocket 实时向前端推送“正在分析第 X 章... 发现人物 A 与 B 的互动”。

### 2.3 大模型调度层 (AI Gateway)
- **多模型路由**：除了 DeepSeek，支持用户选择模型（如 Claude 3.5 Sonnet / GPT-4o），不同模型不同定价。
- **Token 计费与并发限流**：使用现有的 `tenacity` 配合 Redis 令牌桶算法，防止恶意刷单并控制 API 成本。

## 3. API 路由设计规划 (MVP)

| 路由路径 | 方法 | 功能描述 |
| :--- | :--- | :--- |
| `/api/v1/auth/login` | POST | 用户登录/注册 |
| `/api/v1/tasks/upload` | POST | 上传书籍文件并创建分析任务，返回 `task_id` |
| `/api/v1/tasks/{task_id}/status` | GET | 轮询任务状态及进度百分比 (可升级为 WebSocket) |
| `/api/v1/tasks/{task_id}/results`| GET | 获取结构化分析结果 (人物列表、关系图谱 JSON) |
| `/api/v1/reports/{task_id}/download` | GET | 下载完整数字人文分析报告 (PDF/HTML) |

## 4. 第一阶段 (MVP) 实施步骤
1. **搭建 FastAPI 框架**：在项目中创建 `api/` 目录，封装现有的 `NarrativePipeline` 为异步 API。
2. **重构本地缓存**：确保 `diskcache` 在并发 Web 请求下不发生锁死，或替换为 Redis。
3. **实现任务状态机**：`PENDING` -> `CHUNKING` -> `EXTRACTING_RELATIONS` -> `PROFILING` -> `COMPLETED`。
4. **搭建前端脚手架**：实现基础的上传文件与可视化进度条。
