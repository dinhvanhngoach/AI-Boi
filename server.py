import asyncio
import base64
import os
import tempfile
import sys
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from contextlib import asynccontextmanager

from tiktok_handler import start_tiktok_client, idle_broadcaster, current_display, stats
from tts import speak

# ─── Hàng đợi ưu tiên: gift(0) > comment(1) > join(2) > idle(3) ───────────────
PRIORITY_MAP = {"gift": 0, "comment": 1, "join": 2, "idle": 3}


class PriorityQueue:
    """Hàng đợi ưu tiên: quà luôn được xử lý trước comment thường."""

    def __init__(self):
        self._queues = {p: asyncio.Queue() for p in range(4)}

    async def put(self, item: dict):
        p = PRIORITY_MAP.get(item.get("type", "idle"), 3)
        await self._queues[p].put(item)

    async def get(self) -> dict:
        while True:
            for p in sorted(self._queues):
                if not self._queues[p].empty():
                    return await self._queues[p].get()
            await asyncio.sleep(0.1)

    def empty(self) -> bool:
        return all(q.empty() for q in self._queues.values())

    def qsize(self) -> int:
        return sum(q.qsize() for q in self._queues.values())


# ─── Biến toàn cục ─────────────────────────────────────────────────────────────
event_queue = PriorityQueue()
websocket_clients: list[WebSocket] = []


async def play_audio_system(audio_bytes: bytes):
    """
    Phát audio ra loa hệ thống bằng pygame.
    Trên Railway/server không có màn hình → bỏ qua, chỉ phát qua WebSocket.
    Khi chạy local: pygame phát ra loa → Stereo Mix capture vào stream.
    """
    if not audio_bytes:
        return
    # Kiểm tra có đang chạy local không (có display/audio device)
    if os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("RENDER"):
        # Đang trên cloud → không phát local audio, chỉ dùng WebSocket
        return

    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        with open(path, "wb") as f:
            f.write(audio_bytes)
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.05)
        except ImportError:
            if sys.platform == "win32":
                script = (
                    f"Add-Type -AssemblyName presentationCore;"
                    f"$mp = New-Object System.Windows.Media.MediaPlayer;"
                    f"$mp.Open('{path}');"
                    f"$mp.Play();"
                    f"Start-Sleep -Seconds 10;"
                    f"$mp.Close()"
                )
                proc = await asyncio.create_subprocess_exec(
                    "powershell", "-NoProfile", "-c", script,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await proc.wait()
    except Exception as e:
        print(f"[Audio System] Lỗi: {e}")
    finally:
        await asyncio.sleep(0.5)
        try:
            os.remove(path)
        except Exception:
            pass


async def broadcast(data: dict):
    """Gửi dữ liệu tới tất cả client WebSocket (OBS browser source / trình duyệt)."""
    dead = []
    for ws in websocket_clients:
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        websocket_clients.remove(ws)


async def process_queue():
    """Vòng lặp chính: lấy sự kiện → tạo TTS → phát âm thanh + cập nhật UI."""
    while True:
        item = await event_queue.get()
        try:
            # Cập nhật trạng thái hiển thị
            current_display.update({
                "username":    item["username"],
                "mole_number": item["mole_number"],
                "prediction":  item["text"],
                "event_type":  item["type"],
                "gift_name":   item["gift_name"],
                "is_big_gift": item["is_big_gift"],
            })

            # Tạo audio TTS
            audio_bytes = await speak(
                item["text"],
                voice_key=item.get("voice_key"),
                big_gift=item.get("is_big_gift", False),
            )

            audio_b64 = base64.b64encode(audio_bytes).decode() if audio_bytes else ""

            # Gửi UI update tới browser (hiển thị text + highlight nốt ruồi)
            await broadcast({
                "type":        item["type"],
                "username":    item["username"],
                "mole_number": item["mole_number"],
                "prediction":  item["text"],
                "gift_name":   item["gift_name"],
                "is_big_gift": item["is_big_gift"],
                "audio_b64":   audio_b64,  # Browser cũng phát (dự phòng)
            })

            # Phát âm thanh ra loa hệ thống → vào stream qua Stereo Mix / Virtual Cable
            await play_audio_system(audio_bytes)

        except Exception as e:
            print(f"[Queue Processor] Lỗi: {e}")
            await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Khởi động các background task khi server bắt đầu."""
    asyncio.create_task(start_tiktok_client(event_queue))
    asyncio.create_task(idle_broadcaster(event_queue))
    asyncio.create_task(process_queue())
    yield


app = FastAPI(title="TikTok Bói Nốt Ruồi AI", lifespan=lifespan)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_clients.append(websocket)
    print(f"[WebSocket] Client kết nối. Tổng: {len(websocket_clients)}")
    try:
        await websocket.send_json({
            "type":        "init",
            "username":    current_display["username"],
            "mole_number": current_display["mole_number"],
            "prediction":  current_display["prediction"],
            "event_type":  current_display["event_type"],
        })
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)
        print(f"[WebSocket] Client ngắt kết nối. Tổng: {len(websocket_clients)}")


@app.get("/api/stats")
async def get_stats():
    return JSONResponse({**stats, "queue_size": event_queue.qsize(), "ws_clients": len(websocket_clients)})


@app.get("/api/status")
async def get_status():
    return JSONResponse(current_display)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
