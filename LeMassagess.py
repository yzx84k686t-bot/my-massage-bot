import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# Логирование для Render
logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8309397547:AAFDQpjHbdY8fp5a5MElg-gvFiCTu1JJwI0"
ADMIN_ID = 8530477636 

bot = Bot(token=TOKEN)
dp = Dispatcher()
last_client_id = {} # Для связи админа с клиентом

class Booking(StatesGroup):
    waiting_for_massage = State()
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_weight = State()
    waiting_for_illness = State()
    waiting_for_date = State()

# --- КЛАВИАТУРЫ (ТОЛЬКО ТЕКСТОВЫЕ) ---

def get_main_kb():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Записаться")]], resize_keyboard=True)

def get_massage_kb():
    kb = [
        [KeyboardButton(text="Общий массаж (2500₽)"), KeyboardButton(text="Массаж спины (1200₽)")],
        [KeyboardButton(text="Массаж ШВЗ (1000₽)"), KeyboardButton(text="Золотое сечение (20000₽)")],
        [KeyboardButton(text="Турбослим (2000₽)"), KeyboardButton(text="SPA Экстра (3500₽)")],
        [KeyboardButton(text="Лицо: Скульптурный (1200₽)"), KeyboardButton(text="Лицо: Пластика (2500₽)")],
        [KeyboardButton(text="Ручная липосакция (8000₽)")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)

def get_admin_kb():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Принять ✅"), KeyboardButton(text="Отклонить ❌")]], resize_keyboard=True)

# --- ЛОГИКА ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Добро пожаловать в студию Le_Massagess!", reply_markup=get_main_kb())

@dp.message(F.text == "Записаться")
async def start_booking(message: types.Message, state: FSMContext):
    await message.answer("Выберите вид массажа:", reply_markup=get_massage_kb())
    await state.set_state(Booking.waiting_for_massage)

@dp.message(Booking.waiting_for_massage)
async def get_massage(message: types.Message, state: FSMContext):
    await state.update_data(massage=message.text)
    await message.answer("Напишите ваше имя:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Booking.waiting_for_name)

@dp.message(Booking.waiting_for_name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Ваш возраст?")
    await state.set_state(Booking.waiting_for_age)

@dp.message(Booking.waiting_for_age)
async def get_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Ваш вес?")
    await state.set_state(Booking.waiting_for_weight)

@dp.message(Booking.waiting_for_weight)
async def get_weight(message: types.Message, state: FSMContext):
    await state.update_data(weight=message.text)
    await message.answer("Есть ли противопоказания?")
    await state.set_state(Booking.waiting_for_illness)

@dp.message(Booking.waiting_for_illness)
async def get_ill(message: types.Message, state: FSMContext):
    await state.update_data(illness=message.text)
    await message.answer("Напишите желаемую дату и время:")
    await state.set_state(Booking.waiting_for_date)

@dp.message(Booking.waiting_for_date)
async def final_step(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user = message.from_user
    last_client_id[ADMIN_ID] = user.id # Запоминаем ID клиента для админа
    
    admin_text = (f"🔥 НОВАЯ ЗАЯВКА!\n"
                  f"👤 Имя: {data['name']}\n"
                  f"🎂 Возраст: {data['age']}\n"
                  f"⚖️ Вес: {data['weight']}\n"
                  f"💆 Массаж: {data['massage']}\n"
                  f"📅 Дата: {message.text}\n"
                  f"🔗 Профиль: @{user.username if user.username else 'нет'}")

    await bot.send_message(ADMIN_ID, admin_text, reply_markup=get_admin_kb())
    await message.answer("Заявка отправлена! Мастер скоро ответит.", reply_markup=get_main_kb())
    await state.clear()

# --- АДМИНКА ---

@dp.message(F.text == "Принять ✅")
async def admin_accept(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    client_id = last_client_id.get(ADMIN_ID)
    if client_id:
        await bot.send_message(client_id, "✅ Ваша заявка одобрена! Ждем вас по адресу: Макаренко 4В, МедТест, 2 этаж, 201 помещение.")
        await message.answer("Клиент уведомлен.")

@dp.message(F.text == "Отклонить ❌")
async def admin_reject(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    client_id = last_client_id.get(ADMIN_ID)
    if client_id:
        await bot.send_message(client_id, "❌ Извините, на это время запись уже занята.")
        await message.answer("Отказ отправлен.")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
