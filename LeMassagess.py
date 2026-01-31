import asyncio
import calendar
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# Настройка логирования для отслеживания ошибок в Render
logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8309397547:AAFDQpjHbdY8fp5a5MElg-gvFiCTu1JJwI0"
ADMIN_ID = 8530477636 

bot = Bot(token=TOKEN)
dp = Dispatcher()

class Booking(StatesGroup):
    choosing_massage = State()
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_weight = State()
    waiting_for_illness = State()
    confirming_data = State()
    choosing_date = State()

# --- КЛАВИАТУРЫ ---

def main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Записаться")]], 
        resize_keyboard=True
    )

def massage_kb():
    # Твой полный прайс с исправленным Золотым сечением
    prices = [
        ("Общий массаж (2500₽)", "общий"), ("Массаж спины (1200₽)", "спина"),
        ("Массаж ШВЗ (1000₽)", "швз"), ("Золотое сечение (20000₽)", "золотое"),
        ("Турбослим (2000₽)", "турбослим"), ("SPA Экстра (3500₽)", "spa"),
        ("Лицо: Скульптурный (1200₽)", "лицо_ск"), ("Лицо: Пластика (2500₽)", "лицо_пл"),
        ("Ручная липосакция (8000₽)", "липо")
    ]
    buttons = [[InlineKeyboardButton(text=p[0], callback_query_data=f"msg_{p[1]}")] for p in prices]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_calendar_kb(month=None, year=None):
    now = datetime.now()
    month = month or now.month
    year = year or now.year
    kb = []
    
    # Название месяца
    kb.append([InlineKeyboardButton(text=f"{calendar.month_name[month]} {year}", callback_query_data="ignore")])
    
    # Дни недели
    week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    kb.append([InlineKeyboardButton(text=day, callback_query_data="ignore") for day in week_days])
    
    # Генерация сетки календаря
    month_calendar = calendar.monthcalendar(year, month)
    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_query_data="ignore"))
            else:
                # Вс выходной (можно поменять, если работаешь по воскресеньям)
                if calendar.weekday(year, month, day) == 6: 
                    row.append(InlineKeyboardButton(text="❌", callback_query_data="ignore"))
                else:
                    row.append(InlineKeyboardButton(text=str(day), callback_query_data=f"date_{day}_{month}_{year}"))
        kb.append(row)
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- ЛОГИКА ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Добро пожаловать в студию коррекции фигуры Le_Massagess 🤗", 
        reply_markup=main_kb()
    )

@dp.message(F.text == "Записаться")
async def start_booking(message: types.Message, state: FSMContext):
    await message.answer("На какой массаж хотите записаться ?", reply_markup=massage_kb())
    await state.set_state(Booking.choosing_massage)

@dp.callback_query(F.data.startswith("msg_"), Booking.choosing_massage)
async def choose_msg(callback: types.CallbackQuery, state: FSMContext):
    selected_massage = callback.data.split("_")[1]
    await state.update_data(massage=selected_massage)
    await callback.message.answer("Хороший выбор! Напишите свое имя")
    await state.set_state(Booking.waiting_for_name)
    await callback.answer()

@dp.message(Booking.waiting_for_name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Напишите пожалуйста свой возраст")
    await state.set_state(Booking.waiting_for_age)

@dp.message(Booking.waiting_for_age)
async def get_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Напишите пожалуйста свой вес")
    await state.set_state(Booking.waiting_for_weight)

@dp.message(Booking.waiting_for_weight)
async def get_weight(message: types.Message, state: FSMContext):
    await state.update_data(weight=message.text)
    await message.answer("Есть ли у вас противопоказания или какие-то болезни?")
    await state.set_state(Booking.waiting_for_illness)

@dp.message(Booking.waiting_for_illness)
async def confirm_step(message: types.Message, state: FSMContext):
    data = await state.update_data(illness=message.text)
    summary = f"Имя: {data['name']}, Возраст: {data['age']}, Вес: {data['weight']}, Услуга: {data['massage']}"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_query_data="conf_yes"),
         InlineKeyboardButton(text="Нет", callback_query_data="conf_no")]
    ])
    await message.answer(f"Проверьте данные:\n{summary}\n\nВсё верно?", reply_markup=kb)
    await state.set_state(Booking.confirming_data)

@dp.callback_query(F.data == "conf_yes", Booking.confirming_data)
async def date_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Выберите дату на запись:", reply_markup=get_calendar_kb())
    await state.set_state(Booking.choosing_date)
    await callback.answer()

@dp.callback_query(F.data == "conf_no", Booking.confirming_data)
async def retry(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Давайте начнем сначала. На какой массаж хотите записаться ?", reply_markup=massage_kb())
    await state.set_state(Booking.choosing_massage)
    await callback.answer()

@dp.callback_query(F.data.startswith("date_"), Booking.choosing_date)
async def final_step(callback: types.CallbackQuery, state: FSMContext):
    d, m, y = callback.data.split("_")[1:]
    date_str = f"{d}.{m}.{y}"
    data = await state.get_data()
    
    await callback.message.answer("Ваша заявка принята! Прямо сейчас администратор проверяет, свободна ли дата🤩")
    
    # Отправка АДМИНУ
    username = f"@{callback.from_user.username}" if callback.from_user.username else "нет ника"
    admin_text = (f"🔥 НОВАЯ ЗАЯВКА!\n"
                  f"👤 Имя: {data['name']}\n"
                  f"🎂 Возраст: {data['age']}\n"
                  f"⚖️ Вес: {data['weight']}\n"
                  f"⚠️ Здоровье: {data['illness']}\n"
                  f"💆 Массаж: {data['massage']}\n"
                  f"📅 Дата: {date_str}\n"
                  f"🔗 Профиль: {username}")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Принять ✅", callback_query_data=f"adm_acc_{callback.from_user.id}"),
         InlineKeyboardButton(text="Отклонить ❌", callback_query_data=f"adm_rej_{callback.from_user.id}")]
    ])
    
    await bot.send_message(ADMIN_ID, admin_text, reply_markup=kb)
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data.startswith("adm_"))
async def admin_decision(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    
    parts = callback.data.split("_")
    action = parts[1]
    user_id = parts[2]
    
    if action == "acc":
        await bot.send_message(user_id, "✅ Ваша заявка одобрена! Ждем вас по адресу: Макаренко 4В, МедТест, 2 этаж, 201 помещение.")
        await callback.message.edit_text(callback.message.text + "\n\n✅ СТАТУС: ПРИНЯТО")
    else:
        await bot.send_message(user_id, "❌ Ваша заявка отклонена. Причина: На это время запись уже занята.")
        await callback.message.edit_text(callback.message.text + "\n\n❌ СТАТУС: ОТКЛОНЕНО")
    await callback.answer()

async def main():
    # Удаляем вебхуки, чтобы не было конфликтов
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
