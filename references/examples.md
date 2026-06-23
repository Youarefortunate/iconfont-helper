# Iconfont Helper 使用示例

本文档与 [commands.md](./commands.md) 保持相同分组，用于快速查找每类命令的常见调用方式。

执行示例时默认当前目录位于本 skill 根目录：`.trae/skills/iconfont-helper`。如在仓库根目录执行，请把 `scripts/main.py` 替换为 `.trae/skills/iconfont-helper/scripts/main.py`。

## 项目配置组

对应命令说明：[项目配置组](./commands.md#项目配置组)

### 查看所有已注册项目

```bash
python scripts/main.py projects
```

## 查询组

对应命令说明：[查询组](./commands.md#查询组)

### 查看项目概要

```bash
python scripts/main.py detail --project=web-app-icons
```

### 查看项目全部图标

```bash
python scripts/main.py list --project=web-app-icons
```

### 按名称查询单个图标

```bash
python scripts/main.py find --project=web-app-icons --name arrow-right
```

### 按多个条件查询图标

```bash
python scripts/main.py find --project=web-app-icons --name arrow-right --font-class arrow-right --unicode 58883
```

### 删除前查询目标 ID

```bash
python scripts/main.py find --project=web-app-icons --name arrow-right
```

如果返回多个同名图标，后续删除应选择其中一个 `id` 精确删除。

## 远程写操作组

对应命令说明：[远程写操作组](./commands.md#远程写操作组)

### 上传单个 SVG

```bash
python scripts/main.py create --project=web-app-icons --svg ./assets/icons/arrow-right.svg --confirm
```

### 批量上传 SVG

```bash
python scripts/main.py create --project=web-app-icons --svg a.svg --svg b.svg --confirm
```

### 上传目录内所有 SVG

```bash
python scripts/main.py create --project=web-app-icons --svg-dir ./assets/icons --confirm
```

### 修改图标名称和 font_class

```bash
python scripts/main.py update --project=web-app-icons --font-class arrow-right --new-name arrow-right-test --new-font-class arrow-right-test --confirm
```

### 按 ID 精确删除图标

```bash
python scripts/main.py delete --project=web-app-icons --id 47886136 --confirm
```

### 按名称 dry-run 删除

```bash
python scripts/main.py delete --project=web-app-icons --name arrow-right
```

如果存在多个同名图标，该命令会阻止删除并提示改用 `--id`。

### 全删 dry-run

```bash
python scripts/main.py delete --project=web-app-icons --all
```

### 全删真实执行

```bash
python scripts/main.py delete --project=web-app-icons --all --confirm --yes-i-know
```

### 刷新 CDN

```bash
python scripts/main.py refresh --project=web-app-icons --confirm
```

## 同步工作流组

对应命令说明：[同步工作流组](./commands.md#同步工作流组)

### 上传后同步本地 SVG 与字体产物

```bash
python scripts/main.py create-sync --project=web-app-icons --svg ./assets/icons/arrow-right.svg --confirm
```

新上传素材可能需要约 5 分钟审核；如果同步结果没有出现新图标，请等待后重新执行同步流程。

### 修改后同步本地 SVG 与字体产物

```bash
python scripts/main.py update-sync --project=web-app-icons --font-class arrow-right --new-name arrow-right-test --new-font-class arrow-right-test --confirm
```

### 删除后同步本地 SVG 与字体产物

```bash
python scripts/main.py delete-sync --project=web-app-icons --id 47886136 --confirm
```

### library-icons 上传后同步

```bash
python scripts/main.py create-sync --project=library-icons --svg ./packages/icon-library/assets/svg/example.svg --confirm
```

### library-icons 删除后同步

```bash
python scripts/main.py delete-sync --project=library-icons --id 47886136 --confirm
```

## 本地输出类型组

对应命令说明：[本地输出类型组](./commands.md#本地输出类型组)

### SCSS 映射输出配置

```json
{
  "type": "scss_map",
  "path": "src/styles/icons.scss"
}
```

### font-face 输出配置

```json
{
  "type": "font_face",
  "path": "src/styles/iconfont.css"
}
```

### data_js 输出配置

```json
{
  "type": "data_js",
  "path": "packages/icon-library/examples/icons.js"
}
```
