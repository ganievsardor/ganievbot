import asyncio
import logging
import time
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Text
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.fsm.storage.memory import MemoryStorage

# Bot tokeni va admin ID (integer) ni sozlang:
TOKEN = "6367097370:AAHjerMmugPyfJS19n-8TgFVe8ym0fUzA54"
ADMIN_ID = 1951089207

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Global lug'at: foydalanuvchi ID -> { 'start_time': timestamp, 'complaints': [matnlar], 'task': asyncio.Task }
pending_complaints = {}

# /start buyrug‘i: Til tanlovi inline tugmalari bilan
@dp.message(Command("start"))
async def start_command(message: Message):
    lang_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="Русский", callback_data="lang_ru")]
    ])
    await message.answer("Assalomu alaykum! Iltimos, tilni tanlang:", reply_markup=lang_keyboard)

# Til tanlovi handler
@dp.callback_query(Text(startswith="lang_"))
async def language_selection(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    if lang == "uz":
        response = "O'zbekcha tanlandi. Agar talab va takliflaringiz bo'lsa, quyidagi tugmani bosing."
    elif lang == "ru":
        response = "Вы выбрали русский язык. Если у вас есть предложения или жалобы, нажмите кнопку ниже."
    complaint_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Talab va Takliflaringiz", callback_data="complaint")]
    ])
    await callback.message.answer(response, reply_markup=complaint_keyboard)
    await callback.answer()

# "Talab va Takliflaringiz" tugmasi bosilganda – pending rejimga o‘tish
@dp.callback_query(Text(equals="complaint"))
async def complaint_button_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    # Agar foydalanuvchi pending rejimda emas, yangi entry yaratiladi
    if user_id not in pending_complaints:
        pending_complaints[user_id] = {
            'start_time': time.time(),
            'complaints': [],
            'task': asyncio.create_task(process_complaints(user_id, callback.message.chat.id))
        }
    await callback.message.answer("Iltimos, talab va takliflaringizni yozib qoldiring:")
    await callback.answer()

# Pending rejimda bo'lgan foydalanuvchilarning xabarlari shu handler orqali yig‘iladi
@dp.message()
async def handle_pending_complaint(message: Message):
    user_id = message.from_user.id
    if user_id in pending_complaints:
        pending_complaints[user_id]['complaints'].append(message.text)
        # Xabar qabul qilindi degan javob yuborilmasin – faqat yig‘ilsin
        return
    else:
        await message.answer("Noma'lum buyruq. Iltimos, /help buyrug'ini yuboring.")

# 60 soniya kutib, pending shikoyatlar yig‘ilib admin ga yuboriladi va foydalanuvchiga javob keladi
async def process_complaints(user_id: int, chat_id: int):
    await asyncio.sleep(60)  # 60 soniya kutish
    data = pending_complaints.pop(user_id, None)
    if data and data['complaints']:
        combined_text = "\n---\n".join(data['complaints'])
        try:
            await bot.send_message(ADMIN_ID, f"Foydalanuvchi {user_id} shikoyatlari:\n{combined_text}")
        except Exception as e:
            logging.error(f"Forward qilishda xatolik: {e}")
    confirmation_text = ("Sizning shikoyatingiz qabul qilindi. Iltimos, biroz kuting. "
                         "@ganiev_s7 ni kontaktizga saqlang qilib yuboring va kontaktingizni yuboring.")
    contact_button = KeyboardButton(text="Kontakt yuborish", request_contact=True)
    reply_keyboard = ReplyKeyboardMarkup(keyboard=[[contact_button]], resize_keyboard=True, one_time_keyboard=True)
    try:
        await bot.send_message(chat_id, confirmation_text, reply_markup=reply_keyboard)
    except Exception as e:
        logging.error(f"Xatolik: {e}")

# /help: Yordam buyrug‘i
@dp.message(Command("help"))
async def help_command(message: Message):
    help_text = (
        "/start - Botni boshlash va til tanlovi\n"
        "/contact - Kontakt ma'lumotlari"
    )
    await message.answer(help_text)

# /contact: Kontakt yuborish uchun reply keyboard
@dp.message(Command("contact"))
async def contact_command(message: Message):
    contact_button = KeyboardButton(text="Kontakt yuborish", request_contact=True)
    reply_keyboard = ReplyKeyboardMarkup(keyboard=[[contact_button]], resize_keyboard=True, one_time_keyboard=True)
    await message.answer("Iltimos, kontakt raqamingizni yuboring:", reply_markup=reply_keyboard)

# Kontaktni qabul qilish
@dp.message(content_types=types.ContentType.CONTACT)
async def handle_contact(message: Message):
    contact = message.contact.phone_number
    await message.answer(f"Kontakt qabul qilindi: {contact}")
    try:
        await bot.send_message(ADMIN_ID, f"Foydalanuvchi {message.from_user.full_name} (ID: {message.from_user.id}) kontaktini yubordi: {contact}")
    except Exception as e:
        logging.error(f"Kontakt adminga yuborishda xatolik: {e}")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if name == "__main__":
    asyncio.run(main())
