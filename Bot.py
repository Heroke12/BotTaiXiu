import asyncio
import json
import os
import random
import string

from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor

from dotenv import load_dotenv
load_dotenv()  # load .env

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.MARKDOWN)
dp = Dispatcher(bot)

# ================== KEY SYSTEM ==================

KEYS_FILE = "keys.json"
user_licenses = {}


def load_keys():
    if not os.path.exists(KEYS_FILE):
        return {}
    with open(KEYS_FILE, "r") as f:
        return json.load(f)


def save_keys(data):
    with open(KEYS_FILE, "w") as f:
        json.dump(data, f, indent=2)


keys_db = load_keys()


def generate_key():
    chars = string.ascii_uppercase + string.digits
    return "-".join(
        "".join(random.choice(chars) for _ in range(4))
        for _ in range(4)
    )


@dp.message_handler(commands=["genkey"])
async def gen_key(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    key = generate_key()

    keys_db[key] = {
        "used": False,
        "used_by": None
    }
    save_keys(keys_db)

    await message.reply(f"✅ Key mới:\n{key}")


@dp.message_handler(commands=["redeem"])
async def redeem_key(message: types.Message):
    parts = message.text.split()

    if len(parts) != 2:
        await message.reply("Dùng: /redeem KEY")
        return

    key = parts[1].strip().upper()
    uid = str(message.from_user.id)

    if key not in keys_db:
        await message.reply("❌ Key không tồn tại")
        return

    if keys_db[key]["used"]:
        await message.reply("❌ Key đã được dùng")
        return

    keys_db[key]["used"] = True
    keys_db[key]["used_by"] = uid
    user_licenses[uid] = True

    save_keys(keys_db)

    await message.reply("✅ Redeem thành công! Bạn đã kích hoạt bot.")


# ================== PREDICTOR ==================

class TaiXiuPredictor:
    def __init__(self):
        self.analysis_history = []

    def advanced_md5_analysis(self, md5_hash):
        hash_parts = [md5_hash[i:i + 8] for i in range(0, 32, 8)]
        numbers = [int(part, 16) for part in hash_parts]

        total_sum = sum(numbers)

        product = 1
        for num in numbers[:4]:
            product *= (num % 1000) + 1

        binary_pattern = bin(int(md5_hash[:16], 16))[2:].zfill(64)
        ones_count = binary_pattern.count('1')
        zeros_count = binary_pattern.count('0')

        tai_score = 0
        xiu_score = 0

        if total_sum % 2 == 0:
            tai_score += 35
        else:
            xiu_score += 35

        if ones_count > zeros_count:
            tai_score += 25
        else:
            xiu_score += 25

        if product % 2 == 0:
            tai_score += 20
        else:
            xiu_score += 20

        if numbers[0] % 2 == 0:
            tai_score += 10
        else:
            xiu_score += 10

        if int(md5_hash[-1], 16) >= 8:
            tai_score += 10
        else:
            xiu_score += 10

        # ===== LOGIC GỐC =====
        if tai_score > xiu_score:
            base_prediction = "Tài"
            confidence = tai_score / (tai_score + xiu_score) * 100
        else:
            base_prediction = "Xỉu"
            confidence = xiu_score / (tai_score + xiu_score) * 100

        # ===== ĐẢO NGƯỢC =====
        prediction = "Xỉu" if base_prediction == "Tài" else "Tài"

        predicted_score = (sum(int(c, 16) for c in md5_hash[:3]) % 16) + 3

        return {
            "prediction": prediction,
            "confidence": round(confidence, 2),
            "predicted_score": predicted_score,
            "tai_score": tai_score,
            "xiu_score": xiu_score,
            "analysis_details": {
                "total_sum": total_sum,
                "bit_ratio": f"{ones_count}:{zeros_count}",
                "base_prediction": base_prediction
            }
        }


predictor = TaiXiuPredictor()

# ================== BOT COMMANDS ==================

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.reply(
        "🎰 *BOT DỰ ĐOÁN TÀI XỈU*\n\n"
        "Gửi MD5 để phân tích.\n"
        "Cần key để sử dụng.\n"
        "Dùng /redeem KEY"
    )
