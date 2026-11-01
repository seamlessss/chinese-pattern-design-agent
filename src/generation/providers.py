from __future__ import annotations

import base64
import io
import os
import time
from dataclasses import dataclass
from typing import Protocol

import requests
from PIL import Image


class GenerationError(RuntimeError):
    """Safe, user-facing generation failure with no secret material."""


@dataclass(frozen=True)
class GenerationResult:
    image_bytes: bytes
    mime_type: str
    provider: str
    model: str
    size: str
    quality: str = "low"


class ImageGenerationProvider(Protocol):
    def generate(self, prompt: str, *, size: str = "1024x1024") -> GenerationResult: ...


def image_api_key(environ=None, secrets=None) -> str:
    env = os.environ if environ is None else environ
    key = str(env.get("OPENAI_API_KEY", "")).strip()
    if key:
        return key
    if secrets is not None:
        try:
            return str(secrets.get("OPENAI_API_KEY", "")).strip()
        except Exception:
            return ""
    return ""


def bailian_api_key(environ=None, secrets=None) -> str:
    """Read the Alibaba Cloud Model Studio key without persisting or logging it."""
    env = os.environ if environ is None else environ
    key = str(env.get("DASHSCOPE_API_KEY", "")).strip()
    if key:
        return key
    if secrets is not None:
        try:
            return str(secrets.get("DASHSCOPE_API_KEY", "")).strip()
        except Exception:
            return ""
    return ""


class BailianImageProvider:
    """Alibaba Cloud Model Studio (Tongyi Wanxiang) asynchronous image adapter."""

    REGIONS = {
        "beijing": "https://dashscope.aliyuncs.com/api/v1",
        "singapore": "https://dashscope-intl.aliyuncs.com/api/v1",
    }

    def __init__(
        self,
        api_key: str | None,
        model: str = "wanx-v1",
        region: str = "beijing",
        timeout: float = 120,
        poll_interval: float = 2,
        session=None,
        sleeper=None,
    ):
        self.api_key = (api_key or "").strip()
        self.model = model.strip() or "wanx-v1"
        self.region = region if region in self.REGIONS else "beijing"
        self.base_url = self.REGIONS[self.region]
        self.timeout = min(max(float(timeout), 10), 300)
        self.poll_interval = min(max(float(poll_interval), 0), 10)
        self.session = session or requests
        self.sleeper = sleeper or time.sleep

    @property
    def submit_endpoint(self) -> str:
        return f"{self.base_url}/services/aigc/text2image/image-synthesis"

    def _error(self, response, action: str) -> GenerationError:
        request_id = ""
        try:
            payload = response.json()
            request_id = payload.get("request_id", "")
            detail = payload.get("message") or payload.get("code") or ""
        except (ValueError, TypeError):
            detail = ""
        suffix = f"（Request ID: {request_id}）" if request_id else ""
        message = f"百炼{action}失败：HTTP {response.status_code}"
        if detail:
            message += f"，{detail}"
        return GenerationError(message + suffix + "。请检查密钥、模型权限、账户余额和地域配置。")

    @staticmethod
    def _png_bytes(content: bytes) -> bytes:
        if content.startswith(b"\x89PNG\r\n\x1a\n"):
            return content
        try:
            with Image.open(io.BytesIO(content)) as source:
                converted = io.BytesIO()
                source.convert("RGB").save(converted, format="PNG")
                return converted.getvalue()
        except Exception as exc:
            raise GenerationError("百炼返回的结果不是有效图片，未保存生成结果。") from exc

    def generate(self, prompt: str, *, size: str = "1024x1024") -> GenerationResult:
        if not self.api_key:
            raise GenerationError("尚未配置 DASHSCOPE_API_KEY。仍可使用本页的程序化 SVG 备用生成。")
        if not prompt.strip() or len(prompt) > 2000:
            raise GenerationError("百炼生成提示词不能为空，且不能超过 2000 个字符。")
        size_value = size.replace("x", "*")
        if size_value not in {"1024*1024", "720*1280", "1280*720"}:
            raise GenerationError("百炼当前配置不支持该图片尺寸。")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }
        try:
            response = self.session.post(
                self.submit_endpoint,
                headers=headers,
                json={
                    "model": self.model,
                    "input": {"prompt": prompt},
                    "parameters": {"style": "<auto>", "size": size_value, "n": 1},
                },
                timeout=min(self.timeout, 60),
            )
            if response.status_code >= 400:
                raise self._error(response, "任务提交")
            payload = response.json()
            task_id = (payload.get("output") or {}).get("task_id")
            if not task_id:
                raise GenerationError("百炼没有返回任务 ID，未保存生成结果。")

            deadline = time.monotonic() + self.timeout
            task_url = f"{self.base_url}/tasks/{task_id}"
            while time.monotonic() < deadline:
                poll = self.session.get(task_url, headers={"Authorization": f"Bearer {self.api_key}"}, timeout=30)
                if poll.status_code >= 400:
                    raise self._error(poll, "任务查询")
                task = poll.json()
                output = task.get("output") or {}
                status = str(output.get("task_status", "")).upper()
                if status == "SUCCEEDED":
                    results = output.get("results") or []
                    result_url = (results[0] if results else {}).get("url")
                    if not result_url:
                        raise GenerationError("百炼任务已完成，但没有返回可下载的图片地址。")
                    download = self.session.get(result_url, timeout=60)
                    if download.status_code >= 400:
                        raise GenerationError(f"百炼结果图片下载失败：HTTP {download.status_code}。")
                    return GenerationResult(
                        self._png_bytes(download.content), "image/png", "阿里云百炼 · 通义万相",
                        self.model, size, "standard",
                    )
                if status in {"FAILED", "CANCELED", "UNKNOWN"}:
                    detail = output.get("message") or output.get("code") or "任务未成功"
                    raise GenerationError(f"百炼图像生成失败：{detail}。")
                self.sleeper(self.poll_interval)
            raise GenerationError("百炼图像生成等待超时，未保存生成结果；任务可能仍在服务端处理中。")
        except GenerationError:
            raise
        except requests.Timeout as exc:
            raise GenerationError("百炼请求超时，未保存新图片，请稍后重试。") from exc
        except requests.RequestException as exc:
            raise GenerationError("无法连接阿里云百炼，请检查网络和地域配置后重试。") from exc
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise GenerationError("百炼响应格式异常，未保存生成结果。") from exc


