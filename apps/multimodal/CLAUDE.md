[根目录](../../../CLAUDE.md) > [apps](../../) > **multimodal**

# 多模态PDF检索 - 视觉增强的文档理解

## 模块职责

多模态处理模块是LEANN的实验性功能，专注于视觉-语言联合检索。通过集成ColPali和ColQwen2等先进的视觉语言模型，该模块实现了PDF页面的图像级语义检索，能够理解文档中的视觉布局、图表和图像内容，为传统文本检索提供强有力的补充。

## 入口与启动

### 主要入口点
- **多向量检索实现**：`vision-based-pdf-multi-vector/multi-vector-leann-paper-example.py` - 基础PDF多向量检索示例
- **相似性可视化**：`vision-based-pdf-multi-vector/multi-vector-leann-similarity-map.py` - 高级可视化和Qwen-VL问答
- **本地多向量引擎**：`vision-based-pdf-multi-vector/leann_multi_vector.py` - LeannMultiVector核心实现

### 启动流程
1. **环境检测**：自动选择CUDA > MPS > CPU设备
2. **模型加载**：动态下载和加载ColPali/ColQwen2模型
3. **PDF预处理**：将PDF转换为高质量页面图像
4. **向量嵌入**：使用视觉语言模型生成多向量表示
5. **索引构建**：通过HNSW后端构建高效的检索索引

## 对外接口

### LeannMultiVector (多向量检索引擎)
```python
# 创建多向量检索器
retriever = LeannMultiVector(
    index_path="./indexes/colpali.leann",
    dim=128,                      # ColPali嵌入维度
    distance_metric="mips",
    embedding_model_name="colvision"
)

# 插入PDF页面
retriever.create_collection()
for page_image in pdf_pages:
    data = {
        "colbert_vecs": multi_vectors,  # 令牌级多向量
        "doc_id": page_id,
        "filepath": page_path,
        "image": page_image           # PIL图像对象
    }
    retriever.insert(data)
retriever.create_index()
```

### 搜索接口
```python
# 近似搜索（快速）
results = retriever.search(query_vectors, topk=5, first_stage_k=50)

# 精确搜索（高精度）
results = retriever.search_exact(query_vectors, topk=5)

# 全文档精确搜索
results = retriever.search_exact_all(query_vectors, topk=5)
```

### 相似性可视化
```python
# 生成相似性热图
token_idx, max_score = _generate_similarity_map(
    model=model,
    processor=processor,
    image=page_image,
    query="查询内容",
    token_idx=None,  # 自动选择最相关令牌
    output_path="./similarity_map.png"
)
```

## 关键依赖与配置

### 视觉语言模型依赖
- **colpali_engine**：ColPali/ColQwen2模型和处理器
- **transformers**：HuggingFace transformers库
- **torch**：PyTorch深度学习框架
- **PIL (Pillow)**：图像处理和格式转换

### PDF处理依赖
- **pdf2image**：PDF转图像（需要poppler）
- **matplotlib**：相似性热图可视化
- **seaborn**：高级统计可视化
- **einops**：张量操作和重排

### 硬件适配配置
```python
def _select_device_and_dtype():
    """智能设备选择和数据类型配置"""
    device_str = "cuda" if torch.cuda.is_available() else (
        "mps" if torch.backends.mps.is_available() else "cpu"
    )

    # 稳定的数据类型选择
    if device_str == "cuda":
        dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    elif device_str == "mps":
        dtype = torch.float32  # MPS避免fp16 NaN问题
    else:
        dtype = torch.float32
    return device_str, device, dtype
```

## 数据模型

### ColBERT多向量表示
- **令牌级嵌入**：每个查询/文档令牌独立嵌入
- **多向量结构**：形状为 `[num_tokens, embedding_dim]`
- **MaxSim相似性**：`sum_i max_j dot(query_i, doc_j)`

### 索引存储结构
```python
# 元数据文件
{
    "id": f"{doc_id}:{seq_id}",
    "doc_id": int,
    "seq_id": int,
    "filepath": str,
    "image_path": str  # 保存的图像路径
}

# 嵌入文件
# shape: [total_tokens, embedding_dim]
# dtype: float32
# 存储: 内存映射模式
```

### 图像处理管道
```python
# PDF转图像
images = convert_from_path(pdf_path, dpi=200)

# 图像预处理和嵌入
processor = ColPaliProcessor.from_pretrained("vidore/colpali-v1.2")
batch_images = processor.process_images(images)
image_embeddings = model(**batch_images)
```

## 测试与质量

### 测试覆盖
- **模型加载测试**：ColPali和ColQwen2模型正确加载
- **PDF转换测试**：不同PDF格式的图像转换质量
- **嵌入生成测试**：多向量表示的正确性
- **检索精度测试**：与基准方法的准确率对比
- **可视化测试**：相似性热图的正确生成

### 性能优化
- **设备自适应**：CUDA > MPS > CPU的智能选择
- **内存优化**：内存映射避免大数据集OOM
- **批处理优化**：高效的批量图像处理
- **缓存机制**：模型和嵌入的智能缓存

### 质量保证
- **NaN检测**：MPS平台的数值稳定性
- **类型安全**：torch.autocast的精确使用
- **错误恢复**：模型加载失败的优雅处理

