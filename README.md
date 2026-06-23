# Iconfont Helper 使用指南

`iconfont-helper` 用于让 AI 管理 Iconfont 项目图标，支持远程查询、上传、更新、删除、刷新 CDN，以及把远程图标同步成本地 SVG 和字体样式产物。

## 安装

本仓库符合开放 Agent Skills 标准，可通过 `skills` CLI 安装到 Claude Code、Cursor、Codex、OpenCode 等支持 Agent Skills 的 AI 工具中。

从 GitHub 安装：

```bash
npx skills add Youarefortunate/iconfont-helper
```

安装到全局：

```bash
npx skills add Youarefortunate/iconfont-helper --global
```

指定安装到某些 Agent：

```bash
npx skills add Youarefortunate/iconfont-helper --agent claude-code --agent cursor
```

只临时使用，不安装：

```bash
npx skills use Youarefortunate/iconfont-helper
```

也可以使用完整 GitHub 地址：

```bash
npx skills add https://github.com/Youarefortunate/iconfont-helper
```

## 快速开始

### 1. 准备环境文件

将示例环境文件改名为 `.env`：

```bash
cp scripts/.env.example scripts/.env
```

Windows PowerShell：

```powershell
Copy-Item scripts/.env.example scripts/.env
```

### 2. 填写 Iconfont 账号密码

打开 `scripts/.env`，填写你的 Iconfont 登录信息：

```env
ICONFONT_ACCOUNT=你的 Iconfont 登录账号
ICONFONT_PASSWORD=你的 Iconfont 登录密码
ICONFONT_COOKIE=
```

脚本会优先使用 `ICONFONT_COOKIE`。当 Cookie 缺失或过期，并且已配置账号密码时，会尝试自动登录刷新 Cookie。若触发验证码、滑块或其他风控（当前未实现），请手动登录 Iconfont 后更新 Cookie。

### 3. 配置需要同步到本地项目的 Iconfont 项目

如果只需要查询或远程增删改，可以直接通过 `--project-id` 指定 Iconfont 项目 ID。

如果需要同步到本地项目，请将示例配置复制为正式配置：

```bash
cp scripts/iconfont.example.json scripts/iconfont.json
```

Windows PowerShell：

```powershell
Copy-Item scripts/iconfont.example.json scripts/iconfont.json
```

然后按你的项目修改 `scripts/iconfont.json`：

```json
{
  "web-app-icons": {
    "name": "示例 Web 应用图标库",
    "project_id": "1234567",
    "font_name": "web-app-icons",
    "project_root": ".",
    "svg_dir": "assets/icons/svg",
    "outputs": [
      {
        "type": "scss_map",
        "path": "src/styles/icons.scss"
      },
      {
        "type": "font_face",
        "path": "src/styles/iconfont.css"
      }
    ]
  }
}
```

配置字段说明见：[SKILL.md 配置文件结构说明](./SKILL.md#配置文件-iconfontjson-结构说明)。

### 4. 直接向 AI 提需求

配置完成后，可以直接让 AI 使用本 skill，例如：

| 你可以这样问 AI                                      | AI 应执行的能力                                            |
| :--------------------------------------------- | :--------------------------------------------------- |
| `web-app-icons 项目有哪些 icon？`                          | 查询 `scripts/iconfont.json` 中 `web-app-icons` 对应项目，并列出远程图标。 |
| `帮我查询 Iconfont 项目 1234567 里面叫 arrow-right 的图标` | 使用项目 ID 直接查询指定图标。                                    |
| `帮我上传本地 ./assets/icons/add.svg 到 web-app-icons 项目`   | 先 dry-run 检查 SVG，再提示是否确认上传。                          |
| `帮我把 ./assets/icons 目录下的图标上传到 web-app-icons，并同步到本地`  | 上传目录内 SVG，等待确认后执行同步工作流。                              |
| `帮我删除 web-app-icons 项目里 id 为 123 的图标并同步本地`           | 按 ID 精确删除远程图标，并同步本地 SVG 和字体产物。                       |
