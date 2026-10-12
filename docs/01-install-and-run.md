# 安装、配置、启动与重启

## 1. 准备软件

安装 Python 3.10 或以上、Node.js 22 或以上。使用官方来源：<https://www.python.org/downloads/>、<https://nodejs.org/>。安装时按其官方界面设置 PATH。打开新的 CMD 检查：

```cmd
python --version
node --version
npm --version
```

若提示“不是内部或外部命令”，先解决软件安装和 PATH，不修改项目代码。

## 2. 获取源码

可以从 GitHub 下载 ZIP 后解压，或用 `git clone`。进入有 `server.py`、`package.json`、`requirements.txt` 的目录。所有下面的命令都从这个目录执行；路径有空格时加双引号。

```cmd
cd /d "你解压项目的实际路径"
```

## 3. 安装项目依赖

```cmd
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
npm install
.venv\Scripts\python.exe prepare.py
```

`.venv` 是项目自己的 Python 环境；`node_modules` 是 npm 安装的 Qwen；`tasks` 是生成的六题作答目录。不要上传这三类运行目录。

`prepare.py` 可重复运行，它只复制缺失文件，不重置已经完成的题。不要用“重新生成题库”作为修复安装问题的默认手段。

## 4. 配置 Qwen

```cmd
.venv\Scripts\python.exe launch_qwen.py
```

按 Qwen 官方界面选择服务并完成账号配置。项目不预设你的模型服务，不提供密钥；可能发生的调用费用由你选择的服务决定。不要把密钥贴进工作台聊天、README 或 Git 提交。

配置完成后退出这个交互界面。在网页里“已安装”只表示可找到 CLI，不表示账号调用已成功。第一条只读请求成功后，才能确认此次调用可用。

## 5. 启动网页

```cmd
.venv\Scripts\python.exe server.py --open
```

浏览器打开 <http://127.0.0.1:8765/>。窗口保持运行；若浏览器没有自动打开，手动粘贴网址。初始题的部分检查失败、进阶题显示未实现，都属于正常作答起点。

开场请求：

> 请读取当前题的 README、项目指引和代码。我是零基础，请解释我要给程序什么、应该得到什么、需要提交什么，先不要修改。

## 6. 重启

1. 先等当前助手结束，或点击“停止助手”。
2. 在启动服务的 CMD 窗口按 Ctrl+C。
3. 重新运行同一条启动命令。
4. 在浏览器按 Ctrl+F5。

不需要删除 `tasks` 或 `practice-state.json`。如果提示端口占用，先确认旧工作台是否仍运行，不随意停止其他程序。

## Linux/macOS

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm install
.venv/bin/python prepare.py
.venv/bin/python launch_qwen.py
.venv/bin/python server.py --open
```

本项目在 Windows 作为主要目标整理；其他系统的账号和 CLI 行为仍需在对应环境实际验证。
