import re
import random
import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

# ─── Từ điển bói 78 nốt ruồi ───────────────────────────────────────────────────
# Dựa theo bản đồ nốt ruồi truyền thống, vị trí trên khuôn mặt
MOLE_PREDICTIONS = {
    # Vùng trán (1-12): liên quan vận mệnh, sự nghiệp, tư duy
    1:  "Nốt ruồi số 1 nằm chính giữa trán - đây là nốt ruồi của người có tư duy lãnh đạo. Hmm… bạn có khả năng thiên bẩm để dẫn dắt người khác, chỉ cần thêm tự tin là thành công sẽ đến �",
    2:  "Nốt ruồi số 2 ở trán bên phải - dấu hiệu của trí tuệ sắc bén. Bạn thường đưa ra quyết định đúng đắn hơn người khác, đặc biệt trong chuyện tiền bạc và đầu tư 💡",
    3:  "Ồ nốt ruồi số 3 này thú vị lắm… Nằm ở trán trái, báo hiệu bạn có quý nhân phù trợ mạnh mẽ. Trong 3 tháng tới sẽ có người quan trọng xuất hiện và thay đổi cuộc đời bạn �",
    4:  "Nốt ruồi số 4 - trán phải, vị trí của người có phúc lộc dày. Bạn sinh ra đã có duyên với tiền bạc, chỉ cần kiên trì thêm một chút nữa thôi �",
    5:  "Hmm… nốt ruồi số 5 ở giữa trán trái… Đây là nốt ruồi hiếm, người có nốt này thường có trực giác rất nhạy. Bạn hay linh cảm đúng về mọi chuyện phải không? 🔮",
    6:  "Nốt ruồi số 6 - trán phải, gần đường chân tóc. Vận may đang dần ổn định, một giai đoạn bình yên và sung túc đang chờ bạn phía trước ✨",
    7:  "Nốt ruồi số 7 ở trán trái - nốt ruồi của người đa tài. Bạn có nhiều khả năng tiềm ẩn chưa được khai thác hết, đừng giới hạn bản thân mình nhé �",
    8:  "Ồ số 8 là con số may mắn! Nốt ruồi số 8 ở trán phải báo hiệu tài lộc đang trên đường đến. Hãy để ý cơ hội xuất hiện trong tuần này 🍀",
    9:  "Nốt ruồi số 9 - trán trái, vị trí của người có chí khí. Bạn không dễ bỏ cuộc, và chính sự kiên trì đó sẽ đưa bạn đến thành công mà người khác không đạt được 💪",
    10: "Nốt ruồi số 10 ở góc trán phải - dấu hiệu của người được trời phú cho may mắn. Những điều tốt đẹp thường đến với bạn một cách tự nhiên, hãy trân trọng điều đó 🌈",
    11: "Hmm… nốt ruồi số 11 này không đơn giản đâu… Nằm ở trán trái, mang năng lượng bảo hộ rất mạnh. Bạn thường thoát khỏi những tình huống nguy hiểm một cách kỳ lạ 🛡️",
    12: "Nốt ruồi số 12 ở góc trán trái - nốt ruồi của người có duyên với nghệ thuật và sáng tạo. Nếu bạn chưa theo đuổi đam mê, đây là lúc nên bắt đầu rồi đó 🎨",

    # Vùng mắt trái (13-26, 61-62, 65-66): tình cảm, hôn nhân, quan hệ xã hội
    13: "Nốt ruồi số 13 dưới lông mày trái - nốt ruồi tình cảm. Có vẻ như bạn đang có một mối duyên âm thầm… người ấy đang để ý bạn nhiều hơn bạn nghĩ đó 💕",
    14: "Nốt ruồi số 14 ở đầu lông mày trái - dấu hiệu của người có duyên lãnh đạo. Mọi người xung quanh thường tự nhiên tin tưởng và nghe theo bạn 👥",
    15: "Hmm… nốt ruồi số 15 này đặc biệt lắm… Nằm ở đầu lông mày phải, báo hiệu bạn sắp có một quyết định quan trọng. Hãy tin vào trực giác của mình nhé 🎯",
    16: "Nốt ruồi số 16 trên mí mắt trái - nốt ruồi của người đa cảm và tinh tế. Bạn hiểu người khác rất sâu, đây là món quà quý giá đó 💎",
    17: "Nốt ruồi số 17 trên mí mắt phải - dấu hiệu của người có duyên với nghệ thuật. Cảm xúc của bạn rất phong phú, hãy để nó trở thành sức mạnh chứ đừng là gánh nặng 🌸",
    18: "Ồ nốt ruồi số 18 này hiếm lắm đó! Nằm trên mí mắt trái, mang ý nghĩa may mắn trong tình duyên. Một mối quan hệ đẹp đang chờ bạn không xa 💑",
    19: "Nốt ruồi số 19 trên mí mắt phải - nốt ruồi của người được yêu thương. Bạn có sức hút tự nhiên khiến người khác muốn gần gũi và bảo vệ bạn 🌺",
    20: "Hmm… nốt ruồi số 20 dưới mắt trái… Đây là nốt ruồi của người có trái tim nhân hậu. Sự tốt bụng của bạn sẽ được đền đáp xứng đáng trong thời gian tới 🤍",
    21: "Nốt ruồi số 21 dưới mắt phải - dấu hiệu của người có duyên với con cái. Gia đình sẽ là nguồn hạnh phúc lớn nhất của bạn 👨‍👩‍👧",
    22: "Nốt ruồi số 22 dưới mắt trái, gần mũi - nốt ruồi tài lộc ẩn. Tiền bạc sẽ đến từ những nguồn không ngờ tới, hãy để ý những cơ hội nhỏ xung quanh 💸",
    23: "Ồ nốt ruồi số 23 này thú vị! Nằm ở gò má trái cao - người có nốt này thường được quý nhân giúp đỡ suốt đời. Bạn không bao giờ phải đi một mình đâu 🤝",
    24: "Nốt ruồi số 24 ở gò má trái - nốt ruồi của người có duyên với người nổi tiếng. Bạn sẽ có cơ hội gặp gỡ những người quan trọng thay đổi cuộc đời mình ⭐",
    25: "Hmm… nốt ruồi số 25 dưới mắt phải… Đây là nốt ruồi của người nhạy cảm với năng lượng xung quanh. Hãy tin vào linh cảm của mình, nó thường đúng lắm đó 🔮",
    26: "Nốt ruồi số 26 dưới mắt trái, gần mũi - dấu hiệu của người có khả năng thuyết phục. Bạn nói chuyện rất có duyên, người khác dễ bị thuyết phục bởi bạn 🗣️",

    # Vùng mũi và má (27-37, 49-54, 59-63): sức khỏe, tài chính, hôn nhân
    27: "Nốt ruồi số 27 ở má phải - nốt ruồi của người có phúc khí dày. Cuộc sống của bạn sẽ ngày càng tốt hơn theo năm tháng, đừng nản lòng nhé 🌱",
    28: "Hmm… nốt ruồi số 28 này không đơn giản… Nằm ở vùng má trái giữa - báo hiệu bạn có khả năng tích lũy tài sản rất tốt. Hãy bắt đầu tiết kiệm từ bây giờ 🏦",
    29: "Nốt ruồi số 29 ở má phải - dấu hiệu của người có duyên với công việc kinh doanh. Bạn có bản năng nhạy bén với thị trường, đây là lợi thế lớn đó 📈",
    30: "Nốt ruồi số 30 ở má trái dưới - nốt ruồi của người được nhiều người yêu mến. Bạn có tài năng kết nối mọi người lại với nhau 🌐",
    31: "Ồ nốt ruồi số 31 ở má phải! Đây là nốt ruồi của người có vận may bền vững. Không giàu nhanh nhưng cuộc sống luôn ổn định và hạnh phúc 🏡",
    32: "Nốt ruồi số 32 ở má trái - nốt ruồi tình duyên đẹp. Có vẻ như bạn sắp gặp hoặc đang có một mối tình rất đặc biệt… hãy trân trọng nhé 💝",
    33: "Hmm… nốt ruồi số 33 ở má phải ngoài… Người có nốt này thường có cuộc sống phong phú và nhiều trải nghiệm thú vị. Bạn không phải kiểu người thích ở yên một chỗ đúng không? ✈️",
    34: "Nốt ruồi số 34 - vùng má dưới trái. Dấu hiệu của người có sức khỏe tốt và tinh thần lạc quan. Năng lượng tích cực của bạn lan tỏa đến mọi người xung quanh ☀️",
    35: "Nốt ruồi số 35 ở má trái ngoài - nốt ruồi của người có duyên đi xa. Bạn sẽ có cơ hội thay đổi môi trường sống hoặc làm việc ở nơi mới rất tốt 🗺️",
    36: "Ồ nốt ruồi số 36 này đặc biệt! Nằm ở má trái - báo hiệu bạn có tài năng ẩn chưa được phát hiện. Đừng ngại thử những điều mới, bạn sẽ bất ngờ về khả năng của mình 🌟",
    37: "Nốt ruồi số 37 ở vùng má trái gần miệng - nốt ruồi của người ăn nói có duyên. Bạn có khả năng làm người khác vui và thoải mái chỉ bằng lời nói 😊",
    49: "Hmm… nốt ruồi số 49 ở sống mũi… Đây là nốt ruồi tài lộc rất mạnh! Người có nốt này thường có khả năng kiếm tiền giỏi và biết cách giữ tiền 💰",
    50: "Nốt ruồi số 50 ở đầu mũi - nốt ruồi của người có tài kinh doanh thiên bẩm. Bạn có khả năng nhìn thấy cơ hội mà người khác bỏ qua 👁️",
    51: "Nốt ruồi số 51 ở chóp mũi - dấu hiệu của người có phúc lộc dày. Tiền bạc và may mắn luôn theo bạn, chỉ cần bạn biết nắm bắt đúng thời điểm 🎯",
    52: "Ồ nốt ruồi số 52 ở cánh mũi trái! Đây là nốt ruồi tài lộc ẩn - tiền bạc sẽ đến từ nhiều nguồn khác nhau. Hãy mở rộng các mối quan hệ của mình 🤲",
    53: "Nốt ruồi số 53 ở cánh mũi phải - nốt ruồi của người có duyên với bất động sản. Đầu tư vào nhà đất sẽ mang lại may mắn cho bạn trong tương lai 🏠",
    54: "Hmm… nốt ruồi số 54 dưới mũi… Người có nốt này thường có cuộc hôn nhân hạnh phúc và bền vững. Người bạn đời của bạn sẽ là điểm tựa vững chắc suốt đời 💑",
    59: "Nốt ruồi số 59 ở má phải ngoài - nốt ruồi của người có duyên với người nước ngoài hoặc công việc quốc tế. Cơ hội từ nước ngoài đang chờ bạn 🌍",
    60: "Ồ nốt ruồi số 60 ở thái dương phải! Đây là nốt ruồi của người có trí nhớ tốt và học gì cũng nhanh. Bạn có lợi thế lớn trong học tập và công việc đòi hỏi tư duy 🧠",
    61: "Nốt ruồi số 61 ở thái dương trái - dấu hiệu của người có duyên với nghệ thuật biểu diễn. Bạn có sức hút tự nhiên trước đám đông, hãy tận dụng điều này 🎤",
    62: "Hmm… nốt ruồi số 62 ở má trái thấp… Người có nốt này thường có cuộc sống ổn định và bình yên. Hạnh phúc của bạn đến từ những điều giản dị 🌿",
    63: "Nốt ruồi số 63 ở má phải thấp - nốt ruồi của người có sức khỏe dẻo dai. Bạn có thể lực tốt hơn người khác, hãy duy trì lối sống lành mạnh để phát huy điều này 💪",

    # Vùng lông mày (64-69): trí tuệ, sự nghiệp, may mắn
    64: "Nốt ruồi số 64 ở đầu lông mày trái trong - nốt ruồi của người thông minh và nhạy bén. Bạn thường giải quyết vấn đề nhanh hơn người khác rất nhiều 🎓",
    65: "Ồ nốt ruồi số 65 ở đuôi lông mày trái! Đây là nốt ruồi may mắn trong sự nghiệp. Một cơ hội thăng tiến đang đến gần, hãy chuẩn bị sẵn sàng 🚀",
    66: "Hmm… nốt ruồi số 66 ở giữa lông mày trái… Người có nốt này thường có tư duy sáng tạo vượt trội. Những ý tưởng của bạn thường đi trước thời đại 💡",
    67: "Nốt ruồi số 67 ở giữa hai lông mày - đây là vị trí đặc biệt nhất! Nốt ruồi ấn đường mang ý nghĩa vận mệnh tốt đẹp. Bạn được trời phú cho nhiều may mắn hơn người thường 🌟",
    68: "Nốt ruồi số 68 ở đuôi lông mày phải - nốt ruồi của người có duyên với người có địa vị. Bạn sẽ được những người thành công giúp đỡ và dìu dắt 🤝",
    69: "Ồ nốt ruồi số 69 ở giữa lông mày phải! Dấu hiệu của người có trực giác mạnh và khả năng tiên đoán tốt. Bạn thường biết trước điều gì sẽ xảy ra phải không? 🔮",

    # Vùng tai (71-74): phúc lộc, tuổi thọ, tài lộc
    71: "Nốt ruồi số 71 ở tai phải trên - nốt ruồi của người trường thọ và phúc lộc. Bạn có sức sống mãnh liệt và tinh thần lạc quan giúp bạn vượt qua mọi khó khăn 🌿",
    72: "Hmm… nốt ruồi số 72 ở tai phải dưới… Người có nốt này thường được thừa hưởng phúc lộc từ tổ tiên. Gia đình là nền tảng vững chắc nhất của bạn 🏡",
    73: "Nốt ruồi số 73 ở tai trái trên - dấu hiệu của người có duyên với tiền bạc từ sớm. Bạn có khả năng tự lập và kiếm tiền từ rất trẻ 💰",
    74: "Ồ nốt ruồi số 74 ở tai trái dưới! Đây là nốt ruồi hiếm - người có nốt này thường có cuộc sống sung túc và được nhiều người kính trọng. Uy tín của bạn ngày càng tăng cao 👑",

    # Vùng miệng và cằm (38-46, 55-58, 70, 75-78): tình duyên, hôn nhân, con cái
    38: "Nốt ruồi số 38 ở vùng cằm trái - nốt ruồi của người có ý chí mạnh mẽ. Bạn không bao giờ bỏ cuộc, và đây chính là bí quyết thành công của bạn 💪",
    39: "Hmm… nốt ruồi số 39 ở cằm giữa… Người có nốt này thường có cuộc hôn nhân hạnh phúc. Người bạn đời của bạn sẽ là người hiểu và trân trọng bạn nhất 💑",
    40: "Nốt ruồi số 40 ở cằm phải - dấu hiệu của người có duyên với con cái. Bạn sẽ có những đứa con hiếu thảo và thành đạt, đây là niềm tự hào lớn nhất 👨‍👩‍👧‍👦",
    41: "Ồ nốt ruồi số 41 ở cằm phải! Nốt ruồi của người có tài ăn nói và giao tiếp. Bạn có thể thành công trong các lĩnh vực cần kỹ năng thuyết trình và đàm phán 🗣️",
    42: "Nốt ruồi số 42 ở cằm phải gần - người có nốt này thường có cuộc sống ổn định về tài chính. Bạn biết cách quản lý tiền bạc và không bao giờ thiếu thốn 💳",
    43: "Hmm… nốt ruồi số 43 ở cằm phải ngoài… Đây là nốt ruồi của người có duyên với công việc sáng tạo. Tài năng nghệ thuật của bạn sẽ mang lại thu nhập tốt 🎨",
    44: "Nốt ruồi số 44 ở góc cằm phải - nốt ruồi của người có chí khí và bản lĩnh. Bạn không ngại đối mặt với thử thách, và chính điều đó làm bạn khác biệt 🦁",
    45: "Ồ nốt ruồi số 45 ở cổ trái! Đây là nốt ruồi của người có duyên với công việc liên quan đến giọng nói - ca hát, diễn thuyết, dạy học. Giọng nói của bạn có sức hút đặc biệt 🎵",
    46: "Nốt ruồi số 46 ở cổ phải - dấu hiệu của người có sức khỏe tốt và tuổi thọ cao. Bạn có nền tảng sức khỏe vững chắc, hãy duy trì lối sống lành mạnh 🌱",
    47: "Hmm… nốt ruồi số 47 ở trán giữa cao… Người có nốt này thường có tầm nhìn xa và tư duy chiến lược. Bạn thường thấy bức tranh toàn cảnh khi người khác chỉ thấy chi tiết 🦅",
    48: "Nốt ruồi số 48 ở trán giữa thấp - nốt ruồi của người có duyên với học vấn. Bạn học gì cũng giỏi và có khả năng đạt được bằng cấp cao 📚",
    55: "Nốt ruồi số 55 ở cằm giữa dưới - nốt ruồi của người có tình cảm sâu sắc. Bạn yêu hết lòng và được người thân yêu thương rất nhiều 💖",
    56: "Ồ nốt ruồi số 56 ở cổ giữa! Đây là nốt ruồi của người có duyên với công việc truyền thông và mạng xã hội. Bạn có khả năng tạo ảnh hưởng lớn trên mạng đó 📱",
    57: "Nốt ruồi số 57 ở cằm phải dưới - dấu hiệu của người có phúc lộc bền vững. Cuộc sống của bạn sẽ ngày càng tốt hơn theo thời gian 📈",
    58: "Hmm… nốt ruồi số 58 ở cằm trái dưới… Người có nốt này thường có trực giác mạnh về con người. Bạn hiếm khi bị lừa dối vì bạn đọc được tâm lý người khác rất tốt 🧿",
    70: "Nốt ruồi số 70 ở môi trên giữa - nốt ruồi của người có duyên ăn uống và hưởng thụ cuộc sống. Bạn biết cách tận hưởng những điều tốt đẹp trong cuộc sống 🍀",
    75: "Ồ nốt ruồi số 75 ở môi dưới giữa! Đây là nốt ruồi của người ăn nói ngọt ngào và có duyên. Lời nói của bạn có sức mạnh chữa lành và an ủi người khác 🌸",
    76: "Nốt ruồi số 76 ở cằm trên giữa - nốt ruồi tình duyên đẹp. Có vẻ như bạn sắp có một bước ngoặt lớn trong chuyện tình cảm… hãy mở lòng đón nhận nhé 💕",
    77: "Hmm… nốt ruồi số 77 ở khóe miệng trái… Người có nốt này thường có nụ cười rất duyên và thu hút. Bạn làm người khác vui chỉ bằng nụ cười của mình 😊",
    78: "Nốt ruồi số 78 ở khóe miệng phải - nốt ruồi của người có duyên với ẩm thực và nghệ thuật. Bạn có khẩu vị tinh tế và cảm nhận cái đẹp rất sâu sắc 🌺",
}


