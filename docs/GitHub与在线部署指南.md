# GitHub 上传与 Streamlit 在线部署指南

## 1. GitHub 仓库是什么？

GitHub 仓库可以理解为项目代码的在线版本库。老师打开仓库链接后，可以查看代码、README、测试和运行说明，也可以下载整个项目。

本项目当前目录中虽然存在 `.git` 文件夹，但执行 `git status` 会提示“not a git repository”，说明该目录不是有效仓库。下面采用“先保留异常目录，再重新初始化”的安全方式处理，不直接删除现有文件。

## 2. 上传前必须检查

不要上传以下内容：

- `.streamlit/secrets.toml`
- `.env`
- 任何真实 API Key
- `data/generated/` 中不准备公开的生成结果
- Python 虚拟环境 `.venv/`
- 缓存目录 `__pycache__/`、`.pytest_cache/`

项目已经通过 `.gitignore` 排除了这些内容。上传前仍建议执行：

```powershell
git status
```

仔细确认待提交文件中没有密钥。

如果曾经把真实密钥写入任何准备提交的文件，应先到对应平台撤销该密钥并重新创建，不能只删除文件中的文字。

## 3. 创建 GitHub 仓库

1. 打开 <https://github.com/> 并登录。
2. 点击右上角 `+`，选择 `New repository`。
3. 仓库名建议填写：

   ```text
   chinese-pattern-design-agent
   ```

4. Description 可填写：

   ```text
   基于知识图谱、多模态检索与图像生成的中国传统纹样设计辅助智能体
   ```

5. 建议选择 `Public`，这样老师无需登录或申请权限即可访问。
6. 不要勾选自动创建 README、`.gitignore` 或 License，因为本地已经存在项目文件。
7. 点击 `Create repository`。

创建后保留网页，后面需要复制仓库地址，例如：

```text
https://github.com/你的用户名/chinese-pattern-design-agent.git
```

## 4. 在本地初始化 Git

在 PowerShell 中进入项目目录：

```powershell
cd "D:\school\study\fa26\设计大数据基础\期末"
```

先把当前无效的 `.git` 文件夹改名保存：

```powershell
Rename-Item .git .git_invalid_backup
```

然后重新初始化：

```powershell
git init -b main
git config user.name "你的 GitHub 用户名"
git config user.email "你的 GitHub 邮箱"
```

建议把备份目录加入本地忽略列表，避免上传：

```powershell
Add-Content .git\info\exclude ".git_invalid_backup/"
```

## 5. 第一次提交并上传

先查看将要提交的文件：

```powershell
git status
```

添加普通代码和文档：

```powershell
git add .
git status
```

再次确认没有 `.streamlit/secrets.toml`、`.env` 或 API Key，然后提交：

```powershell
git commit -m "Complete traditional pattern design agent"
```

连接刚创建的 GitHub 仓库：

```powershell
git remote add origin https://github.com/你的用户名/chinese-pattern-design-agent.git
git push -u origin main
```

GitHub 现在通常不接受账户密码进行命令行推送。浏览器弹出授权窗口时，按提示登录 GitHub；如果要求 Token，需要在 GitHub Settings 中创建 Personal Access Token，并用 Token 代替密码。

## 6. 图片数据的两种上传选择

当前 100 张正式 PNG 约 242 MB，`.gitignore` 默认不上传 `data/raw/wenyang/patterns/`。因此需要根据展示方式选择方案。

### 方案 A：只提交代码，本地演示（最稳妥）

- 保持当前 `.gitignore` 不变。
- GitHub 仓库用于查看代码和文档。
- 老师按 README 运行下载脚本和数据构建脚本。
- 课堂使用本机 Demo，并准备录屏。

优点是仓库小、上传快、最不容易在截止前出问题。老师的要求明确允许本地演示，因此这是当前最稳妥的交付方案。

### 方案 B：在线 Demo，需要提交图片资源

Streamlit Cloud 无法读取你电脑上的图片。若要直接在线展示完整 100 张图片，必须让云端能够获得这些图片。

最直接的方法是强制加入当前图片目录：

```powershell
git add -f data/raw/wenyang/patterns
git commit -m "Add licensed pattern assets for course demo"
git push
```

注意：

