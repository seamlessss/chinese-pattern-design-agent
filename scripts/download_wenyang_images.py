"""安全下载 Wényàng 正式卡片图：固定修订、原子写入、SHA-256 校验、可续传。"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data" / "raw" / "wenyang"
METADATA = RAW_ROOT / "data" / "patterns.json"
REPORT = ROOT / "data" / "processed" / "wenyang_image_download.json"
REVISION = "64dccd203a5cde5514eeda1096052c7b9bb69663"
BASE_URL = f"https://raw.githubusercontent.com/dososo/chinese-traditional-patterns/{REVISION}/"
CONTENT_LICENSE = RAW_ROOT / "LICENSE-CONTENT.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def encoded_url(relative_path: str) -> str:
    return BASE_URL + "/".join(quote(part, safe="") for part in PurePosixPath(relative_path).parts)


def download_all(*, timeout: int = 90, retries: int = 4, limit: int | None = None) -> dict:
    if not METADATA.is_file() or not CONTENT_LICENSE.is_file():
        raise FileNotFoundError("下载前必须保留上游 patterns.json 和 LICENSE-CONTENT.md")
    records = json.loads(METADATA.read_text(encoding="utf-8"))
    if limit is not None:
        records = records[:limit]
    free_before = shutil.disk_usage(ROOT).free
    # 上游树审计为 242.47 MiB；预留其两倍，容纳临时文件和安全余量。
    required_free = 512 * 1024 * 1024
    if free_before < required_free:
        raise OSError(f"磁盘剩余 {free_before} bytes，不足安全阈值 {required_free} bytes")

    session = requests.Session()
    session.headers["User-Agent"] = "WenyangCourseProject/1.0 (non-commercial educational use)"
    downloaded, existing, failures = [], [], []
    started = datetime.now(timezone.utc).isoformat()
    for number, record in enumerate(records, 1):
        relative = str(record["card_image"])
        expected = str(record["image_sha256"]).lower()
        target = RAW_ROOT.joinpath(*PurePosixPath(relative).parts)
        if target.is_file() and sha256(target) == expected:
            existing.append(relative)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        part = target.with_suffix(target.suffix + ".part")
        error = ""
        for attempt in range(1, retries + 1):
            try:
                with session.get(encoded_url(relative), timeout=(20, timeout), stream=True) as response:
                    response.raise_for_status()
                    with part.open("wb") as stream:
                        for chunk in response.iter_content(1024 * 1024):
                            if chunk:
                                stream.write(chunk)
                actual = sha256(part)
                if actual != expected:
                    raise ValueError(f"SHA-256 不一致：期望 {expected}，实际 {actual}")
                part.replace(target)
                downloaded.append(relative)
                error = ""
                break
            except (requests.RequestException, OSError, ValueError) as exc:
                error = f"{type(exc).__name__}: {exc}"
                if part.exists():
                    part.unlink()
                if attempt < retries:
                    time.sleep(min(2**attempt, 8))
        if error:
            failures.append({"path": relative, "error": error})
        print(f"[{number:03}/{len(records):03}] downloaded={len(downloaded)} existing={len(existing)} failed={len(failures)}", flush=True)

    valid = 0
    invalid = []
    for record in records:
        relative = str(record["card_image"])
        target = RAW_ROOT.joinpath(*PurePosixPath(relative).parts)
        if target.is_file() and sha256(target) == str(record["image_sha256"]).lower():
            valid += 1
        elif target.is_file():
            invalid.append(relative)
    report = {
        "source": "https://github.com/dososo/chinese-traditional-patterns",
        "revision": REVISION,
        "license": "CC BY-NC 4.0",
        "started_at_utc": started,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "requested": len(records),
        "downloaded_this_run": len(downloaded),
        "already_valid": len(existing),
        "valid_after_run": valid,
        "invalid_after_run": invalid,
        "failures": failures,
        "free_bytes_before": free_before,
        "free_bytes_after": shutil.disk_usage(ROOT).free,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="仅下载前 N 张，用于连通性测试")
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--retries", type=int, default=4)
    args = parser.parse_args()
    report = download_all(timeout=args.timeout, retries=args.retries, limit=args.limit)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["failures"] or report["invalid_after_run"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
