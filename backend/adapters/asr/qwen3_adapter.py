import io
import requests

from pydub import AudioSegment

from backend.config import runtime_config

_QWEN3_ASR_SESSION = requests.Session()


class Qwen3AsrAdapter:
    def transcribe_upload(self, upload):
        safe_name = upload.filename or "recording.webm"
        audio_data = upload.read()

        if not safe_name.lower().endswith(".wav"):
            audio = AudioSegment.from_file(io.BytesIO(audio_data))
            audio = audio.set_frame_rate(16000)
            audio = audio.set_channels(1)
            wav_buffer = io.BytesIO()
            audio.export(wav_buffer, format="wav")
            wav_buffer.seek(0)
            safe_name = (
                safe_name.rsplit(".", 1)[0] + ".wav"
                if "." in safe_name
                else safe_name + ".wav"
            )
            audio_data = wav_buffer.read()

        response = _QWEN3_ASR_SESSION.post(
            runtime_config.get_asr_url(),
            files={"file": (safe_name, audio_data, "audio/wav")},
            timeout=180,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {"error": response.text or "Invalid ASR response"}
        return payload, response.status_code


qwen3_asr_adapter = Qwen3AsrAdapter()