# ─── Các pattern nhận diện comment bói ────────────────────────────────────────
BOI_PATTERNS = [
    r"b[oó]i\s*s[oố]\s*(\d+)",       # "bói số 3", "boi so 3"
    r"b[oó]i\s*(\d+)",                # "bói 3", "boi 3"
    r"s[oố]\s*(\d+)",                 # "số 3", "so 3"
    r"xem\s*s[oố]\s*(\d+)",           # "xem số 3"
    r"xem\s*cho\s*t[oô]i\s*s[oố]?\s*(\d+)",  # "xem cho tôi số 3"
    r"b[oó]i\s*gi[uú]p\s*s[oố]?\s*(\d+)",    # "bói giúp số 3"
    r"s[oố]\s*đẹp\s*(\d+)",           # "số đẹp 3"
    r"(\d+)\s*đi",                    # "3 đi"
    r"^(\d+)$",                       # chỉ gõ số "3"
]

# ─── Câu nhắc nhở khi không có ai comment (idle) ──────────────────────────────
IDLE_PHRASES = [
    "Ai chưa bói thì nhanh tay lên nha 👀 Comment bói số từ 1 đến 78 để xem vận mệnh nào!",
    "Nốt ruồi này hiếm lắm đó… Bạn nào muốn biết ý nghĩa thì comment bói số nhé!",
    "Có người vừa nhận kết quả cực kỳ đặc biệt 😳 Bạn có muốn thử không?",
    "Mỗi nốt ruồi đều mang một bí mật riêng… Comment bói số từ 1 đến 78 để khám phá nào!",
    "Hmm… tôi đang cảm nhận được năng lượng rất đặc biệt trong phòng này… Ai muốn bói không?",
    "Đừng bỏ lỡ cơ hội biết vận mệnh của mình nhé! Comment bói số bất kỳ từ 1 đến 78!",
    "78 nốt ruồi, 78 bí mật… Bạn đang mang nốt ruồi số mấy? Comment ngay nào! 🔮",
    "Có vẻ như hôm nay là ngày may mắn của nhiều người… Bạn có muốn kiểm tra không? 🍀",
]

