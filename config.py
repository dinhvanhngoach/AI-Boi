import os
from dotenv import load_dotenv

load_dotenv()

# ─── Tài khoản TikTok ──────────────────────────────────────────────────────────
TIKTOK_USERNAME = os.getenv("TIKTOK_USERNAME", "@your_tiktok_username")

# Session cookie để bypass DEVICE_BLOCKED (lấy từ trình duyệt đang đăng nhập TikTok)
# Hướng dẫn: F12 → Application → Cookies → tiktok.com → copy giá trị "sessionid"
TIKTOK_SESSION_ID = os.getenv("TIKTOK_SESSION_ID", "")

# ─── API Keys ──────────────────────────────────────────────────────────────────
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

# ─── Cấu hình TTS ──────────────────────────────────────────────────────────────
# Chọn engine: "edge" (miễn phí) | "elevenlabs" (chất lượng cao) | "google"
TTS_ENGINE = os.getenv("TTS_ENGINE", "edge")

# ─── Giới hạn tốc độ (giây/user) ──────────────────────────────────────────────
RATE_LIMIT_SECONDS = 10

# ─── Kích thước tối đa của hàng đợi ───────────────────────────────────────────
QUEUE_MAX_SIZE = 50

# ─── Ngưỡng quà lớn (diamond >= giá trị này → hiệu ứng đặc biệt) ──────────────
GIFT_BIG_THRESHOLD = 100

# ─── Đường dẫn ảnh khuôn mặt ──────────────────────────────────────────────────
MOLE_IMAGE_PATH = "static/face.jpg"

# ─── Danh sách giọng đọc Edge TTS (tiếng Việt) ────────────────────────────────
EDGE_VOICES = {
    "nu_diu_dang": "vi-VN-HoaiMyNeural",   # Giọng nữ dịu dàng (mặc định)
    "nam_tram":    "vi-VN-NamMinhNeural",   # Giọng nam trầm (dùng cho quà lớn)
}

# Giọng mặc định: "nu_diu_dang" = giọng nữ | "nam_tram" = giọng nam
DEFAULT_VOICE = "nam_tram"
