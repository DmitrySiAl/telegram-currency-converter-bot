import asyncio
import aiohttp
import logging
import os
from dotenv import load_dotenv
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_languages = {}



RATES_DATA = {
        "USD": 86.59,
        "EUR": 100.57,
        "RUB": 1.0,
        "CNY": 12.88,
        "GBP": 117.05,
        "JPY": 0.555
}



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


@dp.message(ConvertSteps.to_currency)
async def process_to_currency(message: Message, state: FSMContext):
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

    user_data = await state.get_data()
    from_currency = user_data.get("from_currency")

    if currency_input == from_currency:
        same_error = {
            "en": f"❌ You already selected {from_currency}. Please choose a DIFFERENT currency to convert to:",
            "ru": f"❌ Вы уже выбрали {from_currency}. Пожалуйста, выберите ДРУГУЮ валюту для конвертации:",
            "de": f"❌ Sie haben bereits {from_currency} ausgewählt. Bitte wählen Sie eine ANDERE Währung:"
        }
        await message.answer(same_error[lang])
        return

    await state.update_data(to_currency=currency_input)

    texts = {
        "en": f"You are converting **{from_currency}** to **{currency_input}**.\n\n⌨️ Please enter the **amount** you want to convert (e.g., 100 or 50.5):",
        "ru": f"Вы переводите **{from_currency}** в **{currency_input}**.\n\n⌨️ Пожалуйста, введите **сумму**, которую хотите конвертировать (например, 100 или 50.5):",
        "de": f"Sie rechnen **{from_currency}** in **{currency_input}** um.\n\n⌨️ Bitte geben Sie den **Betrag** ein (z. B. 100 или 50.5):"
    }

    await state.set_state(ConvertSteps.amount)

    await message.answer(texts[lang], reply_markup=ReplyKeyboardRemove())


@dp.message(ConvertSteps.amount)
async def process_amount(message: Message, state: FSMContext):
    lang = user_languages.get(message.from_user.id, "en")

    amount_input = message.text.replace(",", ".")

    try:
        amount = float(amount_input)
        if amount <= 0:
            raise ValueError
    except ValueError:
        error_texts = {
            "en": "❌ Please enter a valid positive number (e.g., 100 or 45.5):",
            "ru": "❌ Пожалуйста, введите корректное положительное число (например, 100 или 45.5):",
            "de": "❌ Bitte geben Sie eine gültige positive Zahl ein (z. B. 100 или 45.5):"
        }
        await message.answer(error_texts[lang])
        return

    user_data = await state.get_data()
    from_curr = user_data.get("from_currency")
    to_curr = user_data.get("to_currency")

    waiting_texts = {
        "en": "🔄 Fetching latest rates...",
        "ru": "🔄 Запрашиваю актуальные курсы...",
        "de": "🔄 Aktuelle Kurse abrufen..."
    }
    waiting_msg = await message.answer(waiting_texts[lang])



    try:
        if from_curr not in RATES_DATA or to_curr not in RATES_DATA:
            raise ValueError(f"Неподдерживаемая пара валют: {from_curr} -> {to_curr}")

        rate = round(RATES_DATA[from_curr] / RATES_DATA[to_curr], 6)

        result = amount * rate
        formatted_result = f"{result:,.2f}"
        formatted_amount = f"{amount:,.2f}"

        success_texts = {
            "en": f"✅ **Result (Test Mode):**\n\n{formatted_amount} {from_curr} = **{formatted_result} {to_curr}**\n*(Rate: 1 {from_curr} = {rate} {to_curr})*",
            "ru": f"✅ **Результат (Тестовый режим):**\n\n{formatted_amount} {from_curr} = **{formatted_result} {to_curr}**\n*(Курс: 1 {from_curr} = {rate} {to_curr})*",
            "de": f"✅ **Ergebnis (Testmodus):**\n\n{formatted_amount} {from_curr} = **{formatted_result} {to_curr}**\n*(Kurs: 1 {from_curr} = {rate} {to_curr})*"
        }
        await waiting_msg.delete()
        await message.answer(success_texts[lang], parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Local Conversion Error: {e}")
        api_error_texts = {
            "en": "❌ Sorry, could not process conversion. Invalid currency code.",
            "ru": "❌ К сожалению, не удалось выполнить конвертацию. Неверный код валюты.",
            "de": "❌ Entschuldigung, Konvertierung fehlgeschlagen. Ungültiger Währungscode."
        }
        await waiting_msg.delete()
        await message.answer(api_error_texts[lang])

    if lang == "ru":
        kb = [[KeyboardButton(text="💱 Быстрый конвертер")], [KeyboardButton(text="⭐ Избранные курсы")],
              [KeyboardButton(text="🌐 Выбор языка")]]
    elif lang == "de":
        kb = [[KeyboardButton(text="💱 Schneller Konverter")], [KeyboardButton(text="⭐ Bevorzugte Kurse")],
              [KeyboardButton(text="🌐 Sprachauswahl")]]
    else:
        kb = [[KeyboardButton(text="💱 Quick Converter")], [KeyboardButton(text="⭐ Favorite Rates")],
              [KeyboardButton(text="🌐 Language Selection")]]

    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    return_texts = {
        "en": "Returned to main menu 👇",
        "ru": "Возвращаю вас в главное меню 👇",
        "de": "Zurück zum Hauptmenü 👇"
    }

    await state.clear()
    await message.answer(return_texts[lang], reply_markup=keyboard)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())