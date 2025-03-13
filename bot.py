import asyncio
import logging
import openai
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton
)
from aiogram.enums import ParseMode  # Aiogram 3.x versiyasi uchun
from config import API_ID, API_HASH, BOT_TOKEN, OPENAI_API_KEY, ADMIN_ID

# OpenAI API sozlash
openai.api_key = OPENAI_API_KEY

# Bot va Dispatcher
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot=bot)

user_languages = {}
user_modes = {}  # Foydalanuvchi rejimi: normal yoki ganiev_gpt

# Til tanlash tugmalari
lang_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🇺🇿 O'zbekcha"), KeyboardButton(text="🇷🇺 Русский")]
    ],
    resize_keyboard=True
)

# Kontakt va GanievGPT tugmalari
def get_main_keyboard(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Kontaktni yuborish", request_contact=True) if lang == "uz" else KeyboardButton(text="📞 Отправить контакт", request_contact=True)],
            [KeyboardButton(text="🤖 GanievGPT")]
        ],
        resize_keyboard=True
    )

# GanievGPT rejimi uchun tugma
ganiev_gpt_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="⬅️ Orqaga")]],
    resize_keyboard=True
)

# /start komandasi
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("🇺🇿 Tilni tanlang / 🇷🇺 Выберите язык:", reply_markup=lang_kb)

# Tilni tanlash
@dp.message(F.text.in_(["🇺🇿 O'zbekcha", "🇷🇺 Русский"]))
async def set_language(message: types.Message):
    user_languages[message.from_user.id] = "ru" if message.text == "🇷🇺 Русский" else "uz"
    user_modes[message.from_user.id] = "normal"  # Standart rejim
    lang = user_languages[message.from_user.id]

    await message.answer("✍️ Iltimos, shikoyatingiz yoki taklifingizni yozing:", reply_markup=get_main_keyboard(lang))

# /GanievGPT komandasi
@dp.message(F.text == "🤖 GanievGPT")
async def ganiev_gpt_cmd(message: types.Message):
    user_modes[message.from_user.id] = "ganiev_gpt"  # GanievGPT rejimi
    await message.answer("📝 Savolingizni yozing, men sizga javob beraman.", reply_markup=ganiev_gpt_kb)

# ChatGPT bilan ishlash (faqat GanievGPT rejimida)
@dp.message(F.text)
async def handle_messages(message: types.Message):
    user_id = message.from_user.id
    mode = user_modes.get(user_id, "normal")

    if message.text == "⬅️ Orqaga":
        user_modes[user_id] = "normal"
        lang = user_languages.get(user_id, "uz")
        await message.answer("🔙 Bosh menyuga qaytdingiz.", reply_markup=get_main_keyboard(lang))
        return

    if mode == "ganiev_gpt":
        # Savolni administratorga yuborish
        admin_text = f"🤖 GanievGPT savol:\n👤 {message.from_user.full_name} ({message.from_user.id})\n📝 {message.text}"
        await bot.send_message(ADMIN_ID, admin_text)

        # ChatGPT'dan javob olish
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": message.text}]
            )
            answer = response.choices[0].message.content  # TO'G'RILANGAN QISM
        except Exception as e:
            logging.error(f"OpenAI API xatosi: {e}")
            answer = "❌ GanievGPT bilan bog‘lanib bo‘lmadi. Iltimos, qayta urinib ko‘ring."

        await message.answer(answer)
        return

    # Agar GanievGPT rejimida bo‘lmasa, xabar adminga shikoyat sifatida boradi
    admin_text = f"📩 Yangi xabar:\n👤 {message.from_user.full_name} ({message.from_user.id})\n📝 {message.text}"
    await bot.send_message(ADMIN_ID, admin_text)

    response_text = "✅ Sizning shikoyatingiz qabul qilindi. Iltimos, biroz kuting."
    await message.answer(response_text)

# Foydalanuvchi kontakt yuborganda
@dp.message(F.contact)
async def receive_contact(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, "uz")

    contact_info = f"📞 Yangi kontakt:\n📱 {message.contact.phone_number}\n👤 {message.from_user.full_name}"
    await bot.send_message(ADMIN_ID, contact_info)

    response_text = "✅ Rahmat! Sizning kontaktingiz adminga yuborildi."
    await message.answer(response_text, reply_markup=ganiev_gpt_kb)

# Botni ishga tushirish
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling()

if __name__ == "__main__":  # TO'G'RILANGAN QISM
    asyncio.run(main())
