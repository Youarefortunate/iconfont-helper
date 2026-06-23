from typing import Any, Dict, Iterable, List

from client import request_json
from query import compact_icon, find_icons, list_icons


def resolve_delete_targets(
    project_id: str,
    ids: Iterable[str],
    names: Iterable[str],
    unicodes: Iterable[str],
    all_icons: bool,
) -> List[Dict[str, Any]]:
    """解析需要从项目中删除的图标。"""
    if all_icons:
        return list_icons(project_id)

    id_set = {str(item) for item in ids if item}
    if id_set:
        return [icon for icon in list_icons(project_id) if str(icon.get("id")) in id_set]

    return find_icons(project_id, names=names, unicodes=unicodes)


def has_ambiguous_names(targets: List[Dict[str, Any]], names: Iterable[str]) -> bool:
    """判断按 name 删除是否匹配到多个同名图标。"""
    name_set = {name for name in names if name}
    for name in name_set:
        if sum(1 for icon in targets if icon.get("name") == name) > 1:
            return True
    return False


def delete_icons(
    project_id: str,
    ids: Iterable[str] = (),
    names: Iterable[str] = (),
    unicodes: Iterable[str] = (),
    all_icons: bool = False,
    confirm: bool = False,
    yes_i_know: bool = False,
) -> Dict[str, Any]:
    """按 ID、名称、Unicode 或全量删除项目图标。"""
    targets = resolve_delete_targets(project_id, ids, names, unicodes, all_icons)
    compact_targets = [compact_icon(item) for item in targets]

    if all_icons and not yes_i_know:
        return {
            "dry_run": True,
            "targets": compact_targets,
            "message": "全删需要同时传入 --confirm --yes-i-know。",
        }

    if not ids and not all_icons and has_ambiguous_names(targets, names):
        return {
            "blocked": True,
            "targets": compact_targets,
            "message": "按 name 匹配到多个同名图标，直接删除不安全；请改用 --id 精确删除。",
        }

    if not confirm:
        return {
            "dry_run": True,
            "targets": compact_targets,
            "message": "未传入 --confirm，仅展示即将删除的图标。",
        }

    icon_ids = [str(icon.get("id")) for icon in targets if icon.get("id")]
    if not icon_ids:
        return {"deleted": [], "message": "未匹配到可删除的图标 id。"}

    res = request_json(
        "POST",
        "/api/icon/deleteProjectIcon.json",
        {"type": "project", "ids": ",".join(icon_ids), "pid": project_id},
        referer=f"https://www.iconfont.cn/manage/index?manage_type=myprojects&projectId={project_id}",
    )

    return {"deleted": compact_targets, "result": res.get("data")}
