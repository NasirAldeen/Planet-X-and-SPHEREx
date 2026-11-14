"""Local and deployable web server: python server.py [--host 0.0.0.0]."""
import argparse
import json
import os
import secrets
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from waitress import serve

from planetx.archive import ROOT, build_sequence, validate_query

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 2048
PUBLIC = ROOT / "public"
pool = ThreadPoolExecutor(max_workers=2)
jobs, history = {}, {}
lock = threading.Lock()


@app.after_request
def response_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data: blob:; connect-src 'self'; object-src 'none'; base-uri 'self'")
    return response


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "Planet X · SPHEREx"}


@app.post("/api/search")
def search():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(error="Send a JSON object with ra, dec, fov and detector."), 400
    try:
        args = validate_query(body.get("ra"), body.get("dec"), body.get("fov", 6), body.get("detector", "D3"))
    except (ValueError, TypeError):
        return jsonify(error="Use RA 0–360°, Dec −90–90°, field 2–20 arcmin, and detector D1–D6."), 400
    now = time.monotonic()
    # Only use the socket address; never trust client-supplied forwarding headers.
    client = request.remote_addr
    with lock:
        for key in list(jobs):
            if jobs[key]["status"] in ("done", "error") and now - jobs[key]["updated"] > 1800:
                del jobs[key]
        for key in list(history):
            history[key] = [v for v in history[key] if now - v < 60]
            if not history[key]:
                del history[key]
        recent = history.get(client, [])
        if len(recent) >= 4 or sum(j["status"] == "running" for j in jobs.values()) >= 4:
            return jsonify(error="The archive queue is busy. Please try again in a minute."), 429
        history[client] = recent + [now]
        job_id = secrets.token_urlsafe(18)
        jobs[job_id] = {"status": "running", "message": "Waiting for archive worker…", "updated": now}
    def update(message):
        with lock:
            jobs[job_id].update(message=message, updated=time.monotonic())
    def run():
        try:
            result = build_sequence(*args, refresh=True, progress=update)
            with lock:
                jobs[job_id].update(status="done", result=result, updated=time.monotonic())
        except Exception as exc:
            app.logger.warning("Archive query failed: %s", exc)
            with lock:
                jobs[job_id].update(status="error", message=(str(exc) if isinstance(exc, ValueError)
                    else "IRSA could not complete this request. Try again or choose a bundled target."),
                    updated=time.monotonic())
    pool.submit(run)
    return jsonify(id=job_id), 202


@app.get("/api/jobs/<job_id>")
def job(job_id):
    with lock:
        data = jobs.get(job_id)
        if data is None:
            return jsonify(error="This search expired. Please start a new search."), 404
        return jsonify({k: v for k, v in data.items() if k != "updated"})


@app.get("/")
def index():
    return send_from_directory(PUBLIC, "index.html")


@app.get("/<path:filename>")
def static(filename):
    return send_from_directory(PUBLIC, filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    args = parser.parse_args()
    print(f"Planet X · SPHEREx running at http://{args.host}:{args.port}", flush=True)
    serve(app, host=args.host, port=args.port, threads=8)
