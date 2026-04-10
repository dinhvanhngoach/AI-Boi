import asyncio
import os
import time
from collections import defaultdict
from TikTokLive import TikTokLiveClient
from TikTokLive.events import (
    CommentEvent,
    GiftEvent,
    ConnectEvent,
    DisconnectEvent,
    JoinEvent,
)
from config import TIKTOK_USERNAME, TIKTOK_SESSION_ID, RATE_LIMIT_SECONDS, QUEUE_MAX_SIZE, GIFT_BIG_THRESHOLD

# Euler Stream API key (tùy chọn - tăng rate limit)
EULER_API_KEY = os.getenv("EULER_API_KEY", "")
from ai_response import (
    parse_mole_number,
    get_mole_prediction,
    get_welcome_message,
    get_gift_message,
    get_idle_phrase,
)

# ─── Trạng thái hiển thị hiện tại (dùng chung với server.py) ──────────────────
current_display = {
    "username":    "",
    "mole_number": None,
    "prediction":  "",
    "event_type":  "idle",   # idle | join | comment | gift
    "gift_name":   "",
    "is_big_gift": False,
}

# Thống kê live
stats = {
    "total_comments": 0,
    "total_gifts":    0,
    "total_joins":    0,
}

# Theo dõi thời gian request cuối của mỗi user (rate limiting)
rate_limit_map: dict[str, float] = defaultdict(float)


def _is_rate_limited(username: str) -> bool:
    """Kiểm tra xem user có đang bị giới hạn tốc độ không."""
    now = time.time()
    if now - rate_limit_map[username] < RATE_LIMIT_SECONDS:
        return True
    rate_limit_map[username] = now
    return False


async def _enqueue(queue, item: dict):
    """Thêm sự kiện vào hàng đợi. Quà được ưu tiên, spam bị bỏ qua."""
    if queue.qsize() >= QUEUE_MAX_SIZE and not item.get("priority"):
        print(f"[Queue] Hàng đợi đầy, bỏ qua sự kiện của {item.get('username')}")
        return
    await queue.put(item)


def _build_client() -> TikTokLiveClient:
    """Tạo TikTok client mới (phải tạo mới mỗi lần reconnect, không tái sử dụng)."""
    # Thêm session cookie nếu có để bypass DEVICE_BLOCKED
    # TikTokLive v6.x: web_kwargs → httpx_kwargs → cookies
    kwargs = {}
    if TIKTOK_SESSION_ID:
        kwargs["web_kwargs"] = {"httpx_kwargs": {"cookies": {"sessionid": TIKTOK_SESSION_ID}}}
        print("[TikTok] Dùng session cookie để kết nối")
    # Thêm Euler API key nếu có để tăng rate limit
    if EULER_API_KEY:
        kwargs.setdefault("web_kwargs", {})
        kwargs["web_kwargs"]["signer_kwargs"] = {"sign_api_key": EULER_API_KEY}
        print("[TikTok] Dùng Euler API key")

    client = TikTokLiveClient(unique_id=TIKTOK_USERNAME, **kwargs)

    @client.on(ConnectEvent)
    async def on_connect(event: ConnectEvent):
        print(f"[TikTok] Đã kết nối tới live của {TIKTOK_USERNAME}")

    @client.on(DisconnectEvent)
    async def on_disconnect(event: DisconnectEvent):
        print("[TikTok] Mất kết nối với live stream")

    return client


