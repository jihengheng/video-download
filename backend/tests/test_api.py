from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthcheck() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_login_and_create_task_flow(db_session, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.media.YtDlpMediaService.extract_info",
        lambda self, url, download=False, format_id=None, output_dir=None: {
            "id": "abc123def45",
            "title": "Demo video",
            "thumbnail": "https://cdn.example.com/thumb.jpg",
            "duration": 120,
            "extractor_key": "YouTube",
            "formats": [{"format_id": "18", "ext": "mp4", "width": 640, "height": 360, "filesize": 5 * 1024 * 1024}],
        },
    )
    monkeypatch.setattr(
        "app.services.tasks.TaskPipeline.process_task",
        lambda self, db, task_id: _mock_complete_task(db, task_id),
    )
    register_response = client.post(
        "/api/auth/register",
        json={"email": "demo@example.com", "password": "password123"},
    )
    assert register_response.status_code == 201
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    inspect_response = client.post("/api/video/inspect", json={"url": "https://www.youtube.com/watch?v=abc"}, headers=headers)
    assert inspect_response.status_code == 200
    task_response = client.post(
        "/api/tasks",
        json={"url": "https://www.youtube.com/watch?v=abc", "format_id": "mp4-720p", "need_summary": True},
        headers=headers,
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]

    result_response = client.get(f"/api/tasks/{task_id}/result", headers=headers)
    assert result_response.status_code == 200
    payload = result_response.json()
    assert payload["task_id"] == task_id
    assert payload["summary"]


def test_anonymous_task_result_flow(db_session, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.media.YtDlpMediaService.extract_info",
        lambda self, url, download=False, format_id=None, output_dir=None: {
            "id": "guest123def4",
            "title": "Guest video",
            "thumbnail": None,
            "duration": 90,
            "extractor_key": "YouTube",
            "formats": [{"format_id": "18", "ext": "mp4", "width": 640, "height": 360}],
        },
    )
    monkeypatch.setattr(
        "app.services.tasks.TaskPipeline.process_task",
        lambda self, db, task_id: _mock_complete_task(db, task_id),
    )
    task_response = client.post(
        "/api/tasks",
        json={"url": "https://www.youtube.com/watch?v=guest", "format_id": "mp4-720p", "need_summary": True},
    )
    assert task_response.status_code == 201
    payload = task_response.json()
    task_id = payload["id"]
    public_token = payload["public_token"]

    detail_response = client.get(f"/api/tasks/{task_id}", params={"access_token": public_token})
    assert detail_response.status_code == 200

    result_response = client.get(f"/api/tasks/{task_id}/result", params={"access_token": public_token})
    assert result_response.status_code == 200


def test_direct_download_returns_file_response(db_session, monkeypatch, tmp_path) -> None:
    video_file = tmp_path / "direct-demo.mp4"
    video_file.write_bytes(b"demo-video")

    monkeypatch.setattr(
        "app.services.media.YtDlpMediaService.download_selected_format",
        lambda self, url, format_id, output_dir: (
            {"title": "Direct demo", "extractor_key": "BiliBili"},
            video_file,
        ),
    )

    response = client.post(
        "/api/video/download",
        json={"url": "https://www.bilibili.com/video/BV1Nd596vEyU/", "format_id": "30016"},
    )

    assert response.status_code == 200
    assert response.content == b"demo-video"
    assert "attachment" in response.headers["content-disposition"].lower()


def _mock_complete_task(db, task_id: int):
    from app.repos.tasks import add_artifact, get_task, save_summary, save_transcript

    task = get_task(db, task_id)
    assert task is not None
    save_transcript(
        db,
        task,
        "en",
        "Transcript text",
        [{"start": 0, "end": 5, "text": "Transcript text"}],
    )
    save_summary(
        db,
        task,
        "Short summary",
        ["Point 1"],
        [{"time": "00:00", "label": "Start", "description": "Transcript text"}],
        "Suggested title",
        ["research"],
    )
    add_artifact(db, task, "notes", f"tasks/{task.id}/notes/summary.md", "text/markdown", 42)
    task.status = "completed"
    task.progress = 100
    db.add(task)
    db.commit()
    db.refresh(task)
    return task
