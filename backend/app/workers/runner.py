from app.core.database import SessionLocal
from app.services.tasks import TaskPipeline


def run_task(task_id: int) -> None:
    db = SessionLocal()
    try:
        TaskPipeline().process_task(db, task_id)
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit("Worker entrypoint placeholder. Wire a real queue consumer here.")
