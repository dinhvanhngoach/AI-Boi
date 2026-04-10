import asyncio
import random
import os
import tempfile
from config import TTS_ENGINE, EDGE_VOICES, DEFAULT_VOICE, ELEVENLABS_API_KEY

async def speak(text: str, voice_key: str = None, big_gift: bool = False) -> bytes:
    """
    Chuyển văn bản thành giọng nói. Trả về bytes audio (mp3).
    Thứ tự ưu tiên: ElevenLabs → gTTS → Edge TTS
    """
    if voice_key is None:
        voice_key = random.choice(list(EDGE_VOICES.keys())) if big_gift else DEFAULT_VOICE

    engine = TTS_ENGINE.lower()

    if engine == "elevenlabs":
        return await _elevenlabs_tts(text)
    elif engine == "google":
        return await _google_tts(text)
    elif engine == "gtts":
        return await _gtts(text)
    else:
        # Mặc định: thử gTTS trước (ổn định hơn trên server), fallback Edge TTS
        result = await _gtts(text)
        if result:
            return result
        return await _edge_tts(text, voice_key)


async def _gtts(text: str) -> bytes:
    """gTTS - dùng HTTP thông thường, hoạt động tốt trên server/Railway."""
    try:
        from gtts import gTTS
        import io
        # Chạy trong thread pool để không block event loop
        loop = asyncio.get_event_loop()
        def _gen():
            tts = gTTS(text=text, lang='vi', slow=False)
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            return buf.getvalue()
        audio_bytes = await loop.run_in_executor(None, _gen)
        return audio_bytes
    except ImportError:
        print("[TTS] Chưa cài gTTS. Chạy: pip install gTTS")
        return b""
    except Exception as e:
        print(f"[gTTS] Lỗi: {e}")
        return b""


async def _edge_tts(text: str, voice_key: str) -> bytes:
    """Edge TTS - miễn phí, không cần API key, hỗ trợ tiếng Việt tốt."""
    try:
        import edge_tts
        import re

        # Chỉ bỏ emoji, giữ nguyên tiếng Việt
        import unicodedata
        clean = ''.join(
            c for c in text
            if unicodedata.category(c) not in ('So', 'Sm', 'Sk', 'Sc')
            and ord(c) < 0x1F600 or ord(c) > 0x1F9FF
        ).strip()
        clean = re.sub(r'\s+', ' ', clean).strip()
        if len(clean) < 3:
            clean = "Xin chào các bạn"

        print(f"[Edge TTS] Clean: '{clean[:80]}'")
        voice = EDGE_VOICES.get(voice_key, EDGE_VOICES[DEFAULT_VOICE])
        print(f"[Edge TTS] Voice: {voice}")

        # Thử tối đa 3 lần
        for attempt in range(3):
            try:
                communicate = edge_tts.Communicate(clean, voice)
                audio_bytes = b""
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_bytes += chunk["data"]
                if audio_bytes:
                    return audio_bytes
                print(f"[Edge TTS] Lần {attempt+1}: không nhận được audio, thử lại...")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"[Edge TTS] Lần {attempt+1} lỗi: {e}")
                await asyncio.sleep(1)

        print("[Edge TTS] Thất bại sau 3 lần thử")
        return b""
    except ImportError:
        print("[TTS] Chưa cài edge-tts. Chạy: pip install edge-tts")
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
