import json
import mimetypes
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

from env import IconfontAuthError, get_ctoken, load_cookie
from auth import refresh_cookie_from_credentials


BASE_URL = "https://www.iconfont.cn"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


class IconfontApiError(RuntimeError):
    """Iconfont 接口请求失败。"""


def _headers(cookie: str, referer: str = "") -> Dict[str, str]:
    return {
        "Cookie": cookie,
        "User-Agent": USER_AGENT,
        "Referer": referer or f"{BASE_URL}/",
        "X-Requested-With": "XMLHttpRequest",
    }


def _with_common_params(params: Dict[str, Any], cookie: str) -> Dict[str, Any]:
    merged = dict(params)
    merged.setdefault("t", int(time.time() * 1000))
    merged.setdefault("ctoken", get_ctoken(cookie))
    return merged


def _encode_form(params: Dict[str, Any]) -> bytes:
    encoded = {}
    for key, value in params.items():
        if isinstance(value, (dict, list)):
            encoded[key] = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        elif isinstance(value, bool):
            encoded[key] = "true" if value else "false"
        elif value is None:
            encoded[key] = ""
        else:
            encoded[key] = str(value)
    return urllib.parse.urlencode(encoded).encode("utf-8")


def _parse_response(raw: bytes) -> Dict[str, Any]:
    text = raw.decode("utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise IconfontApiError(f"Iconfont 返回非 JSON 内容: {text[:200]}") from e

    code = data.get("code")
    message = data.get("message") or data.get("error_code") or "未知错误"
    if code == 200:
        return data

    if code == 500 and message == "LOGIN REQUIRED":
        raise IconfontAuthError(
            "Iconfont 登录态失效，请更新 scripts/.env 中的 ICONFONT_COOKIE"
        )

    raise IconfontApiError(f"Iconfont API 报错: code={code}, message={message}")


def _refresh_cookie_once() -> str:
    return refresh_cookie_from_credentials()


def request_json(
    method: str, path: str, params: Dict[str, Any] | None = None, referer: str = ""
) -> Dict[str, Any]:
    """发送 Iconfont JSON 接口请求。"""
    base_params = params or {}
    method = method.upper()
    url = f"{BASE_URL}{path}"

    for attempt in range(2):
        try:
            cookie = load_cookie()
        except IconfontAuthError:
            if attempt == 0:
                # cookie获取失败时尝试使用账号密码登录重新获取cookie
                cookie = _refresh_cookie_once()
            else:
                raise

        request_params = _with_common_params(base_params, cookie)
        headers = _headers(cookie, referer)

        if method == "GET":
            query = urllib.parse.urlencode(request_params)
            req = urllib.request.Request(
                f"{url}?{query}", headers=headers, method="GET"
            )
        else:
            headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
            req = urllib.request.Request(
                url, data=_encode_form(request_params), headers=headers, method="POST"
            )

        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                return _parse_response(res.read())
        except IconfontAuthError:
            if attempt == 0:
                _refresh_cookie_once()
                continue
            raise
        except urllib.error.HTTPError as e:
            if e.code in (401, 403) and attempt == 0:
                _refresh_cookie_once()
                continue
            if e.code in (401, 403):
                raise IconfontAuthError(
                    "Iconfont 登录态无效或权限不足，请更新 scripts/.env 中的 ICONFONT_COOKIE"
                ) from e
            raise IconfontApiError(f"HTTP 请求失败: {e.code} {e.reason}") from e
        except urllib.error.URLError as e:
            raise IconfontApiError(f"网络请求失败: {e.reason}") from e

    raise IconfontAuthError("Iconfont 登录态刷新后仍不可用，请手动更新 scripts/.env")


def _build_multipart(
    fields: Dict[str, Any], files: Iterable[Tuple[str, Path]]
) -> tuple[bytes, str]:
    boundary = f"----IconfontBoundary{int(time.time() * 1000)}"
    chunks: list[bytes] = []

    for key, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
        chunks.append(str(value).encode("utf-8"))
        chunks.append(b"\r\n")

    for field_name, file_path in files:
        file_name = file_path.name
        content_type = mimetypes.guess_type(file_name)[0] or "image/svg+xml"
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(
            f'Content-Disposition: form-data; name="{field_name}"; filename="{file_name}"\r\n'.encode()
        )
        chunks.append(f"Content-Type: {content_type}\r\n\r\n".encode())
        chunks.append(file_path.read_bytes())
        chunks.append(b"\r\n")

    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), boundary


def upload_svg(file_path: Path) -> Dict[str, Any]:
    """上传单个 SVG 到 Iconfont 临时上传区。"""
    last_error: Exception | None = None
    body, boundary = _build_multipart({}, [("icons[]", file_path)])

    for attempt in range(2):
        try:
            cookie = load_cookie()
        except IconfontAuthError:
            if attempt == 0:
                cookie = _refresh_cookie_once()
            else:
                raise

        ctoken = get_ctoken(cookie)
        url = f"{BASE_URL}/api/uploadIcons.json?ctoken={urllib.parse.quote(ctoken)}&_csrf={urllib.parse.quote(ctoken)}"
        headers = _headers(cookie, f"{BASE_URL}/icons/upload")
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=60) as res:
                return _parse_response(res.read())
        except IconfontAuthError:
            if attempt == 0:
                _refresh_cookie_once()
                continue
            raise
        except urllib.error.HTTPError as e:
            if e.code in (401, 403) and attempt == 0:
                _refresh_cookie_once()
                continue
            if e.code in (401, 403):
                raise IconfontAuthError(
                    "Iconfont 登录态无效或权限不足，请更新 scripts/.env 中的 ICONFONT_COOKIE"
                ) from e
            raise IconfontApiError(f"SVG 上传失败: {e.code} {e.reason}") from e
        except (urllib.error.URLError, ssl.SSLError) as e:
            last_error = e
            time.sleep(1)

    raise IconfontApiError(f"SVG 上传网络请求失败: {last_error}")
