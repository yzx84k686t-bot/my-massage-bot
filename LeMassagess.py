import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# Логирование
logging.basicConfig(level=logging.INFO)

# --- НАСТРОЙКИ ---
TOKEN = "8309397547:AAFDQpjHbdY8fp5a5MElg-gvFiCTu1JJwI0"
ADMIN_ID = 8530477636 

bot = Bot(token=TOKEN)
dp = Dispatcher()
last_client_id = {}

# --- СОСТОЯНИЯ ---
class Booking(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_weight = State()
    waiting_for_height = State()
    waiting_for_illness = State()
    choosing_massage = State()
    waiting_for_date = State()

class AdminAction(StatesGroup):
    waiting_for_reject_reason = State()

# --- КЛАВИАТУРЫ ---
def get_start_kb():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Записаться на сеанс ✨")]], resize_keyboard=True)

def get_massage_types_kb():
    kb = [
        [KeyboardButton(text="🌿 Общий массаж (2500₽)"), KeyboardButton(text="💆‍♂️ Спина (1500₽)")],
        [KeyboardButton(text="☁️ Массаж ШВЗ (1000₽)"), KeyboardButton(text="✨ Лицо (1200₽)")],
        [KeyboardButton(text="🔥 Антицеллюлитный (2200₽)"), KeyboardButton(text="💧 Лимфодренажный (2000₽)")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)

def get_admin_choice_kb():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Принять ✅"), KeyboardButton(text="Отклонить ❌")]], resize_keyboard=True)

# --- ХЕНДЛЕРЫ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    # Приветственный стикер (котик или лапки)
    await message.answer_sticker("CAACAgIAAxkBAAEL6ZxmE-9vAAGB-Z_XG0W6S9I9S-R_AAIBAAOCvjYMAAFlU9_Y_V-0NAQ")
    await message.answer(
        f"Здравствуйте, {message.from_user.first_name}! ✨\n\n"
        "Добро пожаловать в уютный мир **Le Massagess**. "
        "Я помогу вам выбрать услугу и записаться на сеанс заботы о себе. "
        "Хотите расслабиться и восстановить силы?",
        parse_mode="Markdown",
        reply_markup=get_start_kb()
    )

@dp.message(F.text == "Записаться на сеанс ✨")
async def start_booking(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Замечательный выбор! 🌸\nДля начала, подскажите, как я могу к вам обращаться?", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Booking.waiting_for_name)

@dp.message(Booking.waiting_for_name)
async def step_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(f"Очень приятно, {message.text}! 😊\nА сколько вам полных лет?")
    await state.set_state(Booking.waiting_for_age)

@dp.message(Booking.waiting_for_age)
async def step_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Принято! Подскажите, пожалуйста, ваш примерный вес (кг) и рост (см)? Это поможет мастеру подготовиться.")
    await state.set_state(Booking.waiting_for_weight)

@dp.message(Booking.waiting_for_weight)
async def step_weight(message: types.Message, state: FSMContext):
    await state.update_data(weight=message.text)
    await message.answer("И ваш рост?")
    await state.set_state(Booking.waiting_for_height)

@dp.message(Booking.waiting_for_height)
async def step_height(message: types.Message, state: FSMContext):
    await state.update_data(height=message.text)
    await message.answer("Почти готово! 🕊 Есть ли какие-то особенности здоровья или противопоказания, о которых нам важно знать?")
    await state.set_state(Booking.waiting_for_illness)

@dp.message(Booking.waiting_for_illness)
async def step_ill(message: types.Message, state: FSMContext):
    await state.update_data(illness=message.text)
    await message.answer("Выберите массаж, который подарит вам легкость:", reply_markup=get_massage_types_kb())
    await state.set_state(Booking.choosing_massage)

@dp.message(Booking.choosing_massage)
async def step_type(message: types.Message, state: FSMContext):
    await state.update_data(massage=message.text)
    await message.answer("И последний шаг: на какой день и время вам было бы удобно записаться?")
    await state.set_state(Booking.waiting_for_date)

@dp.message(Booking.waiting_for_date)
async def step_final(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user = message.from_user
    
    # Исправленный блок ника
    username_text = f"@{user.username}" if user.username else f"[{user.first_name}](tg://user?id={user.id})"
    last_client_id[ADMIN_ID] = user.id
    
    admin_msg = (
        f"🌿 **НОВАЯ ЗАПИСЬ В SALON**\n"
        f"━━━━━━━━━━━━━━\n"
        f"👤 **Имя:** {data['name']}\n"
        f"🔗 **Контакт:** {username_text}\n"
        f"🎂 **Возраст:** {data['age']}\n"
        f"📏 **Данные:** {data['weight']}кг / {data['height']}см\n"
        f"⚠️ **Здоровье:** {data['illness']}\n"
        f"💆 **Услуга:** {data['massage']}\n"
        f"📅 **Желаемое время:** {message.text}\n"
        f"━━━━━━━━━━━━━━"
    )
    
    await bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown", reply_markup=get_admin_choice_kb())
    await message.answer_sticker("CAACAgIAAxkBAAEL6ZxmE-9vAAGB-Z_XG0W6S9I9S-R_AAIBAAOCvjYMAAFlU9_Y_V-0NAQ") # Повтор стикера или другой добрый
    await message.answer("Спасибо за доверие! ❤️ Ваша заявка передана мастеру. Я сразу напишу вам, как только она будет подтверждена.", reply_markup=get_start_kb())
    await state.clear()

# --- АДМИН-ПАНЕЛЬ ---

@dp.message(F.text == "Принять ✅")
async def admin_ok(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    cid = last_client_id.get(ADMIN_ID)
    if cid:
        await bot.send_message(cid, "🌿 Чудесные новости! Ваша запись подтверждена. Мы уже очень ждем вас!")
        await message.answer("Клиент получил доброе уведомление! ✅")

@dp.message(F.text == "Отклонить ❌")
async def admin_no_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("Напишите, пожалуйста, причину, чтобы мы могли вежливо объяснить ситуацию клиенту:")
    await state.set_state(AdminAction.waiting_for_reject_reason)

@dp.message(AdminAction.waiting_for_reject_reason)
async def admin_no_final(message: types.Message, state: FSMContext):
    reason = message.text
    cid = last_client_id.get(ADMIN_ID)
    if cid:
        await bot.send_message(cid, f"🙏 К сожалению, на этот раз не получается записаться.\nПричина: {reason}\n\nНо мы будем очень рады видеть вас в другое время!")
    await message.answer("Уведомление отправлено ❌")
    await state.clear()

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())