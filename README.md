# Quant Platform Knowledge

面向固收量化平台的一期知识库工程，按三层拆分：

- **RAG 知识库**：固收、指标、SDK、策略案例和平台规范。
- **Skills**：策略开发、回测、数据查询的标准工作流。
- **Tools**：`knowledge_search` 供 DeepAgents/Coding Agent 调用；Pilot、回测和 Sandbox 作为后续业务工具接入。

核心原则：**“知道什么”放知识库，“怎么做”放 Skill，“真正执行”放 Tool。** 数据库 600 多张表及关系应进入独立的数据语义层，不放入本知识库。

## 已实现

- Markdown/YAML 结构化知识加载和分类元数据过滤。
- BM25 + 向量的 Hybrid Retrieval，中文、代码标识符均可检索。
- 检索候选重排；默认轻量本地实现，也支持离线 BGE CrossEncoder。
- 内存向量索引和 Qdrant 两种后端。
- FastAPI `/v1/search` 接口、命令行检索和 DeepAgents 工具适配。
- 3 个核心 Skill 与一期示例知识。
- 纯本地单元测试，不依赖数据库和模型下载。

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
quant-kb search "T 和 TL 有什么区别"
quant-kb search "MA 指标如何计算" --category indicator
python -m unittest discover -s tests -v
```

启动 API：

```bash
pip install -e ".[api]"
quant-kb serve --host 0.0.0.0 --port 8000
curl -X POST http://127.0.0.1:8000/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"双均线策略如何回测","top_k":3}'
```

## 内网生产配置

推荐把 BGE 模型提前下载到内网模型目录，并通过环境变量切换实现：

```bash
pip install -e ".[all]"
export KB_VECTOR_BACKEND=qdrant
export KB_QDRANT_URL=http://qdrant:6333
export KB_EMBEDDING_BACKEND=sentence_transformers
export KB_EMBEDDING_MODEL=/models/bge-m3
export KB_RERANKER_BACKEND=cross_encoder
export KB_RERANKER_MODEL=/models/bge-reranker-v2-m3
export KB_MODEL_DEVICE=cpu
quant-kb serve
```

也可用 Docker Compose 启动 API 与 Qdrant：

```bash
docker compose up --build
```

默认 Compose 使用无需模型的 hashing embedding，便于先验证工程链路。生产启用 BGE 时，将模型目录挂载到 `/models` 并修改上述三个后端配置。BGE-M3 的实际向量维度由模型在启动时自动读取，无需手工配置。

## DeepAgents 接入

```python
from quant_kb.deepagents import create_knowledge_search_tool

knowledge_search = create_knowledge_search_tool()
# tools=[knowledge_search] 传给 DeepAgents；三个 Skill 目录通过 Agent 的 skills 配置加载。
```

工具返回 JSON 字符串，包含标题、分类、来源、相关度、片段和元数据。Agent 应先根据任务命中 Skill，再按 Skill 指示调用该工具补充知识。

## 知识目录规范

Markdown 使用 YAML front matter：

```markdown
---
id: fixed-income-duration
title: 久期
category: fixed_income
keywords: [久期, duration, 利率风险]
---
正文……
```

YAML 指标使用结构化字段，参考 [knowledge/indicators/ma.yaml](knowledge/indicators/ma.yaml)。每篇知识必须有唯一 `id`、`title` 和 `category`。新增或修改知识后重启服务，或在部署流程中重新构建索引。

## 生产注意事项

- API 只负责知识检索，不直接执行 SQL、Python 或回测；执行能力应通过有鉴权和资源限制的独立 Tool/Sandbox 暴露。
- API 默认未实现用户鉴权，生产部署必须由平台网关完成身份认证、授权、限流和审计。
- SDK 方法名和示例必须来自已验证文档，Skill 明确禁止 Agent 猜测接口。
- BGE 模型和 Qdrant 镜像需提前完成内网制品审计；禁止运行时访问公网下载模型。
- Qdrant 重建会替换 `KB_QDRANT_COLLECTION` 指定的集合，只为该服务使用独立集合名。
- 当前 BM25 索引在进程内构建。部署多副本时各副本会各自加载关键词索引，Qdrant 数据共享。

## 目录

```text
knowledge/                 示例领域知识
skills/                    DeepAgents Skills
src/quant_kb/              检索、API 和 Agent 工具代码
tests/                     单元测试
```