class OpenAIImageProvider:
    """OpenAI Images API adapter. Only the explicit prompt is sent; local images are not uploaded."""

    endpoint = "https://api.openai.com/v1/images/generations"

    def __init__(self, api_key: str | None, model: str = "gpt-image-1", timeout: float = 120, quality: str = "low", session=None):
        self.api_key = (api_key or "").strip()
        self.model = model.strip() or "gpt-image-1"
        self.timeout = min(max(float(timeout), 1), 180)
        self.quality = quality if quality in {"low", "medium", "high", "auto"} else "low"
        self.session = session or requests

    def generate(self, prompt: str, *, size: str = "1024x1024") -> GenerationResult:
        if not self.api_key:
            raise GenerationError("尚未配置 OPENAI_API_KEY。可先使用本页的程序化 SVG 备用生成。")
        if not prompt.strip() or len(prompt) > 4000:
            raise GenerationError("生成提示词不能为空，且不能超过 4000 个字符。")
        if size not in {"1024x1024", "1024x1536", "1536x1024"}:
            raise GenerationError("不支持该图片尺寸。")
        try:
            response = self.session.post(
                self.endpoint,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "prompt": prompt, "size": size, "quality": self.quality, "n": 1},
                timeout=self.timeout,
            )
            if response.status_code >= 400:
                raise GenerationError(f"图像服务返回 HTTP {response.status_code}。请检查账户、配额或稍后重试。")
            payload = response.json()
            encoded = payload.get("data", [{}])[0].get("b64_json")
            if not encoded:
                raise GenerationError("图像服务没有返回可用图片数据。")
            image = base64.b64decode(encoded, validate=True)
            if not image.startswith(b"\x89PNG\r\n\x1a\n"):
                raise GenerationError("图像服务返回内容不是有效 PNG 图片。")
            return GenerationResult(image, "image/png", "OpenAI Images API", self.model, size, self.quality)
        except GenerationError:
            raise
        except requests.Timeout as exc:
            raise GenerationError("图像生成请求超时。没有保存新图片，请稍后重试。") from exc
        except requests.RequestException as exc:
            raise GenerationError("无法连接图像生成服务。请检查网络后重试。") from exc
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise GenerationError("图像服务响应格式异常，未保存生成结果。") from exc
