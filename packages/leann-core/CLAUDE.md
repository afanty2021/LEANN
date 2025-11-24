[根目录](../../CLAUDE.md) > [packages](../) > **leann-core**

# LEANN Core - 核心API和插件系统

## 模块职责

LEANN Core是整个项目的核心模块，提供统一的API接口、插件注册系统、嵌入计算管理和CLI工具。它是连接各种后端实现和上层应用的桥梁。

## 入口与启动

### 主要入口点
- **API入口**：`src/leann/api.py` - 核心LeannBuilder、LeannSearcher、LeannChat类
- **CLI入口**：`src/leann/cli.py` - 命令行工具主程序
- **MCP入口**：`src/leann/mcp.py` - Model Context Protocol服务器
- **包初始化**：`src/leann/__init__.py` - 自动发现和注册后端

### 启动流程
1. 包导入时自动修复OpenMP线程问题（macOS ARM64）
2. 自动发现并注册所有可用后端
3. 初始化嵌入计算服务器管理器
4. 设置环境变量和平台特定优化

## 对外接口

### 核心API类

#### LeannBuilder
```python
# 构建索引的主要接口
builder = LeannBuilder(
    backend_name="hnsw",           # 后端选择
    embedding_model="facebook/contriever",
    embedding_mode="sentence-transformers"
)
builder.add_text("文档内容")
builder.build_index("output_path")
```

#### LeannSearcher
```python
# 搜索索引的主要接口
searcher = LeannSearcher("index_path")
results = searcher.search("查询内容", top_k=5)
```

#### LeannChat
```python
# 对话式RAG接口
chat = LeannChat("index_path", llm_config={"type": "openai"})
response = chat.ask("问题", top_k=3)
```

### CLI工具接口
```bash
leann build INDEX_NAME --docs DIRECTORY [OPTIONS]
leann search INDEX_NAME QUERY [OPTIONS]
leann ask INDEX_NAME [OPTIONS]
leann list
leann remove INDEX_NAME
```

### MCP集成接口
- `leann_search` - 语义代码搜索
- `leann_list` - 列出可用索引

## 关键依赖与配置

### 核心依赖
- **numpy**：数值计算和数组操作
- **torch**：深度学习框架，嵌入计算
- **sentence-transformers**：文本嵌入模型
- **llama-index**：文档处理和检索
- **openai**：OpenAI API集成
- **pyzmq**：嵌入服务器通信

### 配置系统
- **环境变量**：自动配置OpenMP、MKL线程数
- **设置解析**：`src/leann/settings.py`处理API密钥和URL
- **平台适配**：macOS ARM64特殊处理，CI环境优化

### 文档处理支持
- **PDF解析**：PyMuPDF、pdfplumber、PyPDF2多重支持
- **代码文件**：AST感知分块，支持Python、Java、C#、TypeScript
- **Notebook**：Jupyter notebook转换支持
- **通用文档**：TXT、MD、DOCX等格式

## 数据模型

### 核心数据结构
- **SearchResult**：搜索结果封装，包含内容、分数、元数据
- **MetadataFilter**：元数据过滤引擎，支持复杂查询条件
- **EmbeddingServerManager**：嵌入计算服务器生命周期管理
- **BackendRegistry**：后端插件注册和发现机制

### 索引存储格式
- **HNSW索引**：.leann文件 + .meta.json元数据
- **DiskANN索引**：支持PQ量化和图分区
- **元数据**：JSON格式存储构建参数和统计信息

## 测试与质量

### 测试覆盖
- **单元测试**：`tests/test_basic.py` - 核心API功能测试
- **集成测试**：`tests/test_*` - 各组件集成测试
- **CI测试**：`tests/test_ci_minimal.py` - 最小化CI测试集

### 质量工具
- **Ruff**：代码格式化和静态检查
- **Pre-commit**：Git提交钩子
- **pytest**：测试框架，支持标记和参数化

### 性能优化
- **嵌入服务器**：独立的ZMQ服务器避免重复模型加载
- **批处理**：高效的嵌入计算批处理
- **内存管理**：智能的内存使用和垃圾回收

## 常见问题 (FAQ)

### Q: 如何选择嵌入模型？
A: 推荐使用`facebook/contriever`作为默认模型，它在效果和速度间有良好平衡。对于特定任务，可以考虑：
- 代码搜索：`microsoft/codebert-base`
- 多语言：`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- 本地部署：`nomic-embed-text`或MLX优化模型

### Q: 嵌入服务器端口冲突怎么办？
A: 系统会自动选择可用端口。如需指定端口，使用：
```python
searcher = LeannSearcher(index_path, embedding_server_port=12345)
```

### Q: 如何处理大量文档的内存问题？
A: 启用重新计算模式：
```python
builder = LeannBuilder(
    backend_name="hnsw",
    is_recompute=True,      # 启用重新计算
    is_compact=True         # 启用压缩存储
)
```

### Q: macOS ARM64特有的问题？
A: 系统自动处理OpenMP线程问题，如遇到性能问题：
```python
# 手动设置环境变量
export PYTORCH_ENABLE_MPS_FALLBACK=1
export TOKENIZERS_PARALLELISM=false
```

## 相关文件清单

### 核心文件
- `src/leann/__init__.py` - 包初始化和后端注册
- `src/leann/api.py` - 核心API类实现
- `src/leann/cli.py` - 命令行工具
- `src/leann/mcp.py` - MCP服务器实现
- `src/leann/interface.py` - 后端接口定义
- `src/leann/registry.py` - 插件注册系统

### 功能模块
- `src/leann/embedding_compute.py` - 嵌入计算实现
- `src/leann/embedding_server_manager.py` - 嵌入服务器管理
- `src/leann/metadata_filter.py` - 元数据过滤
- `src/leann/chat.py` - 对话功能实现
- `src/leann/searcher_base.py` - 搜索器基类
- `src/leann/interactive_utils.py` - 交互会话工具
- `src/leann/settings.py` - 配置和设置解析

### 配置文件
- `pyproject.toml` - 项目配置和依赖
- `README.md` - 模块说明文档

## 变更记录 (Changelog)

### 2025-11-24 - 核心模块分析完成
- ✅ 分析核心API架构和接口设计
- ✅ 理解插件注册和后端发现机制
- ✅ 梳理嵌入计算和服务器管理系统
- ✅ 识别CLI工具和MCP集成功能
- 📊 **代码覆盖**：核心文件90%+分析完成
- 🔍 **关键发现**：良好的模块化设计，清晰的接口抽象

### 待深入分析
- 嵌入计算的细节实现和性能优化
- 元数据过滤引擎的查询语言支持
- MCP协议的具体实现细节
- 错误处理和日志记录机制

---

*本文档由自适应初始化系统自动生成，基于2025-11-24 17:06:15的项目快照*