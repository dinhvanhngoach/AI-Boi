import asyncio
import random
import os
import tempfile
from config import TTS_ENGINE, EDGE_VOICES, DEFAULT_VOICE, ELEVENLABS_API_KEY


async def speak(text: str, voice_key: str = None, big_gift: bool = False) -> bytes:
    """
    Chuyển văn bản thành giọng nói. Trả về bytes audio (mp3).
    - voice_key: key trong EDGE_VOICES, None = dùng mặc định hoặc random
    - big_gift: True → dùng giọng đặc biệt cho quà lớn
    """
    if voice_key is None:
        # Quà lớn → random giọng để tạo hiệu ứng bất ngờ
        voice_key = random.choice(list(EDGE_VOICES.keys())) if big_gift else DEFAULT_VOICE

    engine = TTS_ENGINE.lower()

    if engine == "edge":
        return await _edge_tts(text, voice_key)
    elif engine == "elevenlabs":
        return await _elevenlabs_tts(text)
    elif engine == "google":
        return await _google_tts(text)
    else:
        return await _edge_tts(text, voice_key)


async def _edge_tts(text: str, voice_key: str) -> bytes:
    """Edge TTS - miễn phí, không cần API key, hỗ trợ tiếng Việt tốt."""
    try:
        import edge_tts
        voice = EDGE_VOICES.get(voice_key, EDGE_VOICES[DEFAULT_VOICE])
        communicate = edge_tts.Communicate(text, voice)
        audio_bytes = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes += chunk["data"]
        return audio_bytes
    except ImportError:
        print("[TTS] Chưa cài edge-tts. Chạy: pip install edge-tts")
        return b""
    except Exception as e:
        print(f"[Edge TTS] Lỗi: {e}")
        return b""


async def _elevenlabs_tts(text: str) -> bytes:
    """ElevenLabs TTS - chất lượng cao, cần API key."""
    if not ELEVENLABS_API_KEY:
        print("[TTS] Chưa có ElevenLabs API key, chuyển sang Edge TTS")
        return await _edge_tts(text, DEFAULT_VOICE)
    try:
        import httpx
        # Voice mặc định: Rachel (nữ, nhẹ nhàng)
        voice_id = "21m00Tcm4TlvDq8ikWAM"
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.content
    except Exception as e:
        print(f"[ElevenLabs] Lỗi: {e}, chuyển sang Edge TTS")
        return await _edge_tts(text, DEFAULT_VOICE)


async def _google_tts(text: str) -> bytes:
    """Google Cloud TTS - cần cài google-cloud-texttospeech và service account."""
    try:
        from google.cloud import texttospeech
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="vi-VN",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        return response.audio_content
    except Exception as e:
        print(f"[Google TTS] Lỗi: {e}, chuyển sang Edge TTS")
        return await _edge_tts(text, DEFAULT_VOICE)


async def save_audio_file(audio_bytes: bytes, filename: str = None) -> str:
    """Lưu audio bytes ra file tạm, trả về đường dẫn."""
    if not audio_bytes:
        return ""
    if filename:
        path = os.path.join(tempfile.gettempdir(), filename)
    else:
        fd, path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
    with open(path, "wb") as f:
        f.write(audio_bytes)
    return path
