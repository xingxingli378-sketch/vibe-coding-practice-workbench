# Vibe Coding 本地练习工作台

给零基础学习者使用的本地网页：通过 Qwen Code 读取题目、修改实际文件、根据检查反馈继续修复。包含六道自编练习、只读文件预览、独立对话、公开检查、进阶边界检查和两小时模拟计时。

**这是非官方教学项目。**参照[上海创智学院公开形式说明](https://www.sii.edu.cn/2026/0930/c24a1242/page.htm)设计；正式三题内容未公布，不能把本项目当作正式试题、押题或评分系统。图像素材为合成示意图，不代表真实气象 OCR 能力。

## 先看哪里

|你的目标|阅读入口|
|---|---|
|把项目跑起来|[安装与启动](docs/01-install-and-run.md)|
|理解它是如何创建的|[从零创建完整流程](docs/02-build-from-zero.md)|
|学习不会代码时如何操作 Qwen|[新手调试行为模板](docs/03-beginner-debugging.md)|
|自己再编几道题|[出题与验收](docs/04-author-tasks.md)|
|排查报错和卡住|[故障排查](docs/05-troubleshooting.md)|
|了解这次实际经历了什么|[项目演进记录](docs/06-project-history.md)|
|上传到自己的 GitHub|[GitHub 发布流程](docs/07-github-publishing.md)|

## 快速开始：Windows CMD

需要 Python 3.10+、Node.js 22+ 和 npm。Git 仅用于克隆和发布。先下载或克隆本项目，打开项目目录中的 CMD。

```cmd
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
npm install
.venv\Scripts\python.exe prepare.py
.venv\Scripts\python.exe launch_qwen.py
```

最后一条会打开 Qwen 自己的配置流程。只在 Qwen 官方流程中设置账号，不把密钥填进网页或源码。完成后退出 Qwen，再运行：

```cmd
.venv\Scripts\python.exe server.py --open
```

打开 <http://127.0.0.1:8765/>。保持启动窗口开启；关闭窗口停止服务。也可以依次双击 `setup.cmd`、`login.cmd`、`start.cmd`。工作台没有账号也能查看文件和运行检查，发送编程要求则需要可用的 Qwen 账号。

项目使用 Pillow 12.3.0、Qwen Code 0.25.0，固定的是本次整理时的依赖版本。更新依赖前请查看对应官方文档并重新验收，不假定新版本的命令或事件格式完全一致。

## 六道练习

|题号|内容|建议用途|
|---|---|---|
|01|图片格式、尺寸、GIF 首帧和不确定标记|基础读取与结构化|
|02|站点温度清洗|有效/无效输入、输入保护|
|03|三题成绩汇总|校验、舍入和等级边界|
|04|气象示意图批量结构化|内容分类、离线可见时间、批量容错|
|05|多来源观测合并与日统计|CSV、单位换算、去重、拒绝原因|
|06|预报核验与可读报告|配对、误差、事件指标、JSON/HTML|

01–03 是基础练习。04–06 可作为一套两小时自编模拟，建议分配 45/40/35 分钟。每题有十个公开检查点；04 另有五项加练，05/06 各六项。加练是教学检查，不是学校隐藏评分。

## 文件与对话如何保存

```text
task_bank/        原始题面、素材、辅助模块和待实现代码（进入 Git）
tasks/            运行 prepare.py 后生成的实际作答目录（不进入 Git）
practice-state.json  本地对话、检查结果、计时（不进入 Git）
node_modules/     本机 npm 依赖（不进入 Git）
```

`prepare.py` 只补齐缺失文件，已有作答不被覆盖。切题不会删除文件；清空对话只清当前题的对话。需要重练时先备份自己的题目目录，再手动恢复对应 `task_bank` 模板。

## 验证项目本身

```cmd
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe tests\author_qa.py
```

第一条验证工作台基础设施和初始题库；第二条在独立副本验证进阶题的检查与参考实现一致，不修改你的作答。`tests/author_qa.py` 包含验题参考实现，建议做题前不阅读。CI 不调用模型，不需要模型密钥。

## 使用范围

服务只监听 `127.0.0.1`，没有公网登录、多用户权限或容器隔离。每题的 `QWEN.md` 是助手指引，不是操作系统权限边界。只放练习材料，不向公网部署，不在这里存个人敏感文件。

Qwen 使用 `auto-edit`，未启用自动批准所有工具。当前环境如果无法运行 shell，用页面检查按钮；不要把这个限制推断成所有 Qwen 环境都缺少命令工具。

## 主要官方参考

- [学院作答形式说明](https://www.sii.edu.cn/2026/0930/c24a1242/page.htm)
- [Qwen Code 安装说明](https://github.com/QwenLM/qwen-code/blob/main/scripts/installation/INSTALLATION_GUIDE.md)
- [Qwen Code Headless 模式](https://github.com/QwenLM/qwen-code/blob/main/docs/users/features/headless.md)
- [GitHub：上传已有本地项目](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github)