- 该目录约 242 MB，第一次上传和云端启动会比较慢。
- 上传前必须保留数据来源和 CC BY-NC 4.0 署名。
- GitHub 单文件不能超过 100 MB；当前图片需要逐个确认均低于此限制。
- 仓库总大小虽然可以承载，但不适合长期频繁更新大图片。

更理想的后续方案是制作一套不覆盖原图的 Web 缩略图，将部署资源控制在约 20—40 MB；在截止时间紧张时，建议优先保证本地演示和录屏稳定。

## 7. 使用 Streamlit Community Cloud 部署

Streamlit Community Cloud 会从 GitHub 拉取项目并运行 `app.py`，最终提供一个任何人可访问的网址。

### 7.1 部署步骤

1. 打开 <https://share.streamlit.io/>。
2. 使用 GitHub 账号登录并授权 Streamlit。
3. 点击 `Create app` 或 `New app`。
4. 选择：
   - Repository：`你的用户名/chinese-pattern-design-agent`
   - Branch：`main`
   - Main file path：`app.py`
5. 点击 `Deploy`。

部署成功后会得到类似地址：

```text
https://你的应用名.streamlit.app
```

把这个链接放入项目说明文档、PPT 最后一页和 README。

### 7.2 配置百炼密钥

不要把密钥上传到 GitHub。在 Streamlit Cloud 应用页面进入：

```text
Settings → Secrets
```

填写：

```toml
DASHSCOPE_API_KEY = "你的百炼 API Key"
```

保存后重新启动应用。

**重要建议：** 公开 Demo 中启用付费图像生成可能被其他访问者重复调用并产生费用。课程展示阶段更安全的做法是：

- 在线 Demo 不配置付费 Key，只开放检索、图谱、视觉分析、Agent 和程序化 SVG；
- 百炼真实生成在本地演示；
- 或展示提前生成并保存的真实结果及录屏。

### 7.3 常见部署问题

#### 页面有数据但图片缺失

原因通常是图片目录没有提交到 GitHub，或者处理后的 CSV 仍保存了本机绝对路径。云端应从原始 JSON 重新构建数据，使图片路径指向云端仓库目录。

#### 应用启动很慢

首次启动需要安装依赖、读取图片并计算视觉特征。等待几分钟后刷新；后续会使用缓存。

#### 提示 API Key 未配置

这是正常的安全降级状态。检索、图谱、视觉分析、Agent 和程序化 SVG 不受影响。如需百炼生成，在 Streamlit Cloud Secrets 中配置 `DASHSCOPE_API_KEY`。

#### 依赖安装失败

检查 `requirements.txt`，并在应用日志中找到第一个安装错误。项目不需要部署数据库、向量数据库或其他独立服务。

## 8. 后续更新代码

每次修改后运行：

```powershell
python -m pytest -q
git status
git add .
git commit -m "说明本次修改内容"
git push
```

Streamlit Cloud 检测到 GitHub 更新后会自动重新部署。

## 9. 提交材料建议

建议最终准备以下文件：

```text
3240102451_刘天伊_项目说明文档.pdf
3240102451_刘天伊_项目展示.pptx
3240102451_刘天伊_项目展示.pdf（备用）
3240102451_刘天伊_Demo录屏.mp4（备用）
代码仓库链接.txt
```

如果来不及完成在线部署，不会违反老师要求。项目说明文档中写明：

```text
代码仓库：https://github.com/你的用户名/chinese-pattern-design-agent
本地运行：python -m streamlit run app.py
```

同时提交代码压缩包或提供 GitHub 下载链接，并在课堂上使用本地 Demo。

## 10. 截止前检查清单

- [ ] GitHub 链接在未登录浏览器中可以访问。
- [ ] README 中包含安装和启动命令。
- [ ] 仓库中没有 API Key。
- [ ] `python -m pytest -q` 全部通过。
- [ ] 本地 Streamlit 可以正常启动。
- [ ] 项目说明文档已导出 PDF。
- [ ] PPT 已同时导出 PDF。
- [ ] Demo 录屏可以正常播放。
- [ ] PPT 和文档中的数据规模、测试数和指标与应用一致。
- [ ] 若提供在线 Demo，使用手机热点或另一台设备测试链接。

