import asyncio
import aiohttp
import logging
import os
from dotenv import load_dotenv
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_languages = {}



class ConvertSteps(StatesGroup):
    from_currency = State()
    to_currency = State()
    amount = State()



@dp.message(CommandStart())
async def start_command(message: Message):
    kb = [
        [KeyboardButton(text="💱 Quick Converter")],
        [KeyboardButton(text="⭐ Favourite Rates")],
        [KeyboardButton(text="🌐 Language Selection")]
    ]

    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Select a section..."
    )

    await message.answer(
        f"Hello, {message.from_user.first_name}! 👋\n\n"
        f"I am a currency converter bot powered by ExchangeRate-API.\n"
        f"I can help you quickly convert amounts or track your favorite currencies.\n\n"
        f"Please select an option from the menu below 👇",
        reply_markup=keyboard
    )



@dp.message(F.text.in_(["🌐 Language Selection", "🌐 Выбор языка", "🌐 Sprachauswahl"]))
async def language_menu(message: Message):
    kb = [
        [KeyboardButton(text="English")],
        [KeyboardButton(text="Русский")],
        [KeyboardButton(text="Deutsch")]
    ]

    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

    await message.answer(
        "Please, select your language:",
        reply_markup=keyboard
    )



@dp.message(F.text == "Русский")
async def set_russian(message: Message):
    user_languages[message.from_user.id] = "ru"

    kb = [
        [KeyboardButton(text="💱 Быстрый конвертер")],
        [KeyboardButton(text="⭐ Избранные курсы")],
        [KeyboardButton(text="🌐 Выбор языка")]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

    await message.answer(
        "Язык изменен на русский!\n"
        "Что вы хотите сделать дальше?",
        reply_markup=keyboard
    )



@dp.message(F.text == "English")
async def set_english(message: Message):
    user_languages[message.from_user.id] = "en"
    kb = [
        [KeyboardButton(text="💱 Quick Converter")],
        [KeyboardButton(text="⭐ Favorite Rates")],
        [KeyboardButton(text="🌐 Language Selection")]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

    await message.answer(
        "Language changed to English!\n"
        "What would you like to do next?",
        reply_markup=keyboard
    )



@dp.message(F.text == "Deutsch")
async def set_german(message: Message):
    user_languages[message.from_user.id] = "de"

    kb = [
        [KeyboardButton(text="💱 Schneller Konverter")],
        [KeyboardButton(text="⭐ Bevorzugte Kurse")],
        [KeyboardButton(text="🌐 Sprachauswahl")]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

    await message.answer(
        "Sprache auf Deutsch umgestellt!\n"
        "Was möchten Sie als Nächstes tun?",
        reply_markup=keyboard
    )



@dp.message(F.text.in_(["💱 Quick Converter", "💱 Быстрый конвертер", "💱 Schneller Konverter"]))
async def start_converter(message: Message, state: FSMContext):
    lang = user_languages.get(message.from_user.id, "en")

    texts = {
        "en": "Select or type the **first currency** (the one you want to convert FROM), e.g., USD:",
        "ru": "Выберите или введите **первую валюту** (которую хотите перевести), например, USD:",
        "de": "Wählen oder schreiben Sie die **erste Währung** (die Sie уmrechnen möchten), z.B. USD:"
    }

    kb = [
        [KeyboardButton(text="USD"), KeyboardButton(text="EUR")],
        [KeyboardButton(text="RUB"), KeyboardButton(text="CNY")],
        [KeyboardButton(text="GBP"), KeyboardButton(text="JPY")],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    await state.set_state(ConvertSteps.from_currency)
    await message.answer(texts[lang], reply_markup=keyboard)



@dp.message(ConvertSteps.from_currency)
async def process_from_currency(message: Message, state: FSMContext):
    lang = user_languages.get(message.from_user.id, "en")

    currency_input = message.text.upper().strip()

    if len(currency_input) != 3 or not currency_input.isalpha():
        error_texts = {
            "en": "❌ Invalid format. Please enter a 3-letter currency code (e.g., USD, EUR):",
            "ru": "❌ Неверный формат. Пожалуйста, введите 3-буквенный код валюты (например, USD, EUR):",
            "de": "❌ Ungültiges Format. Bitte geben Sie einen 3-stelligen Währungscode ein (z. B. USD, EUR):"
        }
        await message.answer(error_texts[lang])
        return

    await state.update_data(from_currency=currency_input)

    texts = {
        "en": f"Great! You selected **{currency_input}**.\nNow, select or type the **second currency** (the one you want to convert TO):",
        "ru": f"Отлично! Вы выбрали **{currency_input}**.\nТеперь выберите или введите **вторую валюту** (в которую переводим):",
        "de": f"Super! Sie haben **{currency_input}** ausgewählt.\nWählen oder schreiben Sie nun die **zweite Währung**:"
    }

    kb_symbols = ["USD", "EUR", "RUB", "CNY", "GBP", "GPY"]
    if currency_input in kb_symbols:
        kb_symbols.remove(currency_input)

    kb = [
        [KeyboardButton(text=kb_symbols[0]), KeyboardButton(text=kb_symbols[1])],
        [KeyboardButton(text=kb_symbols[2]), KeyboardButton(text=kb_symbols[3]),],
        [KeyboardButton(text=kb_symbols[4])]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    await state.set_state(ConvertSteps.to_currency)
    await message.answer(texts[lang], reply_markup=keyboard)



async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())