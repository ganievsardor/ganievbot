mport asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardRemove
)

TOKEN = "6367097370:AAHjerMmugPyfJS19n-8TgFVe8ym0fUzA54"
ADMIN_ID = 1951089207  # Admin chat ID

# Bot yaratamiz
bot = Bot(token=TOKEN, parse_mode="HTML")

# Dispatcher yaratamiz
dp = Dispatcher()

# Foydalanuvchi tillari va xabarlar uchun lug'atlar
user_languages = {}
user_messages = {}  # Foydalanuvchi xabarlarini saqlash uchun
user_waiting_tasks = {}  # Kutish vazifalarini saqlash uchun

# Tilni tanlash tugmalari
lang_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🇺🇿 O'zbekcha"), KeyboardButton(text="🇷🇺 Русский")]
    ],
    resize_keyboard=True
)

# Kontakt yuborish tugmalari
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
    user_id = message.from_user.id

    if message.text == "🇷🇺 Русский":
        user_languages[user_id] = "ru"
        await message.answer(
            "✍️ Пожалуйста, напишите вашу жалобу или предложение:",
            reply_markup=contact_kb_ru
        )
    else:
        user_languages[user_id] = "uz"
        await message.answer(
            "✍️ Iltimos, shikoyatingiz yoki taklifingizni yozing:",
            reply_markup=contact_kb_uz
        )

@dp.message(F.text)
async def receive_message(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, "uz")

    # Tilni tanlash menyusi xabarlariga javob bermang
    if message.text in ["🇺🇿 O'zbekcha", "🇷🇺 Русский"]:
        return

    # Xabarlarni saqlaymiz
    if user_id in user_messages:
        # Mavjud xabarlarga yangi xabar qo'shish
        user_messages[user_id].append(message.text)

        # Foydalanuvchiga xabar qo'shilganligini bildirish
        confirmation = "✓ Xabar qo'shildi" if lang == "uz" else "✓ Сообщение добавлено"
        await message.answer(confirmation)
    else:
        # Yangi foydalanuvchi uchun xabarlar ro'yxati
        user_messages[user_id] = [message.text]

        # Foydalanuvchiga bildirish
        info_text = "✅ Xabaringiz qabul qilindi. 60 soniya davomida yana ma'lumot qo'shishingiz mumkin." if lang == "uz" else \
                   "✅ Ваше сообщение принято. В течение 60 секунд вы можете добавить дополнительную информацию."
        await message.answer(info_text)

        # Kutish vazifasini yaratish
        if user_id in user_waiting_tasks:
            user_waiting_tasks[user_id].cancel()
        user_waiting_tasks[user_id] = asyncio.create_task(process_after_delay(user_id, message))

# Xabarlarni yuborish (60 soniyadan keyin)
async def process_after_delay(user_id, message):
    try:
        # 60 soniya kutish
        await asyncio.sleep(60)

        # Foydalanuvchi xabarlarini olish
        messages = user_messages.get(user_id, [])
        if not messages:
            return

        # Barcha xabarlarni bir xabar ichiga birlashtirish
        full_text = "\n\n".join(messages)
        lang = user_languages.get(user_id, "uz")

        # Adminga yuborish
        admin_text = f"📩 Yangi xabar:\n👤 {message.from_user.full_name} ({message.from_user.id})\n📝 {full_text}"
        await bot.send_message(ADMIN_ID, admin_text)

        # Foydalanuvchiga javob
        if lang == "ru":
            response_text = "✅ Ваше сообщение принято. Пожалуйста, подождите немного.\n📲 Сохраните @ganiev_s7 и отправьте ваш контакт."
        else:
            response_text = "✅ Sizning xabaringiz qabul qilindi. Iltimos, biroz kuting.\n📲 @ganiev_s7 ni kontaktingizga saqlang va kontaktingizni yuboring."

        # Mos klaviatura tanlash
        kb = contact_kb_ru if lang == "ru" else contact_kb_uz
        await bot.send_message(user_id, response_text, reply_markup=kb)

        # Ma'lumotlarni tozalash
        if user_id in user_messages:
            del user_messages[user_id]
    except Exception as e:
        logging.error(f"Error in processing messages: {e}")
    finally:
        # Har qanday holatda vazifani tozalash
        if user_id in user_waiting_tasks:
            del user_waiting_tasks[user_id]

@dp.message(F.contact)
async def receive_contact(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, "uz")

    contact_info = (
        f"📞 Yangi kontakt:\n"
        f"{message.contact.phone_number}\n"
        f"👤 {message.from_user.full_name} ({message.from_user.id})"
    )
    await bot.send_message(ADMIN_ID, contact_info)

    # Foydalanuvchiga javob va menyuni olib tashlash
    response_text = "✅ Rahmat! Sizning kontaktingiz adminga yuborildi." if lang == "uz" else \
                    "✅ Спасибо! Ваш контакт отправлен администратору."

    await message.answer(response_text, reply_markup=ReplyKeyboardRemove())

async def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
