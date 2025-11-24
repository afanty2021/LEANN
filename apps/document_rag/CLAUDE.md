[根目录](../../CLAUDE.md) > [apps](../) > **document_rag**

# Document RAG - 文档检索增强生成

## 模块职责

Document RAG是LEANN的核心应用示例，展示如何处理和查询各种文档格式（PDF、TXT、MD、DOCX等）。它继承了BaseRAGExample的基础框架，提供了完整的文档索引和语义搜索功能。

## 入口与启动

### 主程序入口
```bash
# 基本用法
python -m apps.document_rag --query "机器学习的主要技术有哪些？"

# 交互模式
python -m apps.document_rag

# 指定数据目录
python -m apps.document_rag --data-dir ./documents --query "总结项目目标"
```

### 类继承结构
```python
class DocumentRAG(BaseRAGExample):
    def __init__(self):
        super().__init__(
            name="Document",
            description="Process and query documents with LEANN",
            default_index_name="test_doc_files"
        )
```

## 对外接口

### 命令行参数
```bash
# 核心参数
--data-dir DIR              # 文档目录（默认：data）
--query "QUESTION"          # 查询问题
--max-items N              # 限制处理的文档数量
--force-rebuild             # 强制重建索引

# 文档特定参数
--file-types .ext .ext      # 指定文件类型过滤
--chunk-size N              # 文本块大小（默认：256）
--chunk-overlap N           # 文本块重叠（默认：128）
--enable-code-chunking      # 启用AST感知代码分块

# 嵌入和LLM参数
--embedding-model MODEL     # 嵌入模型
--embedding-mode MODE       # 嵌入模式
--llm TYPE                  # LLM后端
--llm-model MODEL           # LLM模型
```

### 支持的文档格式
- **PDF**：PyMuPDF、pdfplumber、PyPDF2多重支持
- **文本文件**：TXT、MD、RST等
- **Office文档**：DOCX（通过docx2txt）
- **代码文件**：Python、Java、C#、TypeScript等
- **Jupyter Notebook**：.ipynb文件支持
- **其他**：通过LlamaIndex扩展支持更多格式

## 关键依赖与配置

### 核心依赖
- **llama-index**：文档加载和处理框架
- **llama-index-readers-file**：文件读取器
- **PyMuPDF/pdfplumber/PyPDF2**：PDF解析库
- **astchunk**：AST感知代码分块
- **pathspec**：文件类型过滤

### 配置系统
```python
# 文档读取配置
reader_kwargs = {
    "recursive": True,        # 递归读取子目录
    "encoding": "utf-8",      # 文件编码
    "required_exts": [".pdf", ".txt", ".md"]  # 文件类型过滤
}

# 文本分块配置
node_parser = SentenceSplitter(
    chunk_size=256,           # 文本块大小
    chunk_overlap=128,        # 重叠大小
    separator=" ",           # 句子分隔符
    paragraph_separator="\n\n"  # 段落分隔符
)
```

### 代码感知处理
当启用`--enable-code-chunking`时：
- 使用AST解析器保持代码结构
- 按函数、类、方法进行智能分块
- 支持Python、Java、C#、TypeScript

## 数据模型

### 文档处理流程
```python
# 1. 文档加载
documents = SimpleDirectoryReader(
    args.data_dir,
    recursive=True,
    required_exts=args.file_types
).load_data()

# 2. 文本分块
chunks = create_text_chunks(
    texts,
    chunk_size=args.chunk_size,
    chunk_overlap=args.chunk_overlap,
    enable_code_chunking=args.enable_code_chucking
)

# 3. 索引构建
builder = LeannBuilder(
    backend_name=args.backend_name,
    embedding_model=args.embedding_model,
    # ... 其他参数
)
```

### 元数据管理
```python
# 为每个文本块添加元数据
for i, (text, metadata) in enumerate(chunks):
    builder.add_text(text, metadata={
        "source_file": metadata.get("file_path"),
        "file_type": metadata.get("file_extension"),
        "page_number": metadata.get("page_label"),
        "chunk_index": i,
        "timestamp": datetime.now().isoformat()
    })
```

### 搜索结果处理
```python
# 搜索结果包含：
- content: 匹配的文本内容
- score: 相似度分数
- metadata: 文件路径、页码、文件类型等信息
```

## 测试与质量

