from typing import Any, Dict, Iterable

from client import request_json
from query import compact_icon, find_icons


def get_icon_info(icon_id: str, project_id: str) -> Dict[str, Any]:
    """获取图标编辑接口所需的完整信息。"""
    res = request_json(
        "GET",
        "/api/icon/iconInfo.json",
        {"id": icon_id, "pid": project_id},
        referer=f"https://www.iconfont.cn/manage/index?manage_type=myprojects&projectId={project_id}",
    )
    return res.get("data") or {}


def update_icon(
    project_id: str,
    name: str = "",
    unicode: str = "",
    font_class: str = "",
    new_name: str = "",
    new_font_class: str = "",
    keep_fill: str = "",
    confirm: bool = False,
) -> Dict[str, Any]:
    """修改项目内单个图标的名称、class 或保留填充色配置。"""
    targets = find_icons(
        project_id,
        names=[name] if name else [],
        unicodes=[unicode] if unicode else [],
        font_classes=[font_class] if font_class else [],
    )
    if not targets:
        return {"matched": [], "message": "未匹配到需要修改的图标。"}
    if len(targets) > 1:
        return {
            "matched": [compact_icon(item) for item in targets],
            "message": "匹配到多个图标，请使用更精确的 --name、--unicode 或 --font-class。",
        }

    icon = targets[0]
    icon_info = get_icon_info(str(icon.get("id")), project_id)
    path_attributes = icon_info.get("path_attributes") or ""
    prototype_svg = icon_info.get("prototype_svg") or icon.get("svg") or ""
    payload = {
        "id": icon.get("id"),
        "pid": project_id,
        "prototype_svg": prototype_svg,
        "path_attributes": path_attributes,
        "svg": icon_info.get("svg") or prototype_svg,
        "origin_file": icon_info.get("origin_file") or "",
        "font_class": new_font_class
        or icon_info.get("font_class")
        or icon.get("font_class"),
        "unicode": int(str(icon_info.get("unicode") or icon.get("unicode")), 10),
        "icon_name": new_name
        or icon_info.get("icon_name")
        or icon_info.get("name")
        or icon.get("project_icon_name")
        or icon.get("name"),
    }
    if keep_fill:
        payload["keepFill"] = keep_fill.lower() in ("1", "true", "yes", "y")

    if not confirm:
        return {
            "dry_run": True,
            "before": compact_icon(icon),
            "payload": payload,
            "message": "未传入 --confirm，仅展示即将提交的修改。",
        }

    res = request_json(
        "POST",
        "/api/icon/updateProjectIcon.json",
        payload,
        referer=f"https://www.iconfont.cn/manage/index?manage_type=myprojects&projectId={project_id}",
    )
    return {"before": compact_icon(icon), "payload": payload, "result": res.get("data")}
