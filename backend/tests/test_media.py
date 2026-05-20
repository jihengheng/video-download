from fastapi import HTTPException

from app.services.media import InspectorService, YtDlpMediaService, platform_from_url, validate_public_url


def test_validate_public_url_accepts_https() -> None:
    validate_public_url("https://example.com/watch?v=123")


def test_validate_public_url_rejects_private_host() -> None:
    try:
        validate_public_url("http://localhost/video")
    except HTTPException as exc:
        assert exc.status_code == 400
        assert "不支持内网、本地或私有地址" in exc.detail
    else:
        raise AssertionError("Expected HTTPException for private host")


def test_platform_from_url_maps_common_hosts() -> None:
    assert platform_from_url("https://www.youtube.com/watch?v=abc") == "youtube"
    assert platform_from_url("https://vimeo.com/12345") == "vimeo"


def test_inspector_returns_formats(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.media.YtDlpMediaService.extract_info",
        lambda self, url, download=False, format_id=None, output_dir=None: {
            "title": "Sample",
            "thumbnail": "https://cdn.example.com/thumb.jpg",
            "duration": 123,
            "extractor_key": "YouTube",
            "subtitles": {"en": [{"url": "https://example.com/sub.vtt", "ext": "vtt"}]},
            "formats": [
                {"format_id": "18", "ext": "mp4", "width": 640, "height": 360, "filesize": 5 * 1024 * 1024, "format_note": "360p"},
                {"format_id": "140", "ext": "m4a", "vcodec": "none", "filesize": 1 * 1024 * 1024, "format_note": "audio"},
            ],
        },
    )
    payload = InspectorService().inspect("https://www.youtube.com/watch?v=abc")
    assert payload["source_platform"] == "youtube"
    assert payload["title"] == "Sample"
    assert len(payload["formats"]) == 2
    assert payload["supports_summary"] is True


def test_inspector_normalizes_http_thumbnail_url(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.media.YtDlpMediaService.extract_info",
        lambda self, url, download=False, format_id=None, output_dir=None: {
            "title": "Bilibili Sample",
            "thumbnail": "http://i0.hdslb.com/bfs/archive/demo.jpg",
            "duration": 2450.007,
            "extractor_key": "BiliBili",
            "formats": [
                {"format_id": "30016", "ext": "mp4", "width": 640, "height": 360, "filesize": 5 * 1024 * 1024},
            ],
        },
    )

    payload = InspectorService().inspect("https://www.bilibili.com/video/BV1Nd596vEyU/")

    assert payload["thumbnail_url"] == "https://i0.hdslb.com/bfs/archive/demo.jpg"
    assert payload["duration_seconds"] == 2450


def test_download_selector_merges_video_with_best_audio() -> None:
    selector = YtDlpMediaService()._build_download_format_selector("30016")
    assert selector == "30016+bestaudio/30016/best"
