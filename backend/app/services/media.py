from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import HTTPException, status
import subprocess
from yt_dlp import YoutubeDL

from app.core.config import get_settings
from app.core.errors import user_error

PRIVATE_HOST_PATTERNS = [
    re.compile(r"(^|\.)localhost$"),
    re.compile(r"(^|\.)internal$"),
]


def validate_public_url(url: str) -> None:
    settings = get_settings()
    if len(url) > settings.max_url_length:
        raise user_error(status.HTTP_400_BAD_REQUEST, "链接过长，请检查后重试。")

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise user_error(status.HTTP_400_BAD_REQUEST, "当前只支持 http 或 https 链接。")
    hostname = parsed.hostname or ""
    if _is_private_host(hostname):
        raise user_error(status.HTTP_400_BAD_REQUEST, "不支持内网、本地或私有地址。")


def _is_private_host(hostname: str) -> bool:
    if hostname.startswith(("10.", "127.", "169.254.", "172.16.", "172.17.", "172.18.", "172.19.", "172.2", "192.168.")):
        return True
    return any(pattern.search(hostname) for pattern in PRIVATE_HOST_PATTERNS)


def platform_from_url(url: str) -> str:
    hostname = (urlparse(url).hostname or "").lower()
    if "youtube" in hostname or "youtu.be" in hostname:
        return "youtube"
    if "vimeo" in hostname:
        return "vimeo"
    if "bilibili" in hostname:
        return "bilibili"
    return hostname or "unknown"


class InspectorService:
    def inspect(self, url: str) -> dict:
        validate_public_url(url)
        metadata = YtDlpMediaService().extract_info(url, download=False)
        platform = metadata.get("extractor_key", platform_from_url(url)).lower()
        formats = self._build_format_options(metadata.get("formats", []))
        duration_seconds = normalize_duration_seconds(metadata.get("duration"))
        supports_summary = YtDlpMediaService().has_subtitles(metadata)
        return {
            "title": metadata.get("title") or f"Preview for {platform}",
            "thumbnail_url": normalize_thumbnail_url(metadata.get("thumbnail")),
            "duration_seconds": duration_seconds,
            "source_platform": platform,
            "supports_summary": supports_summary,
            "estimated_processing_minutes": _estimate_processing_minutes(duration_seconds),
            "formats": formats[:12],
        }

    def _build_format_options(self, formats: list[dict[str, Any]]) -> list[dict[str, Any]]:
        options: list[dict[str, Any]] = []
        seen: set[str] = set()
        for fmt in formats:
            format_id = fmt.get("format_id")
            ext = fmt.get("ext")
            if not format_id or not ext or format_id in seen:
                continue
            seen.add(format_id)
            width = fmt.get("width")
            height = fmt.get("height")
            resolution = "audio" if fmt.get("vcodec") == "none" else f"{width or '?'}x{height or '?'}"
            filesize = fmt.get("filesize") or fmt.get("filesize_approx")
            options.append(
                {
                    "format_id": format_id,
                    "ext": ext,
                    "resolution": resolution,
                    "filesize_mb": round(filesize / (1024 * 1024), 2) if filesize else None,
                    "note": fmt.get("format_note") or fmt.get("acodec") or fmt.get("vcodec"),
                    "has_video": fmt.get("vcodec") != "none",
                    "has_audio": fmt.get("acodec") != "none",
                }
            )
        return sorted(
            options,
            key=lambda item: (
                not item["has_video"],
                not item["has_audio"],
                item["resolution"] == "audio",
                -(item["filesize_mb"] or 0),
            ),
        )


