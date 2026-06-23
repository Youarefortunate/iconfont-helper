from typing import Any, Dict, Iterable, List

from client import request_json


def get_project_detail(project_id: str) -> Dict[str, Any]:
    """获取指定 Iconfont 项目详情。"""
    res = request_json(
        "GET",
        "/api/project/detail.json",
        {"pid": project_id},
        referer=f"https://www.iconfont.cn/manage/index?manage_type=myprojects&projectId={project_id}",
    )
    return res.get("data") or {}


def list_icons(project_id: str) -> List[Dict[str, Any]]:
    """列出项目内全部图标。"""
    return list(get_project_detail(project_id).get("icons") or [])


def compact_icon(icon: Dict[str, Any]) -> Dict[str, Any]:
    """输出适合命令行查看的图标摘要。"""
    return {
        "id": icon.get("id"),
        "project_has_icon_id": icon.get("project_has_icon_id"),
        "name": icon.get("name"),
        "font_class": icon.get("font_class"),
        "unicode": str(icon.get("unicode", "")),
        "project_icon_name": icon.get("project_icon_name"),
    }


def find_icons(
    project_id: str,
    names: Iterable[str] | None = None,
    unicodes: Iterable[str] | None = None,
    font_classes: Iterable[str] | None = None,
) -> List[Dict[str, Any]]:
    """按 name、unicode 或 font_class 查找图标。"""
    name_set = {item for item in (names or []) if item}
    unicode_set = {str(item) for item in (unicodes or []) if item}
    font_class_set = {item for item in (font_classes or []) if item}

    result = []
    for icon in list_icons(project_id):
        matched = False
        if name_set and str(icon.get("name", "")) in name_set:
            matched = True
        if name_set and str(icon.get("project_icon_name", "")) in name_set:
            matched = True
        if unicode_set and str(icon.get("unicode", "")) in unicode_set:
            matched = True
        if font_class_set and str(icon.get("font_class", "")) in font_class_set:
            matched = True
        if matched:
            result.append(icon)
    return result
