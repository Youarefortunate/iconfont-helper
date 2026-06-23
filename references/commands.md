# Iconfont Helper 命令大全

本文档按功能组列出 `iconfont-helper` 当前支持的全部命令。命令统一入口为 `../scripts/main.py`。

- 命令示例详见：[examples.md](./examples.md)
- 项目配置来源：[../scripts/iconfont.json](../scripts/iconfont.json)
- 环境文件：`../scripts/.env`

## 通用参数

| 参数 | 适用命令 | 说明 |
| :--- | :--- | :--- |
| `--project` | 除 `projects` 外的大多数命令 | 使用 `iconfont.json` 中注册的项目 key，例如 `demo-mp`、`component-lib`。工作流命令必须优先使用该参数。 |
| `--project-id` | 除 `projects` 外的大多数命令 | 直接指定 Iconfont 项目 ID。仅适合查询或单次远程操作；同步构建工作流需要完整项目配置，建议使用 `--project`。 |
| `--confirm` | 写操作、工作流命令 | 确认执行真实写操作。不传时只做 dry-run 或展示将要处理的目标。 |

## 项目配置组

查看本 skill 已注册的 Iconfont 项目，不会访问远程写接口。

示例：[项目配置组示例](./examples.md#项目配置组)

| 命令 | 功能 | 关键参数 | 输出重点 | 安全说明 |
| :--- | :--- | :--- | :--- | :--- |
| `projects` | 列出 `iconfont.json` 中注册的项目 | 无 | 项目 key、项目名称、Iconfont 项目 ID、字体名称、本地 SVG 目录、输出列表 | 只读 |

## 查询组

查询组只读取远程 Iconfont 项目数据，不会修改项目。

示例：[查询组示例](./examples.md#查询组)

| 命令 | 功能 | 关键参数 | 输出重点 | 安全说明 |
| :--- | :--- | :--- | :--- | :--- |
| `detail` | 查看项目概要 | `--project` / `--project-id` | 项目对象、字体对象、图标数量 | 只读 |
| `list` | 列出项目内全部图标摘要 | `--project` / `--project-id` | `id`、`project_has_icon_id`、`name`、`font_class`、`unicode` | 只读 |
| `find` | 按条件查询图标 | `--name`、`--unicode`、`--font-class` 可重复传入 | 匹配图标摘要 | 只读；删除前建议先用它确认目标 `id` |

## 远程写操作组

远程写操作会调用 Iconfont 接口修改远程项目。除 dry-run 外，必须传入 `--confirm`。

示例：[远程写操作组示例](./examples.md#远程写操作组)

| 命令 | 功能 | 关键参数 | 输出重点 | 安全说明 |
| :--- | :--- | :--- | :--- | :--- |
| `create` | 上传本地 SVG 并提交到 Iconfont 项目 | `--svg`、`--svg-dir`、`--keep-fill`、`--confirm` | 上传结果、提交结果、SVG 兼容性检查、审核提示 | Iconfont 新上传素材通常有约 5 分钟审核时间；渐变、滤镜、defs、use、mask、位图等复杂 SVG 会被预检提示并跳过上传；`submit.unsuccess.status=0` 通常表示审核中 |
| `update` | 修改单个图标信息 | `--name` / `--unicode` / `--font-class`、`--new-name`、`--new-font-class`、`--keep-fill`、`--confirm` | 修改前摘要、提交 payload、接口结果 | 匹配条件应唯一；如目标不唯一，先用 `find` 查清楚 |
| `delete` | 删除远程项目图标 | `--id`、`--name`、`--unicode`、`--all`、`--confirm`、`--yes-i-know` | 待删除目标、接口结果 | 优先使用 `--id`；按 `--name` 匹配到多个同名图标时会阻止执行；全删必须同时传 `--confirm --yes-i-know` |
| `refresh` | 刷新项目 CDN | `--confirm` | CDN 刷新结果 | 写操作；只在确认需要刷新时执行 |

## 同步工作流组

工作流命令会把远程写操作与本地同步构建串联起来：先执行远程新增、修改或删除，再拉取远程图标，同步本地 SVG，清理远程已不存在的 SVG，并生成字体与样式产物。

示例：[同步工作流组示例](./examples.md#同步工作流组)

| 命令 | 功能 | 关键参数 | 输出重点 | 安全说明 |
| :--- | :--- | :--- | :--- | :--- |
| `create-sync` | 上传 SVG 后同步本地 SVG 与字体产物 | `--project`、`--svg` / `--svg-dir`、`--keep-fill`、`--confirm` | 上传结果、SVG 兼容性检查、本地 SVG 同步结果、构建输出 | 新上传素材可能仍在审核中，审核期间同步结果可能暂时没有新增图标；复杂 SVG 会被预检提示并跳过上传 |
| `update-sync` | 修改图标后同步本地 SVG 与字体产物 | `--project`、匹配参数、修改参数、`--confirm` | 修改结果、本地 SVG 同步结果、构建输出 | 修改目标应唯一；建议先 `find` |
| `delete-sync` | 删除图标后同步本地 SVG 与字体产物 | `--project`、`--id` / `--name` / `--unicode`、`--confirm` | 删除结果、本地 SVG 清理结果、构建输出 | 优先使用 `--id`；按 `--name` 多匹配会阻止执行 |

## 本地输出类型组

该组不是 CLI 子命令，而是 `iconfont.json` 中 `outputs` 的配置类型。同步工作流会根据这些类型生成对应产物。

示例：[本地输出类型组示例](./examples.md#本地输出类型组)

| 输出类型 | 功能 | 配置字段 | 输出行为 |
| :--- | :--- | :--- | :--- |
| `scss_map` | 生成 SCSS 图标映射表 | `type`、`path` | 写入 `$icons` map，例如图标名到 Unicode 的映射 |
| `font_face` | 更新样式文件中的 `@font-face` | `type`、`path` | 将 TTF 转 Base64 后内联到目标 SCSS/WXSS |
| `data_js` | 生成图标名称数组 JS 文件 | `type`、`path` | 写入图标名称列表，供示例页或遍历展示使用 |
