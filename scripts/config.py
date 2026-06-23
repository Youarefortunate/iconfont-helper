import json
from pathlib import Path
from typing import Any, Dict


SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "iconfont.json"


class IconfontConfigError(RuntimeError):
    """Iconfont 项目配置错误。"""


def load_projects() -> Dict[str, Dict[str, Any]]:
    """读取 iconfont.json 中注册的项目配置。"""
    if not CONFIG_PATH.exists():
        raise IconfontConfigError(
            f"未找到项目配置文件: {CONFIG_PATH}，请先复制 scripts/iconfont.example.json 为 scripts/iconfont.json 并填写自己的项目配置"
        )

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def resolve_project(project: str = "", project_id: str = "") -> Dict[str, Any]:
    """通过项目 key 或项目 ID 解析 Iconfont 项目配置。"""
    projects = load_projects()

    if project:
        if project not in projects:
            known = ", ".join(projects.keys()) or "无"
            raise IconfontConfigError(f"未知项目 key: {project}，当前可用: {known}")
        return {"key": project, **projects[project]}

    if project_id:
        for key, item in projects.items():
            if str(item.get("project_id")) == str(project_id):
                return {"key": key, **item}
        return {"key": "", "project_id": str(project_id), "name": "未注册项目"}

    raise IconfontConfigError("请传入 --project 或 --project-id")


def list_project_rows() -> list[dict[str, str]]:
    """返回全部已注册项目的可读列表。"""
    rows = []
    for key, item in load_projects().items():
        rows.append(
            {
                "key": key,
                "name": str(item.get("name", "")),
                "project_id": str(item.get("project_id", "")),
                "font_name": str(item.get("font_name", "")),
                "svg_dir": str(item.get("svg_dir", "")),
            }
        )
    return rows
