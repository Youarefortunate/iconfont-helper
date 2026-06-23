import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from http.client import HTTPResponse
from typing import Dict, Iterable, List, Tuple

from env import IconfontAuthError, load_credentials, save_env_value


BASE_URL = "https://www.iconfont.cn"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
# 公钥
PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIGeMA0GCSqGSIb3DQEBAQUAA4GMADCBiAKBgGa4CR/fcRUFv2r+YdiRXBDGqi4E
0HO1Eu0FqvVJtlvXrrxXGHzul+iFR8zO1xKapNhW60pkEpB/jbXUhog7q0R54cSL
bS+4SRv80M2YAdTkaO+frP2j1LyGtNquw/W7oj0+SskEL+U6Yn1a27uHhGbl4BBf
TM9FXzxEEomKPoMRAgMBAAE=
-----END PUBLIC KEY-----"""


class IconfontLoginError(IconfontAuthError):
    """Iconfont 自动登录失败。"""


def _read_length(data: bytes, offset: int) -> Tuple[int, int]:
    length = data[offset]
    offset += 1
    if length < 0x80:
        return length, offset
    size = length & 0x7F
    return int.from_bytes(data[offset : offset + size], "big"), offset + size


def _read_tlv(data: bytes, offset: int) -> Tuple[int, bytes, int]:
    tag = data[offset]
    length, value_offset = _read_length(data, offset + 1)
    end = value_offset + length
    return tag, data[value_offset:end], end


def _read_public_key_numbers(pem: str) -> Tuple[int, int]:
    body = "".join(line for line in pem.splitlines() if "---" not in line)
    der = base64.b64decode(body)
    tag, outer, _ = _read_tlv(der, 0)
    if tag != 0x30:
        raise IconfontLoginError("Iconfont 登录公钥解析失败")

    _, _, offset = _read_tlv(outer, 0)
    tag, bit_string, _ = _read_tlv(outer, offset)
    if tag != 0x03 or not bit_string:
        raise IconfontLoginError("Iconfont 登录公钥格式异常")

    tag, rsa_sequence, _ = _read_tlv(bit_string[1:], 0)
    if tag != 0x30:
        raise IconfontLoginError("Iconfont RSA 公钥格式异常")

    tag, modulus_bytes, offset = _read_tlv(rsa_sequence, 0)
    if tag != 0x02:
        raise IconfontLoginError("Iconfont RSA modulus 解析失败")
    tag, exponent_bytes, _ = _read_tlv(rsa_sequence, offset)
    if tag != 0x02:
        raise IconfontLoginError("Iconfont RSA exponent 解析失败")

    return int.from_bytes(modulus_bytes, "big"), int.from_bytes(exponent_bytes, "big")


def encrypt_password(password: str) -> str:
    """使用 RSA 公钥加密密码。"""
    modulus, exponent = _read_public_key_numbers(PUBLIC_KEY)
    key_size = (modulus.bit_length() + 7) // 8
    message = password.encode("utf-8")
    if len(message) > key_size - 11:
        raise IconfontLoginError("Iconfont 密码过长，无法完成 RSA 加密")

    padding_length = key_size - len(message) - 3
    padding = bytearray()
    while len(padding) < padding_length:
        chunk = os.urandom(padding_length - len(padding))
        padding.extend(item for item in chunk if item != 0)

    encoded = b"\x00\x02" + bytes(padding[:padding_length]) + b"\x00" + message
    encrypted = pow(int.from_bytes(encoded, "big"), exponent, modulus)
    return base64.b64encode(encrypted.to_bytes(key_size, "big")).decode("ascii")


def build_cookie_header(set_cookie_headers: Iterable[str]) -> str:
    """将 Set-Cookie 响应头转换为后续请求可用的 Cookie 头。"""
    pairs: List[str] = []
    for header in set_cookie_headers:
        first = header.split(";", 1)[0].strip()
        if first and "=" in first:
            pairs.append(first)
    return "; ".join(pairs)


def _parse_login_response(raw: bytes) -> Dict[str, object]:
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise IconfontLoginError("Iconfont 登录接口返回非 JSON 内容") from e


def _extract_set_cookie(response: HTTPResponse) -> List[str]:
    return response.headers.get_all("Set-Cookie") or []


def refresh_cookie_from_credentials() -> str:
    """使用 .env 中的账号密码刷新 ICONFONT_COOKIE。"""
    account, password = load_credentials()
    if not account or not password:
        raise IconfontAuthError(
            "Iconfont Cookie 已失效，且未配置 ICONFONT_ACCOUNT / ICONFONT_PASSWORD，请更新 scripts/.env"
        )

    encrypted_password = encrypt_password(password)
    data = urllib.parse.urlencode(
        {"target": account, "password": encrypted_password}
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/account/login.json",
        data=data,
        headers={
            "User-Agent": USER_AGENT,
            "Referer": f"{BASE_URL}/login",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            body = res.read()
            payload = _parse_login_response(body)
            cookie = build_cookie_header(_extract_set_cookie(res))
    except urllib.error.HTTPError as e:
        raise IconfontLoginError(f"Iconfont 自动登录失败: HTTP {e.code}") from e
    except urllib.error.URLError as e:
        raise IconfontLoginError(f"Iconfont 自动登录网络失败: {e.reason}") from e

    error_code = str(payload.get("error_code") or "")
    data_obj = payload.get("data")
    if error_code:
        if re.search("baxia|captcha|verify", error_code, re.IGNORECASE):
            raise IconfontLoginError("Iconfont 自动登录触发风控或验证码，请手动登录后更新 Cookie")
        raise IconfontLoginError(f"Iconfont 自动登录失败: {error_code}")

    if not isinstance(data_obj, dict) or not data_obj.get("id") or not cookie:
        raise IconfontLoginError("Iconfont 自动登录未返回有效登录态，请手动登录后更新 Cookie")

    save_env_value("ICONFONT_COOKIE", cookie)
    return cookie
