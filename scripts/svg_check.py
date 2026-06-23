import re
from pathlib import Path
from typing import Dict, List


UNSUPPORTED_SVG_FEATURES = {
    "linearGradient": "包含线性渐变，Iconfont 字体图标上传通常不支持渐变填充",
    "radialGradient": "包含径向渐变，Iconfont 字体图标上传通常不支持渐变填充",
    "filter": "包含滤镜或阴影，Iconfont 字体图标上传通常不支持滤镜效果",
    "mask": "包含遮罩，Iconfont 字体图标上传通常不支持复杂遮罩",
    "clipPath": "包含裁剪路径，Iconfont 字体图标上传可能无法正确解析",
    "pattern": "包含图案填充，Iconfont 字体图标上传通常不支持图案填充",
    "image": "包含位图图片，Iconfont 字体图标只适合纯矢量路径",
    "use": "包含 use 引用，Iconfont 字体图标上传可能无法解析 defs 引用结构",
    "defs": "包含 defs 定义，通常意味着存在渐变、滤镜、引用或其他复杂结构",
}

URL_FILL_PATTERN = re.compile(r"(?:fill|stroke)\s*=\s*['\"]url\(#", re.IGNORECASE)
STYLE_URL_PATTERN = re.compile(r"(?:fill|stroke)\s*:\s*url\(#", re.IGNORECASE)


class SvgCompatibilityError(ValueError):
    """SVG 不适合直接上传到 Iconfont。"""


def inspect_svg_compatibility(file_path: Path) -> Dict[str, object]:
    """检查 SVG 是否包含 Iconfont 上传不稳定或不支持的特性。"""
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    issues: List[Dict[str, str]] = []

    for tag, reason in UNSUPPORTED_SVG_FEATURES.items():
        if re.search(rf"<\s*{tag}\b", content, re.IGNORECASE):
            issues.append({"feature": tag, "reason": reason})

    if URL_FILL_PATTERN.search(content) or STYLE_URL_PATTERN.search(content):
        issues.append(
            {
                "feature": "url(#...) 填充或描边",
                "reason": "包含引用型填充或描边，通常来自渐变、滤镜或 defs，Iconfont 上传容易失败",
            }
        )

    return {
        "file": str(file_path),
        "supported": not issues,
        "issues": issues,
        "suggestion": "请先将 SVG 转为纯 path、纯色 fill/stroke，移除 defs、gradient、filter、mask、use 等复杂结构后再上传。复杂彩色插画建议作为普通图片资源使用，不建议转成 Iconfont 字体图标。",
    }


def assert_svg_uploadable(file_path: Path) -> None:
    """上传前检查 SVG，不适合上传时抛出带提示的错误。"""
    result = inspect_svg_compatibility(file_path)
    if result["supported"]:
        return

    issue_text = "；".join(
        f"{item['feature']}：{item['reason']}" for item in result["issues"]
    )
    raise SvgCompatibilityError(
        f"SVG 可能无法上传到 Iconfont: {file_path}\n"
        f"检测到: {issue_text}\n"
        f"建议: {result['suggestion']}"
    )