### 测试覆盖
- **集成测试**：`tests/test_document_rag.py` - 端到端功能测试
- **文档解析测试**：各种文件格式的解析能力
- **分块测试**：文本分块和代码分块效果
- **搜索测试**：搜索准确性和相关性

### 质量保证
- **多引擎PDF解析**：PyMuPDF → pdfplumber → PyPDF2降级策略
- **编码处理**：自动检测和处理不同文件编码
- **错误恢复**：单个文件解析失败不影响整体处理
- **进度显示**：详细的处理进度和统计信息

### 性能优化
- **并行处理**：支持多线程文档加载
- **增量更新**：只处理新增或修改的文件
- **缓存机制**：嵌入向量计算结果缓存
- **批处理**：高效的批量嵌入计算

## 常见问题 (FAQ)

### Q: PDF解析质量不好怎么办？
A: 系统使用多重降级策略：
1. 首先尝试PyMuPDF（质量最好）
2. 降级到pdfplumber（表格支持好）
3. 最后使用PyPDF2（兼容性最好）

### Q: 如何处理大型文档集合？
A:
```bash
# 分批处理
python -m apps.document_rag --max-items 1000 --data-dir ./large_docs

# 使用文件类型过滤
python -m apps.document_rag --file-types .pdf .txt --chunk-size 512
```

### Q: 代码文件搜索效果不好？
A: 启用代码感知分块：
```bash
python -m apps.document_rag --enable-code-chunking --data-dir ./src
```

### Q: 如何优化搜索准确性？
A:
1. 调整文本块大小：学术论文使用`--chunk-size 1024`
2. 增加重叠：`--chunk-overlap 256`保持上下文
3. 选择合适的嵌入模型：`--embedding-model nomic-embed-text`

### Q: 处理速度太慢？
A:
1. 使用更小的嵌入模型：`--embedding-model facebook/contriever`
2. 减少文本块大小：`--chunk-size 128`
3. 限制文档数量：`--max-items 100`

### Q: 如何处理中文文档？
A: 确保文件编码正确，系统会自动检测UTF-8编码。对于中文文档，推荐：
```bash
python -m apps.document_rag --embedding-model sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

## 使用示例

### 学术论文分析
```bash
# 分析研究论文
python -m apps.document_rag \
  --data-dir ./papers \
  --file-types .pdf \
  --chunk-size 1024 \
  --chunk-overlap 256 \
  --query "这篇论文的主要贡献是什么？"
```

### 代码库搜索
```bash
# 搜索代码库
python -m apps.document_rag \
  --data-dir ./src \
  --enable-code-chunking \
  --chunk-size 512 \
  --query "用户认证是如何实现的？"
```

### 混合文档类型
```bash
# 处理多种文档类型
python -m apps.document_rag \
  --data-dir ./project_docs \
  --file-types .md .txt .pdf .py \
  --query "项目配置和部署流程"
```

## 相关文件清单

### 主要文件
- `apps/document_rag.py` - 主程序实现
- `apps/base_rag_example.py` - 基础RAG框架
- `apps/chunking/__init__.py` - 文本分块工具
- `apps/claude_data/` - Claude数据处理示例
- `apps/chatgpt_data/` - ChatGPT数据处理示例

### 数据读取器
- `apps/email_data/` - 邮件数据读取
- `apps/history_data/` - 历史数据读取
- `apps/imessage_data/` - iMessage数据读取
- `apps/slack_data/` - Slack数据读取（MCP）
- `apps/twitter_data/` - Twitter数据读取（MCP）

### 测试文件
- `tests/test_document_rag.py` - 文档RAG测试
- `data/` - 示例数据目录

## 变更记录 (Changelog)

### 2025-11-24 - 文档RAG分析完成
- ✅ 分析文档处理流程和格式支持
- ✅ 理解文本分块和代码感知机制
- ✢ 梳理元数据管理和搜索结果处理
- ✅ 识别性能优化和质量保证策略
- 📊 **分析覆盖**：核心应用逻辑完整覆盖
- 🔍 **关键特性**：多格式文档支持和AST感知分块

### 扩展建议
- 添加更多文档格式支持（PPTX、XLSX等）
- 优化大文件处理和内存使用
- 增强多语言文档支持
- 改进表格和图像内容的处理

---

*本文档由自适应初始化系统自动生成，基于2025-11-24 17:06:15的项目快照*