import base64
import io
import os
import re
import shutil
import subprocess
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any, Dict, Iterable, Sequence

from config import IconfontConfigError, resolve_project
from create import upload_to_project
from delete import delete_icons
from query import list_icons
from update import update_icon


SCRIPT_DIR = Path(__file__).resolve().parent


def resolve_project_root(project_config: Dict[str, Any]) -> Path:
    """解析本地根目录。"""
    configured_root = str(project_config.get("project_root") or "").strip()
    env_root = os.environ.get("ICONFONT_PROJECT_ROOT", "").strip()
    root = configured_root or env_root
    if root:
        return Path(root).expanduser().resolve()
    return Path.cwd().resolve()


def resolve_project_path(project_root: Path, path_value: str) -> Path:
    """解析本地路径，支持绝对路径或相对 project_root 的路径。"""
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (project_root / path).resolve()


def resolve_project_context(project: str = "", project_id: str = "") -> Dict[str, Any]:
    """解析工作流需要的项目 key、项目 ID 与完整配置。"""
    project_config = resolve_project(project, project_id)
    project_key = str(project_config.get("key") or project)
    if not project_key:
        raise IconfontConfigError("工作流命令必须使用 iconfont.json 中注册的 --project")
    return {
        "key": project_key,
        "project_id": str(project_config.get("project_id")),
        "config": project_config,
    }


def normalize_svg(show_svg: str) -> str:
    """清洗 Iconfont 返回的 show_svg，保留 viewBox 和内部路径。"""
    view_box_match = re.search(r'viewBox="([^"]+)"', show_svg)
    inner_match = re.search(r"<svg[^>]*>([\s\S]*?)</svg>", show_svg)
    view_box = view_box_match.group(1) if view_box_match else "0 0 1024 1024"
    inner_content = inner_match.group(1) if inner_match else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}">\n{inner_content}\n</svg>'


def sync_remote_svgs(project_config: Dict[str, Any]) -> Dict[str, Any]:
    """将远程 Iconfont 项目图标同步为本地 SVG 文件。"""
    project_id = str(project_config.get("project_id") or "")
    svg_dir = str(project_config.get("svg_dir") or "")
    if not project_id or not svg_dir:
        raise IconfontConfigError("项目配置缺少 project_id 或 svg_dir")

    repo_root = resolve_project_root(project_config)
    folder = resolve_project_path(repo_root, svg_dir)
    folder.mkdir(parents=True, exist_ok=True)

    icons = list_icons(project_id)
    remote_names = set()
    new_count = 0
    updated_count = 0

    for icon in icons:
        name = str(icon.get("font_class") or icon.get("name") or "")
        show_svg = icon.get("show_svg") or ""
        if not name or not show_svg:
            continue

        remote_names.add(name)
        svg_content = normalize_svg(show_svg)
        file_path = folder / f"{name}.svg"
        if not file_path.exists():
            file_path.write_text(svg_content, encoding="utf-8")
            new_count += 1
            continue

        if file_path.read_text(encoding="utf-8").strip() != svg_content.strip():
            file_path.write_text(svg_content, encoding="utf-8")
            updated_count += 1

    removed = []
    for file_path in folder.glob("*.svg"):
        if file_path.stem not in remote_names:
            file_path.unlink()
            removed.append(str(file_path.relative_to(repo_root)))

    return {
        "svg_dir": svg_dir,
        "remote_count": len(remote_names),
        "new_count": new_count,
        "updated_count": updated_count,
        "removed": removed,
    }


def compile_svg_to_font(svg_dir: Path, temp_dist: Path, font_name: str) -> None:
    """使用 svgtofont 将本地 SVG 编译为字体资源。"""
    if temp_dist.exists():
        shutil.rmtree(temp_dist)
    temp_dist.mkdir(parents=True, exist_ok=True)

    command = [
        "npx",
        "-y",
        "svgtofont",
        "--sources",
        str(svg_dir),
        "--output",
        str(temp_dist),
        "--fontName",
        font_name,
        "--css",
        "true",
    ]
    completed = subprocess.run(command, text=True, capture_output=True, shell=True)
    if completed.returncode != 0:
        raise RuntimeError(
            f"svgtofont 编译失败: {completed.stderr or completed.stdout}"
        )


def parse_unicode_mappings(temp_dist: Path, font_name: str) -> Dict[str, str]:
    """从 svgtofont 生成的 CSS 中解析图标名称与 Unicode 映射。"""
    css_path = temp_dist / f"{font_name}.css"
    if not css_path.exists():
        raise RuntimeError(f"未找到生成的 CSS 映射文件: {css_path}")

    css_content = css_path.read_text(encoding="utf-8")
    pattern = rf"\.{font_name}-([\w-]+)::before\s*\{{\s*content:\s*\"\\([\w]+)\";\s*\}}"
    matches = re.findall(pattern, css_content)
    if not matches:
        raise RuntimeError("未能在 CSS 文件中解析出任何图标映射")

    return {name: f"\\{unicode_val}" for name, unicode_val in matches}


def write_scss_map(path: Path, info: Dict[str, str]) -> None:
    """写入 SCSS 图标映射表。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "/** 该文件由 iconfont-helper 自动生成，请勿手动编辑 */\n$icons: (\n"
    for name, unicode_val in info.items():
        content += f'  "{name}": "{unicode_val}",\n'
    content += ");\n"
    path.write_text(content, encoding="utf-8")


def inline_font_face(path: Path, font_name: str, base64_ttf: str) -> None:
    """在目标样式文件中内联写入 Base64 字体声明。"""
    if not path.exists():
        return

    content = path.read_text(encoding="utf-8")
    font_face_regex = r"(?:\/\*\*[\s\S]*?\*\/[\s\r\n]*)*@font-face\s*\{[\s\S]*?\}"
    new_font_face = f"""/** 该段 font-face 声明由 iconfont-helper 自动更新，请勿手动编辑 */
