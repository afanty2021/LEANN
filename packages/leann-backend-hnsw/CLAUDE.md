[根目录](../../CLAUDE.md) > [packages](../) > **leann-backend-hnsw**

# LEANN HNSW Backend - HNSW图索引后端

## 模块职责

LEANN HNSW Backend基于FAISS库实现了HNSW（Hierarchical Navigable Small World）图索引算法。作为默认后端，它提供了卓越的存储效率（通过完全重新计算可达97%存储节省）和优秀的搜索性能。

## 入口与启动

### 后端注册
```python
# 在 src/leann/__init__.py 中自动注册
@register_backend("hnsw")
class HNSWBackend(LeannBackendFactoryInterface):
    @staticmethod
    def builder(**kwargs) -> LeannBackendBuilderInterface:
        return HNSWBuilder(**kwargs)

    @staticmethod
    def searcher(index_path: str, **kwargs) -> LeannBackendSearcherInterface:
        return HNSWSearcher(index_path, **kwargs)
```

### 构建器初始化
```python
builder = HNSWBuilder(
    M=32,                    # 图连接度
    efConstruction=200,      # 构建时的搜索范围
    distance_metric="mips",  # 距离度量
    is_compact=True,         # 启用压缩存储
    is_recompute=True        # 启用重新计算
)
```

## 对外接口

### HNSWBuilder接口
- `build(data, ids, index_path)` - 构建HNSW索引
- 支持的参数：M（连接度）、efConstruction（构建复杂度）、distance_metric（距离度量）
- 自动处理数据类型转换和归一化
- 支持压缩存储和CSR格式转换

### HNSWSearcher接口
- `search(query_embedding, top_k, ef_search)` - 执行相似性搜索
- `search_with_recompute(query_text, top_k, ...)` - 带重新计算的搜索
- `batch_search(query_embeddings, top_k, ...)` - 批量搜索
- `get_index_stats()` - 获取索引统计信息

### 关键算法
- **CSR转换**：`convert_hnsw_graph_to_csr()` - 将FAISS图转换为压缩稀疏行格式
- **嵌入剪枝**：`prune_hnsw_embeddings_inplace()` - 高度保持的嵌入剪枝
- **重新计算搜索**：动态计算搜索路径上的嵌入向量

## 关键依赖与配置

### 核心依赖
- **FAISS**：Facebook AI Similarity Search，HNSW算法实现基础
- **numpy**：数值计算和数组操作
- **scipy.sparse**：稀疏矩阵操作（CSR格式）

### 配置参数
```python
# 构建参数
M = 32                   # 每个节点的最大连接数
efConstruction = 200     # 构建时的候选队列大小
distance_metric = "mips" # 距离度量：mips, l2, cosine

# 存储参数
is_compact = True        # 启用压缩存储
is_recompute = True      # 启用重新计算

# 搜索参数
ef_search = 64           # 搜索时的候选队列大小
search_complexity = 32   # 搜索复杂度
```

### 距离度量支持
- **MIPS**（最大内积搜索）：默认选项，适用于余弦相似度
- **L2**（欧几里得距离）：适用于传统向量空间
- **Cosine**：通过内积实现的余弦相似度

## 数据模型

### 索引存储结构
```
index_path/
├── documents.leann          # 主索引文件
├── documents.leann.meta.json # 元数据文件
└── csr/                     # CSR格式文件（可选）
    ├── graph.csr
    ├── degrees.npy
    └── mapping.npy
```

### 元数据格式
```json
{
    "backend_name": "hnsw",
    "build_params": {
        "M": 32,
        "efConstruction": 200,
        "distance_metric": "mips",
        "is_compact": true,
        "is_recompute": true
    },
    "data_info": {
        "num_vectors": 1000000,
        "dimensions": 768,
        "build_time": 45.2
    }
}
```

### 数据流转换
1. **原始文本** → **嵌入向量** → **FAISS索引**
2. **FAISS索引** → **图结构** → **CSR格式**
3. **搜索查询** → **图遍历** → **动态重新计算**

## 测试与质量

### 测试覆盖
- **后端测试**：`tests/test_basic.py` - HNSW和DiskANN对比测试
- **构建测试**：索引构建和参数验证
- **搜索测试**：准确性和性能基准测试
- **内存测试**：压缩存储和重新计算的内存效率

### 性能基准
- **存储效率**：相比传统向量数据库节省97%存储
- **搜索速度**：毫秒级查询响应时间
- **内存使用**：CSR格式显著减少内存占用
- **扩展性**：支持百万级文档索引

### 质量保证
- **参数验证**：构建时验证参数合理性
- **错误处理**：优雅的降级和详细错误信息
- **兼容性**：与FAISS版本保持兼容

## 常见问题 (FAQ)

### Q: M值如何选择？
A:
- **小数据集**（<100K）：M = 16-32
- **中等数据集**（100K-1M）：M = 32-64
- **大数据集**（>1M）：M = 64-128
更大的M值提供更好的搜索精度但增加内存使用

### Q: efConstruction vs ef_search？
A:
- **efConstruction**：构建时的搜索范围，影响索引质量
- **ef_search**：搜索时的候选队列大小，影响查询速度
通常设置：efConstruction ≥ 4×ef_search

### Q: 什么时候禁用重新计算？
A: 当搜索性能是首要考虑时，可以设置：
```python
builder = HNSWBuilder(is_recompute=False, is_compact=False)
```
这将增加存储需求但提高搜索速度

### Q: 内存不足怎么办？
A:
1. 启用CSR存储：`is_compact=True`
2. 启用重新计算：`is_recompute=True`
3. 减小M值：`M=16`
4. 使用分批构建

### Q: 搜索精度不够？
A:
1. 增加ef_search：`ef_search=128`
2. 增加efConstruction：`efConstruction=400`
3. 增加M值：`M=64`
4. 使用更高质量的嵌入模型

## 相关文件清单

### 核心实现
- `leann_backend_hnsw/__init__.py` - 模块初始化
- `leann_backend_hnsw/hnsw_backend.py` - HNSW后端主要实现
- `leann_backend_hnsw/convert_to_csr.py` - CSR格式转换和剪枝算法

### 配置文件
- `pyproject.toml` - 项目配置和依赖定义

### 测试文件
- `tests/test_basic.py` - 后端功能测试
- `benchmarks/` - 性能基准测试

## 变更记录 (Changelog)

### 2025-11-24 - HNSW后端分析完成
- ✅ 分析HNSW算法实现和参数配置
- ✅ 理解CSR格式转换和嵌入剪枝机制
- ✅ 梳理存储优化和重新计算策略
- ✅ 识别性能调优的关键参数
- 📊 **分析覆盖**：核心实现文件完整分析
- 🔍 **技术亮点**：高度保持剪枝算法和动态重新计算

### 性能优化建议
- 对于实时应用，考虑预计算热点查询
- 大规模部署时启用分区和并行构建
- 监控内存使用，适当调整批处理大小

---

*本文档由自适应初始化系统自动生成，基于2025-11-24 17:06:15的项目快照*