# ─── Câu chào khi có người vào live ───────────────────────────────────────────
WELCOME_TEMPLATES = [
    "Chào mừng {username} đến với phòng bói nốt ruồi huyền bí 🔮 Comment bói số từ 1 đến 78 để xem vận mệnh nhé!",
    "Ồ {username} vừa vào rồi! Chào bạn nha 👋 Hãy comment bói số để khám phá bí mật nốt ruồi của bạn!",
    "Welcome {username}! 🌟 Phòng bói đang chờ bạn, comment bói số từ 1 đến 78 nào!",
    "Chào {username}! Tôi đang cảm nhận được năng lượng đặc biệt từ bạn… Comment bói số để khám phá nhé 🔮",
]

# ─── Câu cảm ơn khi nhận quà thường ──────────────────────────────────────────
GIFT_TEMPLATES = [
    "Ôi cảm ơn {username} đã tặng {gift_name} cho tôi ❤️ Bạn thật tốt bụng quá! Tôi sẽ ưu tiên bói cho bạn ngay!",
    "Wow {username} tặng {gift_name} rồi! 🎁 Cảm ơn bạn rất nhiều nha! Năng lượng tốt lành sẽ đến với bạn!",
    "Cảm ơn {username} đã tặng {gift_name} ✨ Bạn thật hào phóng! Vận may sẽ theo bạn suốt ngày hôm nay!",
]

