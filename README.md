# 纹样知策：基于本体知识图谱与多模态检索的中国传统纹样设计辅助智能体

一个可离线启动的课程期末项目。系统以真实开放纹样数据为底座，提供图鉴检索、RDF 知识图谱、TF-IDF 文化资料检索、颜色特征近邻、PCA/KMeans 分析，以及具有完整工具调用轨迹和可解释评分的确定性设计 Agent。

第二阶段增加统一视觉工作台和“AI 纹样创作室”：配置密钥后可调用 OpenAI Images API；没有密钥时可在本地生成明确标注的程序化 SVG，不会把它说成 AI 模型作品。

> 重要边界：本项目不是文物鉴定工具。《中国传统纹样图鉴》的图像是原创 AI 辅助再设计，不是真实文物照片；文化文字目前属于“数据集描述，尚未独立核验”。颜色聚类不代表历史或文化分类。

## 快速开始

当前已在 Python 3.14.3 验证；代码也以 Python 3.11+ 为目标。

```powershell
python -m pip install -r requirements.txt
python scripts/build_data.py
python -m pytest -q
python -m streamlit run app.py
```

浏览器打开 Streamlit 输出的本地地址（通常为 `http://localhost:8501`）。应用核心能力不依赖在线 API、LLM 或模型下载。

## 已验证数据

- **《中国传统纹样图鉴》**（官方项目名：Wényàng）：`data/patterns.json` 实有 100 条、六类；仓库内容（图片和文字）为 CC BY-NC 4.0，代码和数据结构为 MIT。项目保留原始 ID、文件路径、来源 URL 和许可。本地已从固定提交 `64dccd2` 补齐 100 张正式卡片图，并逐张通过上游 SHA-256 校验。
- **Traditional Pattern Dataset（Hugging Face）**：已核对官方 README、LICENSE、目录 API 和 `dataset_statistics.json`。官方统计为 step 1 1483 图/1483 JSON，step 2 7299 图/1461 JSON，共 8782 图；许可为 CC BY-NC 4.0。因官方映射 CSV 下载超时，未将该来源混入正式数据。`src/data/huggingface_import.py` 提供只接受官方映射 CSV 的手动导入入口。

详细审计见 [docs/data_audit.md](docs/data_audit.md)。原始文件从不被清洗流程覆盖。

## 功能

- 中文图鉴：关键词、类别、寓意、载体组合筛选；详情、缺图状态、来源和许可。
- RDF 本体：7 类核心实体，`hasPeriod`、`hasCategory`、`hasMeaning`、`suitableFor`、`hasVisualFeature`、`relatedTo`、`supportedBySource` 等关系。关系只由已有字段生成。
- 文本知识库：把摘要和寓意拆成可追溯片段，字符 1–3 gram TF-IDF 检索；无证据时固定返回“现有资料不足以确认”。
- 视觉分析：RGB 直方图、RGB 均值/标准差、HSV 均值、主要颜色；欧氏距离近邻；PCA 与 KMeans；轮廓系数。
- 设计 Agent：依次调用需求解析、结构化搜索、知识图谱查询、文化证据检索、视觉近邻、候选排序，展示每一步实际结果。
- 风险提示：时代未知、载体缺失、寓意不足均作为待核验项，未知不计作匹配。
- 证据分层：`dataset_description` 表示数据集自身描述，`external_evidence_status=not_available` 表示当前没有独立外部证据；系统设计建议单独标识，不能作为历史引文。
- AI 纹样创作室：主题、风格、配色、场景和可选纹样参考；可选 OpenAI Images API 生成真实 PNG，或本地几何 SVG 备用。生成图和 sidecar 参数 JSON 保存在 `data/generated/`，不进入正式数据、图谱或文化知识库。

## 推荐算法

默认综合分：

```text
0.55 × 明确条件匹配率 + 0.30 × TF-IDF 证据相关度 + 0.15 × 颜色特征相似度
```

用户可在界面调整权重，系统自动归一化。没有上传参考图时颜色项为 0；缺失字段不能命中。匹配按字段维度计算：时期只检查 `historical_period`，载体只检查 `application_context`，寓意只检查 `cultural_meaning`，视觉条件只检查视觉词。摘要中偶然出现同一字词不会被跨字段误计为命中。

当前 100 张图片全部参与颜色特征分析。默认 KMeans `k=3` 的实测结果为：簇大小 55/22/23，轮廓系数 `0.3162077357`。指标由 `python scripts/build_data.py` 重算并写入 `data/processed/visual_analysis.json`；应用显示实际样本数，不把聚类解释成文化结论。

## 数据准备与手动导入

基础数据已保留在 `data/raw/wenyang/data/`。重新构建：

```powershell
python scripts/build_data.py
```

本工作区已经补齐图片。若需在新环境复现，可运行安全下载器；它固定上游提交、使用临时文件、校验 SHA-256，并支持重复运行时跳过有效文件：

```powershell
python scripts/download_wenyang_images.py
python scripts/build_data.py
```

若逐文件网络通道不稳定，可从官方固定提交归档下载后保留原目录结构。构建脚本每次都从原始 `patterns.json` 重建，不需要删除任何原始数据或旧 CSV。视觉特征缓存使用图片路径、大小和修改时间签名，图片变化时自动失效。

