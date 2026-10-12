# 上传到自己的GitHub账号（私有仓库）

本项目默认私有。公开与否由仓库所有者决定，不由README里的文字决定。

## 上传前检查

Git只提交源码、原始题库、教程和测试。不要提交`tasks`、`practice-state.json`、`.qwen`、`.env`、密钥、个人聊天、`node_modules`或`.venv`。

```cmd
git status --short
git ls-files
```

本项目的`.gitignore`已经排除常见运行数据，但它不能移除曾经提交过的秘密。首次提交前仍要查看待提交文件。

## 方法一：GitHub CLI

从[GitHub CLI官方来源](https://cli.github.com/)安装`gh`，登录时使用官方交互认证，不把令牌写入脚本。

```cmd
gh auth login
gh auth status
```

在项目根目录初始化并提交：

```cmd
git init -b main
git add .
git commit -m "Add reproducible Vibe Coding practice workbench"
gh repo create vibe-coding-practice-workbench --private --source=. --remote=origin --push
gh repo view --web
```

如同名仓库已存在，先确认它是否就是要更新的项目，不强行覆盖或删除。Git身份若未设置，使用自己的姓名与GitHub提供的邮箱配置，不随意使用别人的身份。

## 方法二：GitHub网页创建+Git推送

1. 登录自己的GitHub，创建`vibe-coding-practice-workbench`，选择Private。
2. 不额外初始化README，因为本地已有完整项目。
3. 在本地提交后，按GitHub提供的仓库地址设置remote。

```cmd
git remote add origin https://github.com/你的用户名/vibe-coding-practice-workbench.git
git push -u origin main
```

使用官方登录或已有Git凭据，不在命令里拼接令牌。相关步骤以[GitHub官方说明](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github)为准。

## 发布后验收

- 仓库属于自己的账号，显示Private。
- README和docs能正常阅读，源码与六题模板齐全。
- Actions运行无模型测试；若账号策略禁用Actions，可在本地执行同样命令。
- 重新下载到一个空目录，按安装流程运行；账号配置由使用者自己完成。

GitHub仓库保存源码，不等于把带模型调用的本地工作台部署成公网网站。
