from __future__ import annotations

import argparse
import json
import threading
import uuid
from dataclasses import asdict, dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from agent_system.controller import Controller, RunSummary
from agent_system.sessions import SessionRecorder


STATIC_DIR = Path(__file__).resolve().parent / "static"


@dataclass
class JobState:
    id: str
    task: str
    status: str = "queued"
    message: str = "Queued."
    iterations: int | None = None
    plan: str = ""
    final_code: str = ""
    review: str = ""
    success: bool | None = None
    error: str | None = None
    session_dir: str = ""
    handoff_path: str = ""
    timeline: list[dict[str, str]] = field(default_factory=list)

    def update(self, stage: str, message: str) -> None:
        self.status = stage
        self.message = message
        self.timeline.append({"stage": stage, "message": message})

    def finish(self, summary: RunSummary) -> None:
        self.plan = summary.plan
        self.final_code = summary.final_code
        self.review = summary.review
        self.success = summary.success
        self.iterations = summary.iterations_used
        self.status = "done"
        self.message = "Completed."
        self.timeline.append(
            {
                "stage": "done",
                "message": f"Completed with success={summary.success}.",
            }
        )

    def fail(self, message: str) -> None:
        self.error = message
        self.status = "failed"
        self.message = message
        self.timeline.append({"stage": "failed", "message": message})


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, JobState] = {}
        self._lock = threading.Lock()

    def create(self, task: str, iterations: int | None) -> JobState:
        job = JobState(id=uuid.uuid4().hex, task=task, iterations=iterations)
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> JobState | None:
        with self._lock:
            return self._jobs.get(job_id)

    def all(self) -> list[JobState]:
        with self._lock:
            return list(self._jobs.values())


class AgentUI:
    def __init__(self) -> None:
        self.store = JobStore()

    def submit(self, task: str, iterations: int | None) -> JobState:
        job = self.store.create(task=task, iterations=iterations)
        thread = threading.Thread(
            target=self._run_job,
            args=(job.id,),
            daemon=True,
            name=f"agent-job-{job.id[:8]}",
        )
        thread.start()
        return job

    def _run_job(self, job_id: str) -> None:
        job = self.store.get(job_id)
        if job is None:
            return

        recorder: SessionRecorder | None = None
        try:
            controller = Controller()
            recorder = SessionRecorder(
                task=job.task,
                backend=controller.settings.backend,
                fast_mode=controller.settings.fast_mode,
                iterations=job.iterations,
            )

            def on_status(stage: str, message: str) -> None:
                current = self.store.get(job_id)
                if current is not None:
                    current.update(stage, message)
                recorder.update(stage, message)

            job.update("starting", "Initializing controller.")
            summary = controller.run(
                task=job.task,
                iterations=job.iterations,
                on_status=on_status,
            )
            recorder.finish(summary)
            recorder.save_report_aliases()
            current = self.store.get(job_id)
            if current is not None:
                current.finish(summary)
                current.session_dir = str(recorder.session_dir)
                current.handoff_path = str(recorder.session_dir / "handoff.md")
        except Exception as exc:
            if recorder is not None:
                recorder.fail(str(exc))
            current = self.store.get(job_id)
            if current is not None:
                current.fail(str(exc))


APP = AgentUI()


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "AgentSystemUI/0.1"

    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            self._serve_text((STATIC_DIR / "index.html").read_text(encoding="utf-8"), "text/html; charset=utf-8")
            return
        if self.path == "/app.js":
            self._serve_text((STATIC_DIR / "app.js").read_text(encoding="utf-8"), "application/javascript; charset=utf-8")
            return
        if self.path == "/styles.css":
            self._serve_text((STATIC_DIR / "styles.css").read_text(encoding="utf-8"), "text/css; charset=utf-8")
            return
        if self.path == "/api/jobs":
            jobs = [self._serialize_job(job) for job in APP.store.all()]
            self._serve_json({"jobs": jobs})
            return
        if self.path.startswith("/api/jobs/"):
            job_id = self.path.removeprefix("/api/jobs/").strip("/")
            job = APP.store.get(job_id)
            if job is None:
                self.send_error(HTTPStatus.NOT_FOUND, "Job not found.")
                return
            self._serve_json(self._serialize_job(job))
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found.")

    def do_POST(self) -> None:
        if self.path != "/api/jobs":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found.")
            return

        payload = self._read_json()
        task = str(payload.get("task", "")).strip()
        iterations = payload.get("iterations")
        if not task:
            self.send_error(HTTPStatus.BAD_REQUEST, "Task is required.")
            return
        if iterations in ("", None):
            iterations = None
        elif not isinstance(iterations, int):
            self.send_error(HTTPStatus.BAD_REQUEST, "Iterations must be an integer.")
            return

        job = APP.submit(task=task, iterations=iterations)
        self._serve_json(self._serialize_job(job), status=HTTPStatus.ACCEPTED)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        return json.loads(raw)

    def _serve_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_text(self, body: str, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    @staticmethod
    def _serialize_job(job: JobState) -> dict[str, Any]:
        return asdict(job)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local web UI for agent_system.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host. Default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=8000, help="Bind port. Default: 8000")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    server = ThreadingHTTPServer((args.host, args.port), RequestHandler)
    print(f"Agent UI listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
