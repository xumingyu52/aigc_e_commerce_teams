import os

import requests
from flask import Flask, Response, jsonify, request, send_file
from flask_cors import CORS
from gevent import pywsgi
from scheduler.thread_manager import MyThread

app = Flask(__name__)
app.config["DEBUG"] = True
CORS(app, supports_credentials=True)
MAIN_API_BASE_URL = os.environ.get("MAIN_API_BASE_URL", "http://127.0.0.1:5000")


def _proxy_to_main_api(target_path, *, stream=False):
    target_url = f"{MAIN_API_BASE_URL}{target_path}"
    headers = {}
    content_type = request.headers.get("Content-Type")
    if content_type:
        headers["Content-Type"] = content_type
    accept = request.headers.get("Accept")
    if accept:
        headers["Accept"] = accept

    try:
        upstream = requests.request(
            method=request.method,
            url=target_url,
            params=request.args,
            data=request.get_data(),
            headers=headers,
            cookies=request.cookies,
            stream=stream,
            timeout=300 if stream else 120,
        )
    except requests.RequestException as exc:
        return jsonify({"error": f"main api unavailable: {exc}"}), 502

    excluded_headers = {"content-encoding", "transfer-encoding", "connection"}
    response_headers = [
        (name, value)
        for name, value in upstream.headers.items()
        if name.lower() not in excluded_headers
    ]

    if stream:
        return Response(
            upstream.iter_content(chunk_size=8192),
            status=upstream.status_code,
            headers=response_headers,
        )

    return Response(
        upstream.content,
        status=upstream.status_code,
        headers=response_headers,
    )


@app.errorhandler(Exception)
def handle_exception(error):
    return jsonify({"status": "error", "error": str(error)}), 500


@app.route("/")
def index():
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
    return jsonify({"status": "ok", "service": "flask_shell", "frontend_url": frontend_url})


@app.route("/api/submit", methods=["post"])
def api_submit():
    return _proxy_to_main_api("/api/submit")


@app.route("/api/get-data", methods=["post"])
def api_get_data():
    return _proxy_to_main_api("/api/get-data")


@app.route("/api/start-live", methods=["post"])
def api_start_live():
    return _proxy_to_main_api("/api/start-live")


@app.route("/api/stop-live", methods=["post"])
def api_stop_live():
    return _proxy_to_main_api("/api/stop-live")


@app.route("/api/send", methods=["post"])
def api_send():
    return _proxy_to_main_api("/api/chat")


@app.route("/api/get-msg", methods=["post"])
def api_get_msg():
    return _proxy_to_main_api("/api/get-msg")


@app.route("/v1/chat/completions", methods=["post"])
@app.route("/api/send/v1/chat/completions", methods=["post"])
def api_send_v1_chat_completions():
    return _proxy_to_main_api(request.path)


@app.route("/api/get-member-list", methods=["post"])
def api_get_member_list():
    return _proxy_to_main_api("/api/get-member-list")


@app.route("/audio/<filename>")
def serve_audio(filename):
    audio_file = os.path.join(os.getcwd(), "samples", filename)
    return send_file(audio_file)


@app.route("/robot/<filename>")
def serve_gif(filename):
    gif_file = os.path.join(os.getcwd(), "gui", "robot", filename)
    return send_file(gif_file)


def run():
    server = pywsgi.WSGIServer(("0.0.0.0", 6000), app)
    server.serve_forever()


def start():
    MyThread(target=run).start()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000, debug=True)