# ─── Câu cảm ơn khi nhận quà lớn (hiệu ứng đặc biệt) ─────────────────────────
BIG_GIFT_TEMPLATES = [
    "OMG!!! {username} vừa tặng {gift_name} siêu to khổng lồ!!! 🎉🎉🎉 Cảm ơn bạn cực kỳ nhiều! Tôi sẽ bói đặc biệt cho bạn ngay bây giờ!!!",
    "Trời ơi!!! {username} quá hào phóng luôn!!! Tặng {gift_name} cho tôi!!! 💖💖💖 Xin cảm ơn bạn từ tận đáy lòng!!!",
]


def parse_mole_number(comment: str) -> int | None:
    """Phân tích comment để lấy số nốt ruồi (1-78)."""
    comment_lower = comment.lower().strip()
    for pattern in BOI_PATTERNS:
        match = re.search(pattern, comment_lower)
        if match:
            num = int(match.group(1))
            if 1 <= num <= 78:
                return num
    return None


def get_mole_prediction(username: str, mole_number: int) -> str:
    """Lấy nội dung bói cho số nốt ruồi tương ứng."""
    if mole_number in MOLE_PREDICTIONS:
        base = MOLE_PREDICTIONS[mole_number]
        return f"{username} ơi, {base}"
    # Số không có trong dict → gọi OpenAI generate
    if OPENAI_API_KEY:
        return _generate_ai_prediction(username, mole_number)
    # Fallback mặc định
    return (
        f"{username} ơi, nốt ruồi số {mole_number} của bạn mang năng lượng rất đặc biệt… "
        "Hãy tin vào trực giác của mình, điều tốt đẹp đang trên đường đến với bạn 🌟"
    )


