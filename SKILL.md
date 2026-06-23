---
name: iconfont-helper
description: 自动管理 Iconfont 项目图标，支持远程增删改查、同步本地 SVG，并生成 Base64 图标字体和样式定义。
author: Youfortunate
version: 1.0.0
license: MIT
repository: https://github.com/Youarefortunate/iconfont-helper
---

# Iconfont Helper

本 skill 用于管理 iconfont.cn 项目图标。AI 在用户提出同步图标、构建图标字体、查询图标、上传图标、修改图标或删除图标时使用本 skill。

## 使用原则

1. 先判断用户要操作的项目 key，优先使用用户从 [iconfont.example.json](./scripts/iconfont.example.json) 复制生成的 `scripts/iconfont.json` 中已注册的 `--project`。
2. 不确定命令参数时，不要猜测；先查 [命令大全](./references/commands.md)。
3. 需要示例时，查 [使用示例](./references/examples.md)。
4. 新上传素材通常有约 `5` 分钟审核时间；审核期间查询或同步结果可能不会立即出现新图标。

## 操作结果反馈

执行上传、更新、删除、同步等写操作后，必须在最后向用户汇总本次操作结果，避免只返回原始 JSON。

| 操作类型 | 必须说明 | 包含的操作/受影响的图标 |
| :--- | :--- | :--- |
| 上传 | 成功提交了多少个新图标、被跳过的 SVG 及原因；Iconfont 审核等待提示。 | 详细列出所有新上传的本地文件名 (如 `icon-name.svg`) 及其对应的图标 `name`。 |
| 更新 | 实际修改了哪个图标，修改前后的 `name`、`font_class`、颜色保留等关键字段。 | 详细列出修改过的图标原名称、新名称、图标 ID 等。 |
| 删除 | 未匹配或因同名冲突未删除时说明原因。 | 详细列出被删除的图标名称 (`name`)、图标 ID (`id`) 及 Unicode。 |
| 同步 | 本地新增、更新、删除了哪些 SVG，以及生成或更新了哪些字体与样式产物。 | 详细列出本地新增、更新和删除的具体 SVG 图标列表。 |
| 复杂 SVG | 如果图标因渐变、滤镜、`defs`、`use`、`mask`、位图或 `url(#...)` 引用等特性无法上传，必须说明检测到的具体原因，并提示先转为纯 path、纯色 fill/stroke 后再上传。 | 详细列出未通过检测的具体本地 SVG 文件名及路径。 |

## 环境文件

Cookie 与可选自动登录配置统一放在本 skill 内：

```text
scripts/.env
```

格式：

```env
ICONFONT_COOKIE=你的 Iconfont 登录 Cookie
ICONFONT_ACCOUNT=你的 Iconfont 登录账号，可选
ICONFONT_PASSWORD=你的 Iconfont 登录密码，可选
```

如果 Cookie 缺失或过期，脚本会优先尝试使用 `ICONFONT_ACCOUNT` / `ICONFONT_PASSWORD` 自动登录刷新 `ICONFONT_COOKIE`；未配置账号密码、账号密码错误、触发风控或验证码时，会提示手动登录后更新 `scripts/.env`。

## 命令分组索引

AI 需要使用哪块能力，就进入命令大全中对应分组查找命令；需要调用样例时，进入使用示例中对应分组查找示例。SKILL.md 不展开具体命令细节。

| 分组 | 适用场景 | 命令说明 | 使用示例 |
| :--- | :--- | :--- | :--- |
| 项目配置组 | 查看当前支持哪些 Iconfont 项目、项目 key 和输出配置 | [项目配置组](./references/commands.md#项目配置组) | [项目配置组示例](./references/examples.md#项目配置组) |
| 查询组 | 查看项目详情、列出图标、按名称/Unicode/font_class 查询图标 | [查询组](./references/commands.md#查询组) | [查询组示例](./references/examples.md#查询组) |
| 远程写操作组 | 只修改远程 Iconfont 项目，包括上传、修改、删除、刷新 CDN | [远程写操作组](./references/commands.md#远程写操作组) | [远程写操作组示例](./references/examples.md#远程写操作组) |
| 同步工作流组 | 远程写操作后同步本地 SVG，并重新生成字体与样式产物 | [同步工作流组](./references/commands.md#同步工作流组) | [同步工作流组示例](./references/examples.md#同步工作流组) |
| 本地输出类型组 | 理解 `iconfont.json` 中 `outputs` 的输出类型与产物 | [本地输出类型组](./references/commands.md#本地输出类型组) | [本地输出类型组示例](./references/examples.md#本地输出类型组) |

## 项目注册表

| 项目 Key | 项目名称 | 关联 Iconfont 项目 ID | 字体名称 |
| :--- | :--- | :--- | :--- |
| `web-app-icons` | 示例 Web 应用图标库 | `1234567` | `web-app-icons` |
| `library-icons` | 示例组件库图标库 | `7654321` | `library-icons` |

项目的所有输出文件映射关系（如本地 SVG 目录、编译输出路径等）统一管理在用户本地的 `scripts/iconfont.json` 配置文件中。发布版默认只保留示例配置；实际使用时可复制 [iconfont.example.json](./scripts/iconfont.example.json) 为 `iconfont.json` 并替换为自己的项目参数。各项目可独立定义所需参数及输出规则。

### 配置文件 (iconfont.json) 结构说明

`iconfont.json` 的根对象为项目映射表，键为该项目的 Key，值为该项目的配置详情。

每个项目配置详情支持以下字段：

| 配置字段 | 类型 | 是否必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `name` | `string` | 是 | 项目名称描述，用于可读性。 |
| `project_id` | `string` | 是 | 关联的 Iconfont.cn 项目 ID。 |
| `font_name` | `string` | 是 | 生成的字体族名称，例如 `web-app-icons`。 |
| `project_root` | `string` | 否 | 本地同步根目录。相对路径基于执行命令时的当前目录解析；未配置时使用环境变量 `ICONFONT_PROJECT_ROOT`，仍未配置则使用当前执行目录。 |
| `associated_project` | `string` | 否 | 可选的关联项目描述，仅用于可读性。 |
| `svg_dir` | `string` | 是 | 本地存放同步 SVG 文件的路径；支持绝对路径，或相对 `project_root` 的路径。 |
| `outputs` | `array` | 是 | 编译输出配置列表，指定要生成或内联更新的目标文件。 |

`outputs` 数组中的每一项配置结构如下：

| 配置字段 | 类型 | 是否必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `type` | `string` | 是 | 输出类型。支持 `scss_map`、`font_face`、`data_js`。 |
| `path` | `string` | 是 | 输出目标文件相对于工作区根目录的物理相对路径。 |

输出类型说明请查：[本地输出类型组](./references/commands.md#本地输出类型组)。
