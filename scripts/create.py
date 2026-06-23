from pathlib import Path
from typing import Any, Dict, List, Sequence

from client import request_json, upload_svg
from svg_check import assert_svg_uploadable, inspect_svg_compatibility


def collect_svg_files(svg: Sequence[str] | str = "", svg_dir: str = "") -> List[Path]:
    """收集单个、多个或目录内的 SVG 文件。"""
    files: List[Path] = []
    svg_items = [svg] if isinstance(svg, str) else list(svg)

    for item in svg_items:
        if not item:
            continue
        path = Path(item).resolve()
        if not path.exists() or path.suffix.lower() != ".svg":
            raise ValueError(f"不是有效的 SVG 文件: {path}")
        files.append(path)

    if svg_dir:
        folder = Path(svg_dir).resolve()
        if not folder.exists() or not folder.is_dir():
            raise ValueError(f"不是有效的 SVG 目录: {folder}")
        files.extend(sorted(folder.glob("*.svg")))

    if not files:
        raise ValueError("请传入 --svg 或 --svg-dir")

    return files


def upload_to_project(
    project_id: str,
    svg: Sequence[str] | str = "",
    svg_dir: str = "",
    confirm: bool = False,
    keep_fill: bool = False,
) -> Dict[str, Any]:
    """上传 SVG 并提交到指定 Iconfont 项目。"""
    files = collect_svg_files(svg, svg_dir)
    checks = [inspect_svg_compatibility(item) for item in files]
    unsupported = [item for item in checks if not item["supported"]]

    if not confirm:
        return {
            "dry_run": True,
            "project_id": project_id,
            "files": [str(item) for item in files],
            "compatibility": checks,
            "message": "未传入 --confirm，仅展示即将上传的 SVG 文件；compatibility 中 supported=false 的文件不建议上传。",
        }

    if unsupported:
        return {
            "uploaded": [],
            "skipped": unsupported,
            "message": "检测到不适合上传到 Iconfont 的 SVG，已跳过上传。请按 suggestion 处理后再上传。",
        }

    uploaded = []
    for file_path in files:
        assert_svg_uploadable(file_path)
        res = upload_svg(file_path)
        data = res.get("data") or {}
        uploaded.append(
            {
                "id": data.get("id"),
                "name": data.get("name") or file_path.stem,
                "unicode": data.get("unicode"),
                "slug": data.get("slug", ""),
                "keepFill": keep_fill,
            }
        )

    payload = {
        "advanceType": "project",
        "projectChooseType": "choose",
        "projectId": project_id,
        "updateIcons": uploaded,
    }
    submit_res = request_json(
        "POST",
        "/api/updateUploadIcons.json",
        payload,
        referer="https://www.iconfont.cn/icons/upload",
    )

    return {
        "uploaded": uploaded,
        "submit": submit_res.get("data"),
        "tip": "Iconfont 新上传素材通常会有约 5 分钟审核时间；若 submit.unsuccess 中 status=0，表示已提交但仍在审核中，请稍后再同步或查询项目。",
    }
