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
TOKEN = "6367097370:AAHjerMmugPyfJS19n-8TgFVe8ym0fUzA54"  
OPENAI_API_KEY = "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"  
ADMIN_ID = 1951089207  

openai.api_key = OPENAI_API_KEY
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

user_languages = {}
user_sent_contact = {}

# Til tanlash tugmalari
lang_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🇺🇿 O'zbekcha"), KeyboardButton(text="🇷🇺 Русский")]
    ],
    resize_keyboard=True
)

# Kontakt yuborish va GanievGPT tugmasi
def get_contact_keyboard(lang):
    if lang == "ru":
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📞 Отправить контакт", request_contact=True)],
                [KeyboardButton(text="🤖 GanievGPT")]
            ],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📞 Kontaktni yuborish", request_contact=True)],
                [KeyboardButton(text="🤖 GanievGPT")]
            ],
            resize_keyboard=True
        )

# GanievGPT tugmasi alohida
ganiev_gpt_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🤖 GanievGPT")]],
    resize_keyboard=True
)

# /start komandasi
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "🇺🇿 Tilni tanlang / 🇷🇺 Выберите язык:", 
        reply_markup=lang_kb
    )

# Tilni tanlash
@dp.message(F.text.in_(["🇺🇿 O'zbekcha", "🇷🇺 Русский"]))
async def set_language(message: types.Message):
    user_languages[message.from_user.id] = "ru" if message.text == "🇷🇺 Русский" else "uz"
    user_sent_contact[message.from_user.id] = False  # Foydalanuvchi hali kontakt yubormagan
    lang = user_languages[message.from_user.id]

    text = "✍️ Пожалуйста, напишите вашу жалобу или предложение:" if lang == "ru" else "✍️ Iltimos, shikoyatingiz yoki taklifingizni yozing:"
    await message.answer(text, reply_markup=get_contact_keyboard(lang))

# Foydalanuvchi shikoyat yoki taklif yozishi
@dp.message(F.text)
async def receive_message(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, "uz")

    if message.text == "🤖 GanievGPT":
        await message.answer("📝 Savolingizni yozing, men sizga javob beraman.")
        return

    admin_text = f"📩 Yangi xabar:\n👤 {message.from_user.full_name} ({message.from_user.id})\n📝 {message.text}"
    await bot.send_message(ADMIN_ID, admin_text)

    response_text = "✅ Ваша жалоба принята. Пожалуйста, подождите немного." if lang == "ru" else "✅ Sizning shikoyatingiz qabul qilindi. Iltimos, biroz kuting."
    await message.answer(response_text)

# /GanievGPT komandasi
@dp.message(Command("GanievGPT"))
async def ganiev_gpt_cmd(message: types.Message):
    await message.answer("📝 Savolingizni yozing, men sizga javob beraman.", reply_markup=ganiev_gpt_kb)

# ChatGPT bilan ishlovchi funksiya
@dp.message(F.text)
async def chat_with_ganievgpt(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, "uz")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message.text}]
        )
        answer = response["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"OpenAI API xatosi: {e}")
        answer = "❌ GanievGPT bilan bog‘lanib bo‘lmadi. Iltimos, kuting va qaytadan urinib ko‘ring." if lang == "uz" else "❌ Не удалось подключиться к GanievGPT. Пожалуйста, подождите и попробуйте снова."

    await message.answer(answer)

# Foydalanuvchi kontakt yuborganda
@dp.message(F.contact)
async def receive_contact(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, "uz")

    # Faqat bir marta kontakt yuborish
    if user_sent_contact.get(user_id, False):
        return

    user_sent_contact[user_id] = True  # Foydalanuvchi kontakt yubordi

    contact_info = f"📞 Yangi kontakt:\n{message.contact.phone_number}\n👤 {message.from_user.full_name}"
    await bot.send_message(ADMIN_ID, contact_info)

    response_text = "✅ Спасибо! Ваш контакт отправлен администратору." if lang == "ru" else "✅ Rahmat! Sizning kontaktingiz adminga yuborildi."
    
    # Faqat GanievGPT tugmasini qoldiramiz
    await message.answer(response_text, reply_markup=ganiev_gpt_kb)

# Botni ishga tushirish
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
