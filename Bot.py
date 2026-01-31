
import asyncio
import json
import os
import random
import string
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor

from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.MARKDOWN)
dp = Dispatcher(bot)

# ================== KEY SYSTEM ==================

KEYS_FILE = "keys.json"
USER_FILE = "users.json"


def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


keys_db = load_json(KEYS_FILE)
users_db = load_json(USER_FILE)


def generate_key():
    chars = string.ascii_uppercase + string.digits
    return "-".join(
        "".join(random.choice(chars) for _ in range(4))
        for _ in range(4)
    )


def is_user_active(user_id):
    return str(user_id) in users_db


# ================== ADMIN ==================

@dp.message_handler(commands=["genkey"])
async def gen_key(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    key = generate_key()
    keys_db[key] = {
        "used": False,
        "used_by": None,
        "used_at": None
    }

    save_json(KEYS_FILE, keys_db)

    await message.reply(f"🔑 **KEY MỚI**\n`{key}`")


# ================== USER ==================

@dp.message_handler(commands=["redeem"])
async def redeem_key(message: types.Message):
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Dùng: `/redeem <KEY>`")
        return

    key = args[1].upper()
    uid = str(message.from_user.id)

    if key not in keys_db:
        await message.reply("❌ Key không tồn tại")
        return

    if keys_db[key]["used"]:
        await message.reply("❌ Key đã được sử dụng")
        return

    keys_db[key]["used"] = True
    keys_db[key]["used_by"] = uid
    keys_db[key]["used_at"] = datetime.utcnow().isoformat()

    users_db[uid] = {
        "activated_at": datetime.utcnow().isoformat()
    }

    save_json(KEYS_FILE, keys_db)
    save_json(USER_FILE, users_db)

    await message.reply("✅ **KÍCH HOẠT THÀNH CÔNG**")


# ================== PREDICTOR ==================

class TaiXiuPredictor:
    def advanced_md5_analysis(self, md5_hash):
        parts = [md5_hash[i:i + 8] for i in range(0, 32, 8)]
        nums = [int(p, 16) for p in parts]

        total_sum = sum(nums)
        product = 1
        for n in nums[:4]:
            product *= (n % 1000) + 1

        binary = bin(int(md5_hash[:16], 16))[2:].zfill(64)
        ones = binary.count("1")
        zeros = binary.count("0")

        tai = xiu = 0

        tai += 35 if total_sum % 2 == 0 else 0
        xiu += 35 if total_sum % 2 != 0 else 0

        tai += 25 if ones > zeros else 0
        xiu += 25 if ones <= zeros else 0

        tai += 20 if product % 2 == 0 else 0
        xiu += 20 if product % 2 != 0 else 0

        tai += 10 if nums[0] % 2 == 0 else 0
        xiu += 10 if nums[0] % 2 != 0 else 0

        tai += 10 if int(md5_hash[-1], 16) >= 8 else 0
        xiu += 10 if int(md5_hash[-1], 16) < 8 else 0

        if tai > xiu:
            base = "Tài"
            confidence = tai / (tai + xiu) * 100
        else:
            base = "Xỉu"
            confidence = xiu / (tai + xiu) * 100

        prediction = "Xỉu" if base == "Tài" else "Tài"
        score = (sum(int(c, 16) for c in md5_hash[:3]) % 16) + 3

        return prediction, round(confidence, 2), score, base


predictor = TaiXiuPredictor()


# ================== MD5 COMMAND ==================

@dp.message_handler(commands=["md5"])
async def md5_cmd(message: types.Message):
    if not is_user_active(message.from_user.id):
        await message.reply("🔒 Chưa kích hoạt. Dùng `/redeem <KEY>`")
        return

    args = message.text.split()
    if len(args) != 2:
        await message.reply("Dùng: `/md5 <chuỗi_md5>`")
        return

    md5 = "".join(args[1].lower().split())

    if len(md5) != 32 or not all(c in "0123456789abcdef" for c in md5):
        await message.reply("❌ MD5 không hợp lệ")
        return

    prediction, confidence, score, base = predictor.advanced_md5_analysis(md5)

    await message.reply(
        f"📊 **PHÂN TÍCH MD5**\n\n"
        f"🔢 `{md5}`\n"
        f"🎯 **KẾT QUẢ:** **{prediction}**\n"
        f"📈 Độ tin cậy: {confidence}%\n"
        f"🎲 Điểm: {score}\n"
        f"🧠 Logic gốc: {base}"
    )


# ================== FALLBACK ==================

@dp.message_handler()
async def fallback(message: types.Message):
    await message.reply("ℹ️ Dùng lệnh: `/md5 <chuỗi_md5>`")


# ================== RUN ==================

if __name__ == "__main__":
    print("🤖 Bot đang chạy...")
    executor.start_polling(dp, skip_updates=True)