class YtDlpMediaService:
    def extract_info(self, url: str, download: bool = False, format_id: str | None = None, output_dir: Path | None = None) -> dict[str, Any]:
        validate_public_url(url)
        settings = get_settings()
        options: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "socket_timeout": 30,
            "skip_download": not download,
        }
        if format_id:
            options["format"] = self._build_download_format_selector(format_id)
        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            options["paths"] = {"home": str(output_dir)}
            options["outtmpl"] = {"default": "%(title).160s [%(id)s].%(ext)s"}
            options["merge_output_format"] = "mp4"

        with YoutubeDL(options) as ydl:
            try:
                info = ydl.extract_info(url, download=download)
            except Exception as exc:  # pragma: no cover - depends on remote providers
                message = str(exc)
                if "Sign in to confirm you’re not a bot" in message or "Sign in to confirm you're not a bot" in message:
                    raise user_error(status.HTTP_400_BAD_REQUEST, "目标平台触发了风控验证，当前无法直接下载该视频。请稍后重试或更换视频链接。") from exc
                raise user_error(status.HTTP_400_BAD_REQUEST, f"视频解析失败：{message}") from exc

        duration = info.get("duration")
        if duration and duration > settings.max_video_duration_seconds:
            raise user_error(status.HTTP_400_BAD_REQUEST, "视频时长超过当前系统限制。")
        return info

    def download_selected_format(self, url: str, format_id: str, output_dir: Path) -> tuple[dict[str, Any], Path]:
        info = self.extract_info(url, download=True, format_id=format_id, output_dir=output_dir)
        requested_downloads = info.get("requested_downloads") or []
        target = None
        if requested_downloads:
            filepath = requested_downloads[0].get("filepath")
            if filepath:
                target = Path(filepath)
        if target is None:
            ext = info.get("ext", "mp4")
            target = output_dir / f"{info.get('title', 'video')} [{info.get('id', 'media')}].{ext}"
        if not target.exists():
            downloaded_files = sorted(output_dir.glob("*"), key=lambda path: path.stat().st_mtime, reverse=True)
            if downloaded_files:
                target = downloaded_files[0]
        if not target.exists():
            raise user_error(status.HTTP_500_INTERNAL_SERVER_ERROR, "视频下载完成后未找到文件，请稍后重试。")
        return info, target

    def extract_subtitle_text(self, info: dict[str, Any], output_dir: Path) -> tuple[str | None, list[dict]]:
        subtitles = info.get("subtitles") or {}
        automatic = info.get("automatic_captions") or {}
        language, entries = self._pick_subtitle_entries(subtitles) or self._pick_subtitle_entries(automatic) or (None, None)
        if not language or not entries:
            return None, []

        chosen = next((entry for entry in entries if entry.get("ext") in {"vtt", "srv3", "json3", "ttml"}), entries[0])
        subtitle_url = chosen.get("url")
        if not subtitle_url:
            return None, []

        output_dir.mkdir(parents=True, exist_ok=True)
        subtitle_path = output_dir / f"subtitle-{language}.{chosen.get('ext', 'txt')}"
        content = self._download_text(subtitle_url)
        subtitle_path.write_text(content, encoding="utf-8")
        transcript_text, segments = _subtitle_to_transcript(content)
        return transcript_text, segments

    def has_subtitles(self, info: dict[str, Any]) -> bool:
        return bool(info.get("subtitles") or info.get("automatic_captions"))

    def _build_download_format_selector(self, format_id: str) -> str:
        normalized = format_id.strip()
        if not normalized:
            return "bestvideo+bestaudio/best"
        return f"{normalized}+bestaudio/{normalized}/best"

    def _pick_subtitle_entries(self, payload: dict[str, Any]) -> tuple[str, list[dict[str, Any]]] | None:
        for preferred in ("en", "en-US", "zh-Hans", "zh-CN", "zh-Hant", "zh"):
            if preferred in payload and payload[preferred]:
                return preferred, payload[preferred]
        for language, entries in payload.items():
            if entries:
                return language, entries
        return None

    def _download_text(self, url: str) -> str:
        result = subprocess.run(
            ["curl", "-L", "--silent", "--show-error", url],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise user_error(status.HTTP_502_BAD_GATEWAY, "字幕下载失败，请稍后重试。")
        return result.stdout
def write_manifest(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _estimate_processing_minutes(duration_seconds: int | None) -> int:
    if not duration_seconds:
        return 8
    return max(3, min(60, round(duration_seconds / 120)))


def normalize_duration_seconds(duration: Any) -> int | None:
    if duration is None:
        return None
    try:
        return max(0, round(float(duration)))
    except (TypeError, ValueError):
        return None


def normalize_thumbnail_url(url: Any) -> str | None:
    if not isinstance(url, str) or not url.strip():
        return None

    normalized = url.strip()
    if normalized.startswith("//"):
        return f"https:{normalized}"
    if normalized.startswith("http://"):
        return f"https://{normalized[len('http://'):]}"
    return normalized


def _subtitle_to_transcript(content: str) -> tuple[str, list[dict]]:
    segments: list[dict] = []
    transcript_lines: list[str] = []
    blocks = re.split(r"\n\s*\n", content.strip())
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        time_line = next((line for line in lines if "-->" in line), None)
        text_lines = [line for line in lines if "-->" not in line and not line.isdigit() and not line.startswith("WEBVTT")]
        if not text_lines:
            continue
        text = " ".join(text_lines)
        transcript_lines.append(text)
        if time_line:
            start = time_line.split("-->")[0].strip().replace(".", ",")
            segments.append({"start": 0, "end": 0, "timecode": start, "text": text})
    return "\n".join(transcript_lines), segments


def ensure_workspace(task_id: int) -> Path:
    settings = get_settings()
    task_dir = settings.workspace_dir / f"task-{task_id}"
    task_dir.mkdir(parents=True, exist_ok=True)
    return task_dir
