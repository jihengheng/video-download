from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.models import User
from app.services.tasks import TaskPipeline


def test_task_pipeline_creates_summary_artifacts(monkeypatch, tmp_path) -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        monkeypatch.setenv("OBJECT_STORAGE_DIR", str(tmp_path / "object_store"))
        monkeypatch.setenv("WORKSPACE_DIR", str(tmp_path / "workspace"))
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai")

        video_file = tmp_path / "fixture.mp4"
        video_file.write_bytes(b"video")
        monkeypatch.setattr(
            "app.services.media.YtDlpMediaService.extract_info",
            lambda self, url, download=False, format_id=None, output_dir=None: {
                "id": "abc123",
                "title": "A public video",
                "thumbnail": None,
                "duration": 90,
                "extractor_key": "YouTube",
                "formats": [{"format_id": "18", "ext": "mp4", "width": 640, "height": 360}],
                "subtitles": {"en": [{"url": "https://example.com/sub.vtt", "ext": "vtt"}]},
            },
        )
        monkeypatch.setattr(
            "app.services.media.YtDlpMediaService.download_selected_format",
            lambda self, url, format_id, output_dir: (
                {"title": "A public video", "thumbnail": None, "duration": 90},
                video_file,
            ),
        )
        monkeypatch.setattr(
            "app.services.media.YtDlpMediaService.extract_subtitle_text",
            lambda self, info, output_dir: (
                "Transcript text",
                [{"start": 0, "end": 5, "timecode": "00:00:00,000", "text": "Transcript text"}],
            ),
        )
        monkeypatch.setattr(
            "app.services.transcription.TranscriptionService.transcribe_from_subtitles",
            lambda self, transcript_text, segments: {
                "language": "en",
                "text": transcript_text,
                "segments": segments,
            },
        )
        monkeypatch.setattr(
            "app.services.summarization.SummarizationService.summarize",
            lambda self, transcript_text, segments: {
                "summary": "Short summary",
                "key_points": ["Point 1"],
                "timeline": [{"time": "00:00", "label": "Start", "description": "Transcript text"}],
                "title_suggestion": "Suggested title",
                "tags": ["research"],
            },
        )

        user = User(email="worker@example.com", password_hash="hash", role="user", is_banned=False)
        db.add(user)
        db.commit()
        db.refresh(user)

        inspected = {
            "title": "A public video",
            "thumbnail_url": None,
            "duration_seconds": 90,
            "source_platform": "youtube",
        }
        pipeline = TaskPipeline()
        task = pipeline.create_from_inspection(
            db=db,
            user=user,
            inspected=inspected,
            url="https://www.youtube.com/watch?v=abc",
            format_id="mp4-720p",
            need_summary=True,
        )
        completed = pipeline.process_task(db, task.id)

        assert completed.status == "completed"
        assert completed.progress == 100
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
