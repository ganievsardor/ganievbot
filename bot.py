import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = "6367097370:AAHjerMmugPyfJS19n-8TgFVe8ym0fUzA54"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("Assalomu alaykum! Agar siz G’aniyev Sardor bilan gaplashmoqchi bo‘lsangiz, @Ganiev_S7 kontaktizga saqlang va kuting.")

@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer(
        "Bu bot sizga G’aniyev Sardor bilan bog‘lanish uchun yordam beradi.\n\n"
        "/start - Botni boshlash\n"
        "/contact - Kontakt olish"
    )

@dp.message(Command("contact"))
async def contact_command(message: types.Message):
    await message.answer("G’aniyev Sardor bilan bog‘lanish uchun @Ganiev_S7 kontaktizga saqlang va kuting.")

@dp.message()
async def handle_text_messages(message: types.Message):
    text_lower = message.text.lower()
    if "salom" in text_lower:
        await message.answer("Va alaykum salom! Qanday yordam kerak?")
    else:
        await message.answer("Siz nimadir yozdingiz, lekin tushunmadim. /help buyrug‘ini ko‘rib chiqing.")

async def main():
    await dp.start_polling(bot)

if name == "__main__":
    asyncio.run(main())
