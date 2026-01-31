import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8309397547:AAFDQpjHbdY8fp5a5MElg-gvFiCTu1JJwI0"
ADMIN_ID = 8530477636 

bot = Bot(token=TOKEN)
dp = Dispatcher()
last_client_id = {}

# --- СОСТОЯНИЯ ---
class Booking(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_weight_height = State()
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
        [KeyboardButton(text="🔥 Антицеллюлитный (2200₽)"), KeyboardButton(text="💧 Лимфодренажный (2000₽)")],
        [KeyboardButton(text="🦶 Массаж стоп (800₽)"), KeyboardButton(text="🦾 Руки полностью (900₽)")],
        [KeyboardButton(text="🏆 Курс «Золотое сечение» (20000₽)")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)

def get_admin_choice_kb():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Принять ✅"), KeyboardButton(text="Отклонить ❌")]], resize_keyboard=True)

# --- ХЕНДЛЕРЫ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Здравствуйте, {message.from_user.first_name}! ✨\n\n"
        "Добро пожаловать в **Le Massagess**. Позвольте себе отдых и восстановление. 🌸",
        reply_markup=get_start_kb()
    )

@dp.message(F.text == "Записаться на сеанс ✨")
async def start_booking(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Прекрасный выбор! Как я могу к вам обращаться?", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Booking.waiting_for_name)

@dp.message(Booking.waiting_for_name)
async def step_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(f"Приятно познакомиться, {message.text}! Сколько вам полных лет?")
    await state.set_state(Booking.waiting_for_age)

@dp.message(Booking.waiting_for_age)
async def step_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Ваш примерный вес и рост (кг/см)?")
    await state.set_state(Booking.waiting_for_weight_height)

@dp.message(Booking.waiting_for_weight_height)
async def step_wh(message: types.Message, state: FSMContext):
    await state.update_data(wh=message.text)
    await message.answer("Есть ли травмы или противопоказания?")
    await state.set_state(Booking.waiting_for_illness)

@dp.message(Booking.waiting_for_illness)
async def step_ill(message: types.Message, state: FSMContext):
    await state.update_data(illness=message.text)
    await message.answer("Выберите услугу или курс:", reply_markup=get_massage_types_kb())
    await state.set_state(Booking.choosing_massage)

@dp.message(Booking.choosing_massage)
async def step_type(message: types.Message, state: FSMContext):
    await state.update_data(massage=message.text)
    await message.answer("Укажите удобную дату и время для записи:")
    await state.set_state(Booking.waiting_for_date)

@dp.message(Booking.waiting_for_date)
async def step_final(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user = message.from_user
    username = f"@{user.username}" if user.username else f"ID: {user.id}"
    last_client_id[ADMIN_ID] = user.id
    
    admin_msg = (
        f"🌿 **НОВАЯ ЗАЯВКА**\n"
        f"━━━━━━━━━━━━━━\n"
        f"👤 Имя: {data['name']}\n"
        f"🔗 Контакт: {username}\n"
        f"🎂 Возраст: {data['age']}\n"
        f"📏 Параметры: {data['wh']}\n"
        f"⚠️ Здоровье: {data['illness']}\n"
        f"💆 Услуга: {data['massage']}\n"
        f"📅 Время: {message.text}\n"
        f"━━━━━━━━━━━━━━"
    )
    
    await bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown", reply_markup=get_admin_choice_kb())
    await message.answer("✅ Ваша заявка отправлена мастеру! Скоро я пришлю вам ответ.", reply_markup=get_start_kb())
    await state.clear()

# --- АДМИН-ПАНЕЛЬ ---

@dp.message(F.text == "Принять ✅")
async def admin_ok(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    cid = last_client_id.get(ADMIN_ID)
    if cid:
        await bot.send_message(cid, "🌿 Запись подтверждена! Ждем вас в назначенное время.")
        await message.answer("Клиент уведомлен! ✅")

@dp.message(F.text == "Отклонить ❌")
async def admin_no_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("Введите причину отклонения:")
    await state.set_state(AdminAction.waiting_for_reject_reason)

@dp.message(AdminAction.waiting_for_reject_reason)
async def admin_no_final(message: types.Message, state: FSMContext):
    reason = message.text
    cid = last_client_id.get(ADMIN_ID)
    if cid:
        await bot.send_message(cid, f"🙏 К сожалению, запись отклонена.\nПричина: {reason}")
    await message.answer("Отказ отправлен ❌")
    await state.clear()

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
