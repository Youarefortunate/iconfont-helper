from typing import Any, Dict

from client import request_json


def refresh_cdn(project_id: str, confirm: bool = False) -> Dict[str, Any]:
    """刷新 Iconfont 项目 CDN。"""
    if not confirm:
        return {
            "dry_run": True,
            "project_id": project_id,
            "message": "未传入 --confirm，仅展示即将刷新 CDN 的项目。",
        }

    res = request_json(
        "POST",
        "/api/project/cdn.json",
        {"pid": project_id},
        referer=f"https://www.iconfont.cn/manage/index?manage_type=myprojects&projectId={project_id}",
    )
    return {"project_id": project_id, "result": res.get("data")}