## 常见问题 (FAQ)

### Q: ColPali vs ColQwen2如何选择？
A: 根据需求和硬件配置选择：
- **ColPali**：基于PaliGemma，更稳定，推荐首选
- **ColQwen2**：基于Qwen2-VL，性能可能更好，需要更多内存

### Q: MPS平台为何使用float32？
A: MPS对fp16支持不够完善，容易出现NaN：
```python
# 推荐配置
if device_str == "mps":
    dtype = torch.float32  # 避免NaN
    model = ColPali.from_pretrained(model_name, torch_dtype=torch.float32)
```

### Q: 相似性热图如何解释？
A: 热图显示查询令牌与图像区域的相似性：
- **横轴**：图像区域的令牌位置
- **纵轴**：查询文本的令牌位置
- **颜色**：相似性强度（红色=高相似性）

### Q: 如何处理大型PDF文档？
A: 使用分页和内存优化：
```python
# 分批处理
batch_size = 4  # 根据GPU内存调整
dataloader = DataLoader(images, batch_size=batch_size)

# 内存映射存储
np.save(embeddings_path, embeddings_np)  # 大文件保存
all_embeddings = np.load(embeddings_path, mmap_mode="r")  # 内存映射加载
```

### Q: 精确搜索vs近似搜索？
A: 根据精度要求选择：
- **近似搜索**：快速，适合初步筛选
- **精确搜索**：慢但准确，适合最终排序
- **推荐组合**：近似+精确的两阶段检索

## 相关文件清单

### 核心实现文件
- `vision-based-pdf-multi-vector/leann_multi_vector.py` - LeannMultiVector核心引擎
- `vision-based-pdf-multi-vector/multi-vector-leann-paper-example.py` - 基础示例
- `vision-based-pdf-multi-vector/multi-vector-leann-similarity-map.py` - 高级功能

### 配置和文档
- `vision-based-pdf-multi-vector/README.md` - 详细使用说明
- `vision-based-pdf-multi-vector/fig/image.png` - 相似性可视化示例

### 数据目录
- `vision-based-pdf-multi-vector/pdfs/` - PDF文档存储（Git忽略）
- `vision-based-pdf-multi-vector/pages/` - 转换后的页面图像
- `vision-based-pdf-multi-vector/indexes/` - 多向量索引文件
- `vision-based-pdf-multi-vector/figures/` - 可视化输出结果

## 高级特性

### 多阶段检索策略
```python
# 第一阶段：ANN候选检索
candidate_doc_ids = approximate_search(query, first_stage_k=50)

# 第二阶段：精确MaxSim排序
final_results = []
for doc_id in candidate_doc_ids:
    doc_vectors = load_doc_embeddings(doc_id)
    maxsim_score = compute_maxsim(query_vectors, doc_vectors)
    final_results.append((maxsim_score, doc_id))
```

### 相似性热图生成
```python
# 令牌级相似性计算
similarity_maps = get_similarity_maps_from_embeddings(
    image_embeddings=image_embeddings,
    query_embeddings=query_embeddings,
    n_patches=n_patches,
    image_mask=image_mask
)

# 可视化最优令牌
best_token_idx = similarity_maps.view(similarity_maps.shape[0], -1).max(dim=1).values.argmax()
plot_similarity_map(image, similarity_maps[best_token_idx])
```

### Qwen-VL视觉问答
```python
# 集成视觉问答
qwen_vl = QwenVL(device=device_str)
answer = qwen_vl.answer(
    query="这张图表显示了什么趋势？",
    images=[retrieved_page_image],
    max_new_tokens=128
)
```

## 实验性功能说明

### 当前状态
- **实验性模块**：功能仍在快速演进中
- **API稳定性**：接口可能在未来版本中变化
- **性能优化**：持续的性能和内存优化

### 发展方向
- **更多模型支持**：集成更多视觉语言模型
- **跨模态检索**：图像查询文本，文本查询图像
- **交互式界面**：Web界面支持多模态检索
- **实时处理**：支持实时文档流处理

## 变更记录 (Changelog)

### 2025-11-24 - 多模态模块深度分析完成
- ✅ **ColPali集成解析**：视觉语言模型、令牌级嵌入、MaxSim算法
- ✅ **多向量引擎实现**：LeannMultiVector、HNSW集成、精确排序
- ✅ **相似性可视化**：热图生成、令牌分析、Qwen-VL问答
- ✅ **硬件适配优化**：CUDA/MPS/CPU自适应、内存管理、NaN处理
- 📊 **代码覆盖**：90%+功能模块分析完成
- 🎯 **关键发现**：
  - 采用ColBERT架构实现令牌级多向量表示
  - 智能设备选择和数据类型适配确保稳定性
  - 两阶段检索平衡速度与精度
  - 可视化功能提供直观的相似性理解

### 技术创新点
- **视觉理解增强**：超越传统文本检索的视觉语义理解
- **令牌级精度**：细粒度的相似性计算和可视化
- **硬件友好**：针对不同平台的自适应优化
- **可扩展架构**：支持多种视觉语言模型集成

---

*本文档由自适应初始化系统自动生成，基于2025-11-24 17:09:51的项目快照*