@font-face {{
  font-family: "{font_name}";
  src: url("data:font/ttf;charset=utf-8;base64,{base64_ttf}") format("truetype");
  font-weight: normal;
  font-style: normal;
}}"""
    updated = re.sub(font_face_regex, new_font_face, content)
    path.write_text(updated, encoding="utf-8")


def write_data_js(path: Path, info: Dict[str, str]) -> None:
    """写入图标示例 data.js 名称列表。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = (
        "/** 该文件由 iconfont-helper 自动生成，请勿手动编辑 */\nconst icons = [\n"
    )
    for name in info.keys():
        content += f'  "{name}",\n'
    content += "];\n\nexport default icons;\n"
    path.write_text(content, encoding="utf-8")


def build_local_outputs(project_config: Dict[str, Any]) -> Dict[str, Any]:
    """基于本地 SVG 目录生成字体、映射与样式输出。"""
    repo_root = resolve_project_root(project_config)
    svg_dir = resolve_project_path(repo_root, str(project_config.get("svg_dir") or ""))
    font_name = str(project_config.get("font_name") or "")
    outputs = project_config.get("outputs") or []
    if not svg_dir.exists() or not any(svg_dir.glob("*.svg")):
        raise RuntimeError(f"本地 SVG 目录为空或不存在: {svg_dir}")
    if not font_name:
        raise IconfontConfigError("项目配置缺少 font_name")

    temp_dist = svg_dir.parent / "dist-fonts-temp"
    compile_svg_to_font(svg_dir, temp_dist, font_name)
    info = parse_unicode_mappings(temp_dist, font_name)

    ttf_path = temp_dist / f"{font_name}.ttf"
    if not ttf_path.exists():
        raise RuntimeError(f"未能找到生成的 TTF 文件: {ttf_path}")
    base64_ttf = base64.b64encode(ttf_path.read_bytes()).decode("utf-8")

    written = []
    for output in outputs:
        out_path = output.get("path")
        out_type = output.get("type")
        if not out_path:
            continue
        target = resolve_project_path(repo_root, str(out_path))
        if out_type == "scss_map":
            write_scss_map(target, info)
        elif out_type == "font_face":
            inline_font_face(target, font_name, base64_ttf)
        elif out_type == "data_js":
            write_data_js(target, info)
        else:
            continue
        written.append(str(target.relative_to(repo_root)))

    if temp_dist.exists():
        shutil.rmtree(temp_dist)

    return {"font_name": font_name, "icon_count": len(info), "written": written}


def sync_local_assets(project_config: Dict[str, Any]) -> Dict[str, Any]:
    """同步远程 SVG 并构建本地图标产物。"""
    output = io.StringIO()
    with redirect_stdout(output):
        svg_result = sync_remote_svgs(project_config)
        build_result = build_local_outputs(project_config)

    return {
        "synced": True,
        "svg": svg_result,
        "build": build_result,
        "logs": [line for line in output.getvalue().splitlines() if line.strip()],
    }


def create_sync(
    project: str = "",
    project_id: str = "",
    svg: Sequence[str] | str = "",
    svg_dir: str = "",
    keep_fill: bool = False,
    confirm: bool = False,
) -> Dict[str, Any]:
    """上传图标后同步远程图标到本地并重新构建字体产物。"""
    context = resolve_project_context(project, project_id)
    create_result = upload_to_project(
        context["project_id"],
        svg=svg,
        svg_dir=svg_dir,
        keep_fill=keep_fill,
        confirm=confirm,
    )
    if not confirm:
        return {"operation": create_result, "sync": {"skipped": "未传入 --confirm"}}

    return {"operation": create_result, "sync": sync_local_assets(context["config"])}


def update_sync(
    project: str = "",
    project_id: str = "",
    name: str = "",
    unicode: str = "",
    font_class: str = "",
    new_name: str = "",
    new_font_class: str = "",
    keep_fill: str = "",
    confirm: bool = False,
) -> Dict[str, Any]:
    """修改图标后同步远程图标到本地并重新构建字体产物。"""
    context = resolve_project_context(project, project_id)
    update_result = update_icon(
        context["project_id"],
        name=name,
        unicode=unicode,
        font_class=font_class,
        new_name=new_name,
        new_font_class=new_font_class,
        keep_fill=keep_fill,
        confirm=confirm,
    )
    if not confirm:
        return {"operation": update_result, "sync": {"skipped": "未传入 --confirm"}}

    return {"operation": update_result, "sync": sync_local_assets(context["config"])}


def delete_sync(
    project: str = "",
    project_id: str = "",
    ids: Iterable[str] = (),
    names: Iterable[str] = (),
    unicodes: Iterable[str] = (),
    all_icons: bool = False,
    confirm: bool = False,
    yes_i_know: bool = False,
) -> Dict[str, Any]:
    """删除图标后同步远程图标到本地并重新构建字体产物。"""
    context = resolve_project_context(project, project_id)
    delete_result = delete_icons(
        context["project_id"],
        ids=ids,
        names=names,
        unicodes=unicodes,
        all_icons=all_icons,
        confirm=confirm,
        yes_i_know=yes_i_know,
    )
    if not confirm:
        return {"operation": delete_result, "sync": {"skipped": "未传入 --confirm"}}

    return {"operation": delete_result, "sync": sync_local_assets(context["config"])}
