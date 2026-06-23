from pathlib import Path
from typing import Dict


SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR / ".env"


class IconfontAuthError(RuntimeError):
    """Iconfont 登录态缺失或失效。"""


def parse_env_text(text: str) -> Dict[str, str]:
    """解析 .env 文本中的键值配置。"""
    env: Dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def load_env() -> Dict[str, str]:
    """读取当前 skill 的 .env 配置。"""
    if not ENV_PATH.exists():
        raise IconfontAuthError(f"未找到 Cookie 配置文件，请创建并更新: {ENV_PATH}")
    return parse_env_text(ENV_PATH.read_text(encoding="utf-8"))


def set_env_value(text: str, key: str, value: str) -> str:
    """更新或追加 .env 文本中的指定键值。"""
    lines = text.splitlines()
    updated = False
    for index, raw_line in enumerate(lines):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        current_key = stripped.split("=", 1)[0].strip()
        if current_key == key:
            lines[index] = f"{key}={value}"
            updated = True
            break

    if not updated:
        lines.append(f"{key}={value}")

    return "\n".join(lines) + "\n"


def save_env_value(key: str, value: str) -> None:
    """写回 .env 中的指定键值。"""
    text = ENV_PATH.read_text(encoding="utf-8") if ENV_PATH.exists() else ""
    ENV_PATH.write_text(set_env_value(text, key, value), encoding="utf-8")


def load_cookie() -> str:
    """从当前 skill 的 .env 文件读取 Iconfont Cookie。"""
    cookie = load_env().get("ICONFONT_COOKIE", "")

    if not cookie:
        raise IconfontAuthError(
            f"ICONFONT_COOKIE 为空，请在 {ENV_PATH} 中更新登录 Cookie"
        )

    return cookie


def load_credentials() -> tuple[str, str]:
    """读取 Iconfont 账号密码，缺失时返回空字符串。"""
    env = load_env()
    return env.get("ICONFONT_ACCOUNT", ""), env.get("ICONFONT_PASSWORD", "")


def extract_cookie_value(cookie: str, name: str) -> str:
    """从 Cookie 字符串中提取指定键值。"""
    for part in cookie.split(";"):
        if "=" not in part:
            continue
        key, value = part.strip().split("=", 1)
        if key == name:
            return value
    return ""


def get_ctoken(cookie: str) -> str:
    """读取 ctoken，缺失时使用 iconfont 前端一致的 null。"""
    return extract_cookie_value(cookie, "ctoken") or "null"
