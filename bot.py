import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.utils.markdown import hbold

# Token va admin ID
TOKEN = "6367097370:AAHjerMmugPyfJS19n-8TgFVe8ym0fUzA54"
ADMIN_ID = 1951089207  # O'zgartirish shart emas

# Bot va dispatcher yaratish
bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher()

# Foydalanuvchi tillari va xabar vaqtlari uchun lug‘atlar
user_languages = {}
user_last_message_time = {}

# 🔹 Tilni tanlash tugmalari
lang_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🇺🇿 O'zbekcha"), KeyboardButton(text="🇷🇺 Русский")]
    ],
    resize_keyboard=True
)

# 🔹 Kontakt yuborish tugmasi
contact_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📞 Kontaktni yuborish", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# `/start` komandasiga javob
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("🇺🇿 Tilni tanlang / 🇷🇺 Выберите язык:", reply_markup=lang_kb)

# 🔹 Tilni tanlash tugmasi
@dp.message(F.text.in_(["🇺🇿 O'zbekcha", "🇷🇺 Русский"]))
async def set_language(message: types.Message):
    user_languages[message.from_user.id] = "ru" if message.text == "🇷🇺 Русский" else "uz"
    lang = user_languages[message.from_user.id]

    if lang == "ru":
        await message.answer("✍️ Пожалуйста, напишите вашу жалобу или предложение:", reply_markup=contact_kb)
    else:
        await message.answer("✍️ Iltimos, shikoyatingiz yoki taklifingizni yozing:", reply_markup=contact_kb)

# 🔹 Shikoyat yoki taklif qabul qilish
@dp.message(F.text)
async def receive_message(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, "uz")
    now = asyncio.get_event_loop().time()

    if user_id in user_last_message_time:
        time_diff = now - user_last_message_time[user_id]
        if time_diff < 60:
            return  # 60 soniyadan oldin yana xabar kelsa, javob bermaydi

    user_last_message_time[user_id] = now

    # Adminga yuboriladigan xabar
    admin_text = f"📩 Yangi xabar:\n👤 {message.from_user.full_name} ({message.from_user.id})\n📝 {message.text}"
    await bot.send_message(ADMIN_ID, admin_text)

    # Foydalanuvchiga javob
    response_text = "✅ Sizning shikoyatingiz qabul qilindi. Iltimos, biroz kuting.\n📲 @ganiev_s7 ni kontaktingizga saqlang va kontaktingizni yuboring." if lang == "uz" else \
                    "✅ Ваша жалоба принята. Пожалуйста, подождите немного.\n📲 Сохраните @ganiev_s7 и отправьте ваш контакт."

    await message.answer(response_text)

# 🔹 Kontakt yuborish qabul qilish
@dp.message(F.contact.is_)
async def receive_contact(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, "uz")
    contact_info = f"📞 Yangi kontakt:\n{message.contact.phone_number}\n👤 {message.from_user.full_name}"

    # Adminga yuborish
    await bot.send_message(ADMIN_ID, contact_info)

    # Foydalanuvchiga javob va menyuni olib tashlash
    response_text = "✅ Rahmat! Sizning kontaktingiz adminga yuborildi." if lang == "uz" else \
                    "✅ Спасибо! Ваш контакт отправлен администратору."

    await message.answer(response_text, reply_markup=ReplyKeyboardRemove())

# Botni ishga tushirish
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