async def start_tiktok_client(queue):
    """Khởi động TikTok Live client và lắng nghe các sự kiện.
    Tạo client mới mỗi lần reconnect để tránh lỗi 'one connection per client'.
    """
    # Thời gian chờ tăng dần khi bị block (1s → 5s → 15s → 30s → 60s)
    backoff_steps = [1, 5, 15, 30, 60]
    backoff_idx   = 0

    while True:
        # Tạo client MỚI mỗi lần kết nối
        client = _build_client()

        @client.on(JoinEvent)
        async def on_join(event: JoinEvent):
            """Xử lý khi có người vào live."""
            username = event.user.nickname or event.user.unique_id
            stats["total_joins"] += 1
            print(f"[Vào live] {username}")
            msg = get_welcome_message(username)
            await _enqueue(queue, {
                "type":        "join",
                "username":    username,
                "text":        msg,
                "priority":    False,
                "voice_key":   "nu_diu_dang",
                "mole_number": None,
                "gift_name":   "",
                "is_big_gift": False,
            })

        @client.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            """Xử lý comment bói nốt ruồi."""
            username = event.user.nickname or event.user.unique_id
            comment  = event.comment
            stats["total_comments"] += 1

            mole_number = parse_mole_number(comment)
            if mole_number is None:
                return  # Không phải comment bói → bỏ qua

            if _is_rate_limited(username):
                print(f"[Rate Limit] {username} bị giới hạn, bỏ qua")
                return

            print(f"[Comment] {username}: '{comment}' → nốt ruồi #{mole_number}")
            prediction = get_mole_prediction(username, mole_number)
            await _enqueue(queue, {
                "type":        "comment",
                "username":    username,
                "text":        prediction,
                "priority":    False,
                "voice_key":   "nu_diu_dang",
                "mole_number": mole_number,
                "gift_name":   "",
                "is_big_gift": False,
            })

        @client.on(GiftEvent)
        async def on_gift(event: GiftEvent):
            """Xử lý khi nhận quà - luôn được ưu tiên."""
            if event.gift.streakable and not event.gift.streak_ended:
                return  # Chờ chuỗi quà kết thúc mới xử lý

            username   = event.user.nickname or event.user.unique_id
            gift_name  = event.gift.name or "quà"
            gift_value = event.gift.diamond_count or 0
            is_big     = gift_value >= GIFT_BIG_THRESHOLD
            stats["total_gifts"] += 1

            print(f"[Quà] {username} tặng {gift_name} ({gift_value} diamond)")
            msg = get_gift_message(username, gift_name, is_big=is_big)
            await _enqueue(queue, {
                "type":        "gift",
                "username":    username,
                "text":        msg,
                "priority":    True,
                "voice_key":   "nam_tram" if is_big else "nu_diu_dang",
                "mole_number": None,
                "gift_name":   gift_name,
                "is_big_gift": is_big,
            })

        try:
            await client.start()
            # Kết nối thành công → reset backoff
            backoff_idx = 0
        except Exception as e:
            err_msg = str(e)
            wait    = backoff_steps[min(backoff_idx, len(backoff_steps) - 1)]
            backoff_idx += 1

            if "DEVICE_BLOCKED" in err_msg:
                # TikTok block IP/device → chờ lâu hơn
                wait = max(wait, 60)
                print(f"[TikTok] Bị TikTok chặn (DEVICE_BLOCKED). Chờ {wait}s rồi thử lại...")
                print("[TikTok] Gợi ý: thêm session cookie vào .env để bypass block")
            elif "one connection per client" in err_msg:
                # Client cũ chưa giải phóng → chờ ngắn rồi tạo client mới
                wait = 3
                print(f"[TikTok] Client cũ chưa giải phóng. Tạo client mới sau {wait}s...")
            else:
                print(f"[TikTok] Lỗi: {err_msg}. Thử lại sau {wait}s...")

            # Dọn dẹp client cũ trước khi tạo mới
            try:
                await client.disconnect()
            except Exception:
                pass

            await asyncio.sleep(wait)


async def idle_broadcaster(queue):
    """Tự động phát câu nhắc nhở mỗi 30 giây khi hàng đợi trống."""
    while True:
        await asyncio.sleep(30)
        if queue.empty():
            phrase = get_idle_phrase()
            print(f"[Idle] Phát câu nhắc: {phrase[:40]}...")
            await queue.put({
                "type":        "idle",
                "username":    "",
                "text":        phrase,
                "priority":    False,
                "voice_key":   "nu_diu_dang",
                "mole_number": None,
                "gift_name":   "",
                "is_big_gift": False,
            })