如需导入 Hugging Face 数据，保持官方结构：

```text
data/raw/huggingface/step_2/
├── dataset_image/
├── dataset_json/
└── image_json_mapping.csv
```

调用 `import_stage(Path(...), "step_2")`。导入器按 CSV **每行一张图片** 创建记录；多个图片共享 JSON 时仍是不同图片记录，ID 由来源和完整相对路径生成。缺少映射 CSV 会直接报错，不使用名称相似度猜测映射，也不自动与《中国传统纹样图鉴》的同名项合并。

## AI 创作 Provider

### 阿里云百炼（推荐给中国内地账号）

创作室已接入百炼通义万相的异步图像生成接口。默认使用北京地域
`dashscope.aliyuncs.com`、模型 `wanx2.1-t2i-turbo`，配置位于
`config.json`。程序提交任务后轮询状态，并立即下载临时结果 URL；密钥不会写入生成记录。

在百炼控制台创建 API Key 后，只需在本机项目目录新建
`.streamlit/secrets.toml`（该文件已被 `.gitignore` 排除）：

```toml
DASHSCOPE_API_KEY = "sk-你的完整百炼密钥"
```

也可仅对当前 PowerShell 窗口设置：

```powershell
$env:DASHSCOPE_API_KEY="sk-你的完整百炼密钥"
python -m streamlit run app.py
```

中国内地控制台创建的 Key 使用 `region: "beijing"`。只有在新加坡国际站创建的
Key 才把它改为 `region: "singapore"`；Key 与地域不匹配会鉴权失败。首次调用前，
在百炼控制台确认模型服务可用并开通相应的按量付费/免费额度。项目不会代替账户开通服务，
也不会在测试中发起真实付费调用。

同时保留 OpenAI Images API（`gpt-image-1`）作为可选 Provider。模块接口位于 `src/generation/providers.py`，模型与地域参数位于 `config.json`。未配置任何 API 密钥时，AI 按钮会禁用，但程序化 SVG 和其他页面仍可使用。自动化测试不会调用付费 API，也不宣称已经生成过模型图片。

启用方式（二选一）：

```powershell
$env:OPENAI_API_KEY="你的密钥"
python -m streamlit run app.py
```

或在本机创建 `.streamlit/secrets.toml`：

```toml
OPENAI_API_KEY = "你的密钥"
```

密钥只从环境变量或 Streamlit secrets 读取，不写入项目文件。调用前页面说明服务商可能计费，费用按账户当前价格和额度执行。上传参考图片不会发生；请求只发送用户本次生成的提示词，其中若选择纹样参考，只包含其来源可追踪的文字字段。服务不可用、密钥缺失、超时或响应异常时显示友好错误，不伪造生成结果。

本地“程序化 SVG 备用图”不需要密钥或网络，结果标记为“程序化生成”，使用“下载生成图”保存 SVG。每份输出旁保存参数 JSON，包括 Prompt、风格/配色/场景、Provider 与参考纹样 ID。生成产物不进入正式推荐或文化检索语料。

## 工程结构

```text
app.py                         Streamlit UI
src/data/                      清洗、审计、两来源导入
src/ontology/                  RDF 本体与查询
src/retrieval/                 TF-IDF 知识检索
src/vision/                    颜色特征、近邻、PCA/KMeans
src/agent/                     工具编排与解释排序
data/raw/                      原始下载/审计文件
data/processed/                可复现构建产物
tests/                         与正式数据物理隔离的 fixture 和测试
docs/                          数据审计、架构、演示脚本
```

## 已知限制

- 《中国传统纹样图鉴》的开放汇总 JSON 没有历史时期字段；应用如实显示未知。载体信息扩充前仅从汇总摘要明确词提取（31%），扩充后优先读取固定提交详情页的“常见载体”章节（100%）；这仍是数据集描述，不是外部历史考证。
- 虽已补齐 100 张正式图，但这些图是上游原创 AI 辅助再设计卡片，不是文物照片；图片背景和版式也会影响颜色特征。
- 当前文本库有 900 个来自汇总元数据和官方详情页的真实片段，但尚无独立博物馆或学术文献语料，因此文化回答只能标记为数据集描述，不能作为历史定论。
- `related_patterns` 只从官方详情页明确列出的名称精确映射；没有相似度猜测。
- 第二数据源未正式入库，原因和可恢复步骤见数据审计。

## 测试

测试 fixture 由测试运行时在临时目录创建，不进入正式 CSV 或正式推荐。覆盖字段规范化、缺图、重复 ID、官方一对多映射、RDF 查询、图像特征/损坏图片、文本证据分层/无证据、Agent 完整匹配、未知历史时期、无候选、空数据、图像生成提示词/输入校验/API mock/未配置密钥/API 错误/程序化 SVG/来源参数保存，以及所有页面渲染和主要按钮。

## 署名

纹样资料与预览图：**BLCaptain（爆裂队长NEXT）—《中国传统纹样图鉴》**（官方项目名：Wényàng），<https://wenyang.net>，CC BY-NC 4.0。项目仅用于非商业课程学习与研究。
