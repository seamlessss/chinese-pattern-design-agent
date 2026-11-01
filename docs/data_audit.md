# 数据审计报告

审计日期：2026-10-20（Asia/Shanghai）  
实际运行环境：Windows，Python 3.14.3

## 1. 《中国传统纹样图鉴》（官方项目名：Wényàng）

- 地址：<https://github.com/dososo/chinese-traditional-patterns>
- 核对提交：`64dccd203a5cde5514eeda1096052c7b9bb69663`
- 文件树：433 项，其中 322 个 blob；`data/patterns.json` 89,076 bytes，`patterns.csv` 25,752 bytes。
- JSON 实际结构：顶层为 100 项数组；每项都有 `id`, `name_cn`, `name_en`, `category`, `summary`, `meaning`, `visual_keywords`, `batch`, `card_image`, `detail_page`, `meta_json`, `image_size`, `image_sha256`, `source_note`。
- 图片树：100 张正式卡片 PNG；仓库另有 8 张 preview JPG。本轮从固定提交归档补齐全部正式图片；原有 8 张 preview 保留。
- 许可：代码和数据结构 MIT；图片、摘要、寓意、详情页及数据文本值 CC BY-NC 4.0，要求署名、仅限非商业用途。
- README 明确：卡片图是原创 AI 辅助生成与再设计，不直接复制具体文物图案。

### 清洗后的实际统计

| 指标 | 实测值 |
|---|---:|
| 正式记录 | 100 |
| 重复统一 ID | 0 |
| 扩充前本地可用图片 | 8 |
| 扩充前缺失图片 | 92 |
| 扩充后本地可用图片 | 100 |
| 扩充后缺失图片 | 0 |
| 分类覆盖 | 100% |
| 寓意覆盖 | 100% |
| 视觉词覆盖 | 100% |
| 历史时期覆盖 | 0% |
| 扩充前应用场景覆盖（仅汇总摘要） | 31% |
| 扩充后应用场景覆盖（官方详情页明确字段） | 100% |
| 官方详情页明确关联覆盖 | 80% |

扩充前，应用场景只从汇总摘要中出现的明确载体词提取，覆盖率 31%。固定提交归档带有每条纹样的官方详情页；扩充后改为优先读取其中“常见载体”章节，覆盖率为 100%。`relatedTo` 只来自详情页“关联纹样”中能精确映射到本数据集名称的条目，80 条记录提供了有效关联，生成 428 条有向关系；没有使用名称相似度推断。历史时期依然没有来源，覆盖率仍为 0%。

当前文本知识库包含 900 个片段：每条记录的汇总摘要、汇总寓意，以及详情页中实际存在的构成、视觉、文化寓意、载体、色彩建议、现代应用和素材说明章节。每个片段保留本地详情路径、数据集 URL 和关联纹样 ID，全部标为数据集自身描述、未获得外部独立核验。

### 图片下载与完整性

- 下载前磁盘：总计 207.03 GiB、可用 112.38 GiB。
- 上游文件树正式图片：100 张、254,243,625 bytes（242.47 MiB），单图 1,430,349–3,005,514 bytes。
- `raw.githubusercontent.com` 逐文件首图三次尝试在 184 秒内超时，未留下 `.part` 文件，也未覆盖原数据。
- GitHub `codeload` 固定提交归档可达，实际下载 255,156,155 bytes。
- 归档 SHA-256：`F6D649C856F1E338FD447FE2CF594E675FF81B2E19DB76C681951443DA727009`；ZIP 完整性测试通过。
- 解出的正式图片总大小与上游树一致；逐条对照 `patterns.json.image_sha256`：100 有效、0 无效、0 失败。
- Pillow 验证：100 张均可解码，尺寸全部为 1086×1448。
- 下载报告：`data/processed/wenyang_image_download.json`。归档和大图目录由 `.gitignore` 排除，避免提交大体积内容。

### 重算后的视觉指标

| 指标 | 实测值 |
|---|---:|
| 实际参与样本 | 100 |
| PCA 维数 | 2 |
| KMeans k | 3 |
| 簇大小 | 55 / 22 / 23 |
| 轮廓系数 | 0.3162077357 |

特征为 RGB 三通道直方图、RGB 均值/标准差和 HSV 均值。缓存保存在 `data/processed/visual_features.npz`，带图片签名；报告保存在 `visual_analysis.json`。这些指标只描述当前卡片图片的颜色统计。

## 2. Traditional Pattern Dataset

- 地址：<https://huggingface.co/datasets/BaoWenwen/Traditional-Pattern-Dataset>
- 已成功取得：目录 API 首页（HTTP 200，234,844 bytes）、README、LICENSE、`dataset_statistics.json`（308,046 bytes）。原始响应保留在 `data/raw/source_audit/`。
- 许可：CC BY-NC 4.0。README 特别说明许可不等于确认所有第三方源图权利。
- 官方统计：8782 图片、2944 JSON 标注。

| 阶段 | 图片 | JSON | 官方映射 |
|---|---:|---:|---|
| step 1 | 1483 | 1483 | 同相对目录、同文件 stem，一对一 |
| step 2 | 7299 | 1461 | 同相对目录、同基础数字 ID，一对多 |

step 2 的 `001.json` 可映射 `001.jpg`、`001_1.jpg`、`001_2.png` 等。完整相对目录和前导零都是身份的一部分；不能跨目录匹配，也不能将共享标注的图片误当成独立 JSON。官方 CSV 列为 `image`, `json`, `match_type`。

### 网络结果与处置

最初沙箱内请求失败为 `WinError 10013`；获准联网后目录与审计文件成功下载。继续下载 `step_1/image_json_mapping.csv` 时连接在 120 秒后超时（`requests.exceptions.ConnectTimeout`），因此本次没有声称已导入 HF 记录，也没有把其官方总数当成本地数据规模。

已实现 `src/data/huggingface_import.py`：必须提供官方 CSV；缺少映射即报错；一行一图，step 2 共享 JSON 的多张图分别保留来源路径；不会按名称自动合并《中国传统纹样图鉴》的记录。待网络稳定时按 README 的目录放置文件即可手动导入。

## 3. 数据隔离与真实性

- `data/raw/`：不被修改的上游文件和审计响应。
- `data/processed/`：仅由构建脚本生成的正式数据。
- 测试 fixture：只由 pytest 写入系统临时目录，来源名为“测试 fixture”，不进入正式统计与应用。
- 正式卡片始终展示来源和许可证；缺图显示占位提示。
- 当前没有独立学术文化资料，所有文化字段均标记“数据集描述，尚未独立核验”。
- 正式表新增 `evidence_type=dataset_description` 与 `external_evidence_status=not_available`；系统设计建议在界面另行标识，不进入证据片段。

## 4. 第二阶段生成数据隔离

- AI/程序化输出目录：`data/generated/`，已从版本控制提交范围排除。
- 每次成功生成保存图片和同 ID 的 JSON sidecar；记录 Provider、模型/程序、尺寸、质量、Prompt、用户参数和参考纹样 ID。
- 生成结果不并入 `data/processed/patterns.csv`、`pattern_graph.ttl` 或 TF-IDF 文本语料。
- 当前环境检查未发现 `OPENAI_API_KEY`，因此本轮没有发起或声称完成真实付费 API 生成。OpenAI Provider 的成功、HTTP 失败、超时和无密钥分支均由 mock 自动化测试验证。
- 程序化 SVG 可离线运行，并在 UI 和元数据中标记为“程序化生成”，不能称为 AI 图像。
