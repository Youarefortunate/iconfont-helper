import argparse
import json
import sys
from typing import Any, Dict

from config import IconfontConfigError, list_project_rows, resolve_project
from create import upload_to_project
from delete import delete_icons
from env import IconfontAuthError
from query import compact_icon, find_icons, get_project_detail, list_icons
from refresh import refresh_cdn
from update import update_icon
from workflow import create_sync, delete_sync, update_sync


def print_json(data: Any) -> None:
    """以 JSON 格式输出命令结果。"""
    print(json.dumps(data, ensure_ascii=False, indent=2))


def add_project_args(parser: argparse.ArgumentParser) -> None:
    """为命令添加项目解析参数。"""
    parser.add_argument("--project", default="", help="iconfont.json 中注册的项目 key")
    parser.add_argument("--project-id", default="", help="Iconfont 项目 ID")


def resolve_project_id(args: argparse.Namespace) -> str:
    """解析命令行传入的项目 ID。"""
    project = resolve_project(args.project, args.project_id)
    return str(project.get("project_id") or args.project_id)


def build_parser() -> argparse.ArgumentParser:
    """构建 Iconfont 增删改查与同步工作流命令。"""
    parser = argparse.ArgumentParser(description="Iconfont 项目图标增删改查脚本")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 项目配置组：查看 iconfont.json 中已经注册的项目路由。
    subparsers.add_parser("projects", help="查看 iconfont.json 中注册的项目")

    # 查询组：只读取远程项目数据，不修改 Iconfont 项目。
    detail_parser = subparsers.add_parser("detail", help="查看项目详情")
    add_project_args(detail_parser)

    list_parser = subparsers.add_parser("list", help="列出项目图标")
    add_project_args(list_parser)

    find_parser = subparsers.add_parser(
        "find", help="按 name、unicode 或 font_class 查询图标"
    )
    add_project_args(find_parser)
    find_parser.add_argument(
        "--name", action="append", default=[], help="图标名称，可重复传入"
    )
    find_parser.add_argument(
        "--unicode", action="append", default=[], help="Unicode 编码，可重复传入"
    )
    find_parser.add_argument(
        "--font-class", action="append", default=[], help="font_class，可重复传入"
    )

    # 写入组：直接调用 Iconfont 接口执行新增、删除、修改与 CDN 刷新。
    upload_parser = subparsers.add_parser("create", help="上传 SVG 并加入项目")
    add_project_args(upload_parser)
    upload_parser.add_argument(
        "--svg", action="append", default=[], help="SVG 文件路径，可重复传入"
    )
    upload_parser.add_argument("--svg-dir", default="", help="批量 SVG 目录")
    upload_parser.add_argument(
        "--keep-fill", action="store_true", help="提交彩色图标时保留填充色"
    )
    upload_parser.add_argument(
        "--confirm", action="store_true", help="确认执行真实写操作"
    )

    delete_parser = subparsers.add_parser("delete", help="删除项目图标")
    add_project_args(delete_parser)
    delete_parser.add_argument(
        "--id",
        action="append",
        default=[],
        help="按 Iconfont 图标 ID 精确删除，可重复传入",
    )
    delete_parser.add_argument(
        "--name",
        action="append",
        default=[],
        help="按图标名称删除，可重复传入；同名多个时会阻止执行",
    )
    delete_parser.add_argument(
        "--unicode", action="append", default=[], help="按 Unicode 删除，可重复传入"
    )
    delete_parser.add_argument("--all", action="store_true", help="删除项目内全部图标")
    delete_parser.add_argument(
        "--confirm", action="store_true", help="确认执行真实写操作"
    )
    delete_parser.add_argument("--yes-i-know", action="store_true", help="全删二次确认")

    update_parser = subparsers.add_parser("update", help="修改项目图标信息")
    add_project_args(update_parser)
    update_parser.add_argument("--name", default="", help="通过图标名称匹配")
    update_parser.add_argument("--unicode", default="", help="通过 Unicode 匹配")
    update_parser.add_argument("--font-class", default="", help="通过 font_class 匹配")
    update_parser.add_argument("--new-name", default="", help="新的图标名称")
    update_parser.add_argument("--new-font-class", default="", help="新的 font_class")
    update_parser.add_argument(
        "--keep-fill", default="", help="是否保留填充色，true 或 false"
    )
    update_parser.add_argument(
        "--confirm", action="store_true", help="确认执行真实写操作"
    )

    refresh_parser = subparsers.add_parser("refresh", help="刷新项目 CDN")
    add_project_args(refresh_parser)
    refresh_parser.add_argument(
        "--confirm", action="store_true", help="确认执行真实写操作"
    )

    # 工作流组：将远程写操作与本地 SVG 同步和字体构建串联。
    create_sync_parser = subparsers.add_parser(
        "create-sync", help="上传 SVG 后同步本地 SVG 与字体产物"
    )
    add_project_args(create_sync_parser)
    create_sync_parser.add_argument(
        "--svg", action="append", default=[], help="SVG 文件路径，可重复传入"
    )
    create_sync_parser.add_argument("--svg-dir", default="", help="批量 SVG 目录")
    create_sync_parser.add_argument(
        "--keep-fill", action="store_true", help="提交彩色图标时保留填充色"
    )
    create_sync_parser.add_argument(
        "--confirm", action="store_true", help="确认执行真实写操作"
    )

    update_sync_parser = subparsers.add_parser(
        "update-sync", help="修改图标后同步本地 SVG 与字体产物"
    )
    add_project_args(update_sync_parser)
    update_sync_parser.add_argument("--name", default="", help="通过图标名称匹配")
    update_sync_parser.add_argument("--unicode", default="", help="通过 Unicode 匹配")
    update_sync_parser.add_argument(
        "--font-class", default="", help="通过 font_class 匹配"
    )
    update_sync_parser.add_argument("--new-name", default="", help="新的图标名称")
    update_sync_parser.add_argument(
        "--new-font-class", default="", help="新的 font_class"
    )
    update_sync_parser.add_argument(
        "--keep-fill", default="", help="是否保留填充色，true 或 false"
    )
    update_sync_parser.add_argument(
        "--confirm", action="store_true", help="确认执行真实写操作"
    )

    delete_sync_parser = subparsers.add_parser(
        "delete-sync", help="删除图标后同步本地 SVG 与字体产物"
    )
    add_project_args(delete_sync_parser)
    delete_sync_parser.add_argument(
        "--id",
        action="append",
        default=[],
        help="按 Iconfont 图标 ID 精确删除，可重复传入",
    )
    delete_sync_parser.add_argument(
        "--name",
        action="append",
        default=[],
        help="按图标名称删除，可重复传入；同名多个时会阻止执行",
    )
    delete_sync_parser.add_argument(
        "--unicode", action="append", default=[], help="按 Unicode 删除，可重复传入"
    )
    delete_sync_parser.add_argument(
        "--all", action="store_true", help="删除项目内全部图标"
    )
    delete_sync_parser.add_argument(
        "--confirm", action="store_true", help="确认执行真实写操作"
    )
    delete_sync_parser.add_argument(
        "--yes-i-know", action="store_true", help="全删二次确认"
    )

    return parser


