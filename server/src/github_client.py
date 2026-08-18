import os
import base64
import json
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

GITHUB_API = "https://api.github.com"
OWNER = os.getenv("GITHUB_OWNER", "zhan-zip")
REPO = os.getenv("GITHUB_REPO", "bookkeeping")
TOKEN = os.getenv("GITHUB_TOKEN", "")

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}


def _url(path: str) -> str:
    return f"{GITHUB_API}/repos/{OWNER}/{REPO}/contents/{path}"


def get_file(path: str) -> Optional[Dict[str, Any]]:
    """获取仓库文件内容和 sha"""
    resp = requests.get(_url(path), headers=HEADERS)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return None
    content = base64.b64decode(data["content"]).decode("utf-8")
    return {
        "content": content,
        "sha": data["sha"],
        "path": data["path"],
    }


def put_file(path: str, content: str, sha: Optional[str], message: str) -> Dict[str, Any]:
    """写入文件（创建或更新），需带上 sha 防冲突"""
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
    }
    if sha:
        payload["sha"] = sha
    resp = requests.put(_url(path), headers=HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json()


def ensure_file_exists(path: str, default_content: str, message: str) -> Dict[str, Any]:
    """确保文件存在，不存在则创建"""
    existing = get_file(path)
    if existing:
        return existing
    return put_file(path, default_content, None, message)