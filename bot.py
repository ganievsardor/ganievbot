import asyncio
import logging
import openai
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardRemove
)
from aiogram.client.default import DefaultBotProperties

# Tokenlar
# SECURITY ISSUE: Tokens should be stored as environment variables
TOKEN = "6367097370:AAHjerMmugPyfJS19n-8TgFVe8ym0fUzA54"  # Should use os.environ.get("BOT_TOKEN")
# SECURITY ISSUE: This is an organization ID, not an API key
OPENAI_API_KEY = "org-aCINbcM9pgBWpKKFfCoKgdSs"  # Should use os.environ.get("OPENAI_API_KEY")
ADMIN_ID = 1951089207  # Admin chat ID

# OpenAI sozlamalari
openai.api_key = OPENAI_API_KEY

# Bot yaratamiz
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))

# Dispatcher yaratamiz
dp = Dispatcher()

# Foydalanuvchi tillari va xabar vaqtlari uchun lug‘atlar
user_languages = {}
user_last_message_time = {}

# Tilni tanlash tugmalari
lang_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🇺🇿 O'zbekcha"), KeyboardButton(text="🇷🇺 Русский")]
    ],
    resize_keyboard=True
)

# Kontakt yuborish tugmasi
contact_kb_uz = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📞 Kontaktni yuborish", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True
)

contact_kb_ru = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📞 Отправить контакт", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True
)

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "🇺🇿 Tilni tanlang / 🇷🇺 Выберите язык:", 
        reply_markup=lang_kb
    )

@dp.message(F.text.in_(["🇺🇿 O'zbekcha", "🇷🇺 Русский"]))
async def set_language(message: types.Message):
    if message.text == "🇷🇺 Русский":
        user_languages[message.from_user.id] = "ru"
        await message.answer(
            "✍️ Пожалуйста, напишите вашу жалобу или предложение:",
            reply_markup=contact_kb_ru
        )
    else:
        user_languages[message.from_user.id] = "uz"
        await message.answer(
            "✍️ Iltimos, shikoyatingiz yoki taklifingizni yozing:",
            reply_markup=contact_kb_uz
        )

@dp.message(F.text)
async def receive_message(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, "uz")
    now = asyncio.get_event_loop().time()

    if user_id in user_last_message_time:
        time_diff = now - user_last_message_time[user_id]
        if time_diff < 60:
            # ISSUE: Rate limited users should receive feedback
            if lang == "ru":
                await message.answer("⏳ Пожалуйста, подождите минуту перед отправкой нового сообщения.")
            else:
                await message.answer("⏳ Iltimos, yangi xabar yuborishdan oldin bir daqiqa kuting.")
            return

    user_last_message_time[user_id] = now

    admin_text = (
        f"📩 Yangi xabar:\n"
        f"👤 {message.from_user.full_name} ({message.from_user.id})\n"
        f"📝 {message.text}"
    )
    await bot.send_message(ADMIN_ID, admin_text)

    response_text = (
        "✅ Ваша жалоба принята. Пожалуйста, подождите немного.\n"
        "📲 Сохраните @ganiev_s7 и отправьте ваш контакт."
    ) if lang == "ru" else (
        "✅ Sizning shikoyatingiz qabul qilindi. Iltimos, biroz kuting.\n"
        "📲 @ganiev_s7 ni kontaktingizga saqlang va kontaktingizni yuboring."
    )

    await message.answer(response_text)

@dp.message(F.contact)
async def receive_contact(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, "uz")

    contact_info = (
        f"📞 Yangi kontakt:\n"
        f"{message.contact.phone_number}\n"
        f"👤 {message.from_user.full_name}"
    )
    await bot.send_message(ADMIN_ID, contact_info)

    response_text = "✅ Спасибо! Ваш контакт отправлен администратору." if lang == "ru" else "✅ Rahmat! Sizning kontaktingiz adminga yuborildi."
    await message.answer(response_text, reply_markup=ReplyKeyboardRemove())

# ChatGPT bilan ishlovchi funksiya
async def ask_chatgpt(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

@dp.message(F.text)
async def chatgpt_response(message: types.Message):
    user_message = message.text
    chatgpt_reply = await ask_chatgpt(user_message)
    await message.answer(chatgpt_reply)

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