def run(args: argparse.Namespace) -> Dict[str, Any] | list[Dict[str, Any]]:
    """根据命令分发到查询、写入或工作流模块。"""
    # 项目配置分支：不需要解析具体项目 ID，直接返回注册表。
    if args.command == "projects":
        return list_project_rows()

    project_id = resolve_project_id(args)

    # 查询分支：读取项目详情、图标列表或按条件筛选图标。
    if args.command == "detail":
        detail = get_project_detail(project_id)
        return {
            "project": detail.get("project"),
            "font": detail.get("font"),
            "icon_count": len(detail.get("icons") or []),
        }

    if args.command == "list":
        return [compact_icon(icon) for icon in list_icons(project_id)]

    if args.command == "find":
        return [
            compact_icon(icon)
            for icon in find_icons(
                project_id,
                names=args.name,
                unicodes=args.unicode,
                font_classes=args.font_class,
            )
        ]

    # 新增分支：上传本地 SVG，并提交到指定 Iconfont 项目。
    if args.command == "create":
        return upload_to_project(
            project_id,
            svg=args.svg,
            svg_dir=args.svg_dir,
            keep_fill=args.keep_fill,
            confirm=args.confirm,
        )

    # 删除分支：按名称、Unicode 或全量删除远程项目图标。
    if args.command == "delete":
        return delete_icons(
            project_id,
            ids=args.id,
            names=args.name,
            unicodes=args.unicode,
            all_icons=args.all,
            confirm=args.confirm,
            yes_i_know=args.yes_i_know,
        )

    # 修改分支：更新单个远程图标的名称、font_class 或保留填充色配置。
    if args.command == "update":
        return update_icon(
            project_id,
            name=args.name,
            unicode=args.unicode,
            font_class=args.font_class,
            new_name=args.new_name,
            new_font_class=args.new_font_class,
            keep_fill=args.keep_fill,
            confirm=args.confirm,
        )

    # 刷新分支：刷新 Iconfont 项目的 CDN 地址。
    if args.command == "refresh":
        return refresh_cdn(project_id, confirm=args.confirm)

    # 工作流分支：写操作完成后同步远程图标并构建本地产物。
    if args.command == "create-sync":
        return create_sync(
            args.project,
            args.project_id,
            svg=args.svg,
            svg_dir=args.svg_dir,
            keep_fill=args.keep_fill,
            confirm=args.confirm,
        )

    if args.command == "update-sync":
        return update_sync(
            args.project,
            args.project_id,
            name=args.name,
            unicode=args.unicode,
            font_class=args.font_class,
            new_name=args.new_name,
            new_font_class=args.new_font_class,
            keep_fill=args.keep_fill,
            confirm=args.confirm,
        )

    if args.command == "delete-sync":
        return delete_sync(
            args.project,
            args.project_id,
            ids=args.id,
            names=args.name,
            unicodes=args.unicode,
            all_icons=args.all,
            confirm=args.confirm,
            yes_i_know=args.yes_i_know,
        )

    raise ValueError(f"未知命令: {args.command}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        print_json(run(args))
        return 0
    except (IconfontAuthError, IconfontConfigError, ValueError) as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"执行失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
