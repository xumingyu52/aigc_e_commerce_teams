import json
import os
import time
import threading
from pathlib import Path

from flask import jsonify, send_file

import avatar_runtime
from backend.adapters.asr.qwen3_adapter import qwen3_asr_adapter
from backend.config import runtime_config
from backend.schemas.live_dto import ChatCompletionRequest, ChatRequest, HistoryRequest
from core import content_db, member_db, wsa_server
from core.interact import Interact
from scheduler.thread_manager import MyThread
from tts import qwen3, tts_voice, volcano_tts


class LiveService:
    """Live2D-oriented service chain with a deliberately short call path."""

    def __init__(self):
        self._voice_lock = threading.RLock()
        self._voice_list = None

    def _get_voice_list(self, force_reload: bool = False):
        with self._voice_lock:
            if self._voice_list is None or force_reload:
                runtime_config.reload_runtime_config()
                try:
                    self._voice_list = tts_voice.merge_voice_options(
                        tts_voice.get_builtin_voice_options(),
                        tts_voice.get_ali_voice_options(),
                        volcano_tts.get_volcano_voices(),
                        qwen3.get_qwen_voices(),
                    )
                except Exception:
                    self._voice_list = tts_voice.get_builtin_voice_options()
            return [voice.copy() for voice in self._voice_list]

    def _ensure_runtime(self):
        web = wsa_server.new_web_instance(port=10003)
        if not web.is_running():
            web.start_server()
        human = wsa_server.new_instance(port=10004)
        if not human.is_running():
            human.start_server()
        if not avatar_runtime.is_running() or avatar_runtime.get_instance() is None:
            return avatar_runtime.start()
        return avatar_runtime.get_instance()

    def _broadcast_live_state(self, state: int):
        web = wsa_server.get_web_instance()
        if web and web.is_running():
            web.add_cmd({"liveState": state})

    def get_runtime_payload(self):
        config = runtime_config.reload_runtime_config()
        voices = self._get_voice_list(force_reload=True)
        return {"config": config, "voice_list": voices}

    def save_runtime_payload(self, request_data):
        data = request_data.values.get("data")
        config_data = json.loads(data) if data else request_data.get_json(force=True)
        cfg = config_data.get("config", config_data)
        runtime_config.save_runtime_config(cfg)
        self._get_voice_list(force_reload=True)
        return {"result": "successful"}

    def start_live(self):
        runtime_config.reload_runtime_config()
        self._ensure_runtime()
        self._broadcast_live_state(1)
        return {"result": "successful"}

    def stop_live(self):
        if avatar_runtime.is_running():
            avatar_runtime.stop()
        self._broadcast_live_state(0)
        return {"result": "successful"}

    def get_message_history(self, request_data):
        raw_data = request_data.form.get("data")
        if not raw_data:
            return {"list": []}

        try:
            payload = json.loads(raw_data)
        except Exception:
            return {"list": []}

        dto = HistoryRequest.from_payload(payload)
        uid = member_db.new_instance().find_user(dto.username)
        if uid == 0:
            return {"list": []}

        rows = content_db.new_instance().get_list("all", "desc", 1000, uid)
        result = [
            {
                "type": row[0],
                "way": row[1],
                "content": row[2],
                "createtime": row[3],
                "timetext": row[4],
                "username": row[5],
            }
            for row in reversed(rows)
        ]
        return {"list": result}

    def get_member_list(self):
        users = member_db.new_instance().get_all_users()
        return {"list": [{"uid": row[0], "username": row[1]} for row in users]}

    def submit_chat(self, payload):
        dto = ChatRequest.from_payload(payload)
        if not dto.text:
            return {"error": "Empty text"}, 400

        avatar = self._ensure_runtime()
        interact = Interact("text", 1, {"user": dto.user, "msg": dto.text})
        MyThread(target=avatar.on_interact, args=[interact]).start()
        return {"status": "success", "message": "Interaction started"}, 200

    def transcribe_audio(self, upload):
        if upload is None or upload.filename == "":
            return {"error": "Missing audio file"}, 400
        try:
            return qwen3_asr_adapter.transcribe_upload(upload)
        except Exception as exc:
            return {"error": f"Audio conversion failed: {exc}"}, 400

    def serve_audio_file(self, filename):
        audio_dir = os.path.join(os.getcwd(), "samples")
        audio_path = os.path.join(audio_dir, filename)
        if not os.path.isfile(audio_path):
            return jsonify({"error": "Audio file not found"}), 404
        return send_file(audio_path)

    def get_latest_audio(self, since: int | None):
        samples_dir = Path(os.getcwd()) / "samples"
        if not samples_dir.exists():
            return {"audio": None}

        candidates = [path for path in samples_dir.glob("sample-*.wav") if path.is_file()]
        if since is not None:
            candidates = [path for path in candidates if int(path.stat().st_mtime * 1000) >= since]
        if not candidates:
            return {"audio": None}

        latest = max(candidates, key=lambda path: path.stat().st_mtime)
        mtime_ms = int(latest.stat().st_mtime * 1000)
        return {
            "audio": {
                "filename": latest.name,
                "mtime_ms": mtime_ms,
                "url": f"/audio/{latest.name}",
            }
        }

    def get_ws_status(self):
        ui = wsa_server.get_web_instance()
        human = wsa_server.get_instance()
        return {
            "ui_server_running": bool(ui is not None and ui.is_running()),
            "human_server_running": bool(human is not None and human.is_running()),
            "human_client_connected": bool(human.isConnect if human else False),
        }

    def create_chat_completion(self, payload):
        dto = ChatCompletionRequest.from_payload(payload)
        avatar = self._ensure_runtime()
        interact = Interact("text", 1, {"user": dto.username, "msg": dto.prompt})
        resp = avatar.on_interact(interact)
        resp_text = "" if resp is None else str(resp)
        return {
            "id": "chatcmpl-local",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": dto.model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": resp_text},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": len(dto.prompt or ""),
                "completion_tokens": len(resp_text),
                "total_tokens": len(dto.prompt or "") + len(resp_text),
            },
        }


live_service = LiveService()