def _generate_ai_prediction(username: str, mole_number: int) -> str:
    """Dùng OpenAI API để tạo nội dung bói khi số không có trong dict."""
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Bạn là một thầy bói nốt ruồi huyền bí, dịu dàng và gây tò mò. "
                        "Phong cách nói hơi tâm linh, dịu dàng, gây nghiện. "
                        "Trả lời ngắn gọn trong 2-3 câu, mang tính tích cực và giải trí. "
                        "Không đề cập đến bất kỳ điều gì tiêu cực hay nhạy cảm."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Bói ý nghĩa nốt ruồi số {mole_number} cho người tên {username}",
                },
            ],
            max_tokens=150,
            temperature=0.8,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[OpenAI] Lỗi khi gọi API: {e}")
        return (
            f"{username} ơi, nốt ruồi số {mole_number} của bạn ẩn chứa điều kỳ diệu… "
            "Hãy để tâm đến những cơ hội xung quanh bạn trong thời gian tới nhé 🔮"
        )


def get_welcome_message(username: str) -> str:
    """Tạo câu chào khi có người vào live."""
    return random.choice(WELCOME_TEMPLATES).format(username=username)


def get_gift_message(username: str, gift_name: str, is_big: bool = False) -> str:
    """Tạo câu cảm ơn khi nhận quà."""
    templates = BIG_GIFT_TEMPLATES if is_big else GIFT_TEMPLATES
    return random.choice(templates).format(username=username, gift_name=gift_name)


def get_idle_phrase() -> str:
    """Lấy câu nhắc nhở ngẫu nhiên khi không có hoạt động."""
    return random.choice(IDLE_PHRASES)
