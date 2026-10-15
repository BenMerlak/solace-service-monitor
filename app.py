from flask import Flask, jsonify, request, g, render_template
from threading import Lock
from datetime import datetime, timezone
import json
import time
import logging

app = Flask(__name__)

start_time = time.monotonic()


metrics = {
    "total_requests": 0,
    "health_checks": 0,
    "application_requests": 0,
    "failed_requests": 0
}

metrics_lock = Lock()

logging.basicConfig(
    level = logging.INFO,
    format = "%(message)s"
)

logger = logging.getLogger(__name__)


@app.before_request
def before_request():
    g.start_time = time.monotonic()


@app.after_request
def after_request(response):
    duration_ms = round(
        (time.monotonic() - g.start_time) * 1000, 2
    )

    with metrics_lock:
        metrics["total_requests"] += 1

        if request.path == "/health":
            metrics["health_checks"] += 1
        else:
            metrics["application_requests"] += 1

        if response.status_code >= 400:
            metrics["failed_requests"] += 1

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "INFO" if response.status_code < 400 else "ERROR",
        "method": request.method,
        "path": request.path,
        "status_code": response.status_code,
        "duration_ms": duration_ms    
    }

    logger.info(json.dumps(log_entry))

    return response


@app.route("/")
def home():
    return jsonify({
        "message": "Hello form Solace Platform Project!",
        "status": "running",
        "endpoints": ["/", "/health", "/status"]
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/status")
def status():
    with metrics_lock:
        current_metrics = metrics.copy()

    return jsonify({
        "service": "solace-api",
        "status": "running",
        "uptime_seconds": round(time.monotonic() - start_time, 2),
        "metrics": current_metrics
    })


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 5000)