# 🔮 TikTok AI Livestream - Bói Nốt Ruồi

Hệ thống AI livestream TikTok tự động, không cần streamer.

## Cài đặt nhanh

```bash
pip install -r requirements.txt
cp .env.example .env
# Sửa .env: điền TIKTOK_USERNAME của bạn
python server.py
```

## Cấu hình OBS

1. Thêm **Browser Source** trong OBS
2. URL: `http://localhost:8000`
3. Width: `600`, Height: `400`
4. Tick **"Shutdown source when not visible"** = OFF

## Thêm ảnh khuôn mặt

Đặt ảnh khuôn mặt (có nốt ruồi đánh số) vào: `static/face.jpg`

Chỉnh vị trí các nốt ruồi trong `static/index.html` (phần `.mole-1` đến `.mole-10`).

## Trigger keywords

Người xem comment bất kỳ dạng nào sau đây đều được xử lý:
- `bói số 3` / `boi so 3`
- `bói 3` / `boi 3`
- `số 3` / `so 3`
- `xem số 3`
- `xem cho tôi số 3`
- `bói giúp 3`
- `3 đi`

## Cấu hình giọng đọc

Sửa `config.py`:
- `TTS_ENGINE = "edge"` → miễn phí, tiếng Việt tốt
- `TTS_ENGINE = "elevenlabs"` → chất lượng cao, cần API key

## API endpoints

- `GET /` → Web UI (dùng cho OBS)
- `GET /api/stats` → Thống kê live
- `GET /api/status` → Trạng thái hiện tại
- `WS /ws` → WebSocket real-time
