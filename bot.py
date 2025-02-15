import asyncio
import traceback

import validators
from datetime import datetime, timedelta
from typing import Dict, Any

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, \
    ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.callback_data import CallbackData

from config import Config, MESSAGES
from database import JSONDatabase


# ----------- КЛАССЫ СОСТОЯНИЙ -----------
class RedirectStates(StatesGroup):
    waiting_for_subdomain = State()
    waiting_for_url = State()
    waiting_for_temp_length = State()
    waiting_for_temp_url = State()
    waiting_for_expiry = State()
    confirm_random = State()


# ----------- CALLBACK_DATA -----------
class RedirectCallback(CallbackData, prefix="redirect"):
    action: str
    subdomain: str


class ExpiryCallback(CallbackData, prefix="expiry"):
    days: int


# ----------- ИНИЦИАЛИЗАЦИЯ -----------
db = JSONDatabase("redirects.json")
bot = Bot(
    token=Config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

router = Router()


# ----------- КЛАВИАТУРЫ -----------
def get_main_keyboard(lang: str) -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="➕ " + MESSAGES[lang]["add_redirect"]),
            KeyboardButton(text="🕒 " + MESSAGES[lang].get("add_temp", "Создать временный"))
        ],
        [
            KeyboardButton(text="📋 " + MESSAGES[lang]["list_redirects"]),
            KeyboardButton(text="📊 " + MESSAGES[lang].get("stats", "Статистика"))
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_yes_no_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ " + MESSAGES[lang].get("yes", "Да"),
                    callback_data="yes"
                ),
                InlineKeyboardButton(
                    text="🔄 " + MESSAGES[lang].get("no", "Сгенерировать новую"),
                    callback_data="no"
                )
            ]
        ]
    )


def get_expiry_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="1 " + MESSAGES[lang].get("day", "день"),
                    callback_data=ExpiryCallback(days=1).pack()
                ),
                InlineKeyboardButton(
                    text="7 " + MESSAGES[lang].get("days", "дней"),
                    callback_data=ExpiryCallback(days=7).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="30 " + MESSAGES[lang].get("days", "дней"),
                    callback_data=ExpiryCallback(days=30).pack()
                ),
                InlineKeyboardButton(
                    text="90 " + MESSAGES[lang].get("days", "дней"),
                    callback_data=ExpiryCallback(days=90).pack()
                )
            ]
        ]
    )


def get_redirect_keyboard(lang: str, subdomain: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 " + MESSAGES[lang].get("delete_button", "Удалить"),
                    callback_data=RedirectCallback(action="delete", subdomain=subdomain).pack()
                ),
                InlineKeyboardButton(
                    text="📊 " + MESSAGES[lang].get("stats_button", "Статистика"),
                    callback_data=RedirectCallback(action="stats", subdomain=subdomain).pack()
                ),
            ]
        ]
    )


# ----------- ОБРАБОТЧИКИ /START -----------
@router.message(Command("start"))
async def cmd_start(message: Message):
    lang = Config.DEFAULT_LANGUAGE
    if Config.WHITELIST_ENABLED and f"@{message.from_user.username}" not in Config.WHITELIST_USERS:
        await message.answer(MESSAGES[lang]["not_authorized"])
        return

    await message.answer(
        MESSAGES[lang]["welcome"],
        reply_markup=get_main_keyboard(lang)
    )


# ----------- ДОБАВЛЕНИЕ ПОСТОЯННОГО РЕДИРЕКТА -----------
@router.message(F.text.regexp(r"^➕"))
async def start_redirect_creation(message: Message, state: FSMContext):
    """
    Ловим нажатие кнопки "➕ Добавить редирект"
    """
    lang = Config.DEFAULT_LANGUAGE
    await state.set_state(RedirectStates.waiting_for_subdomain)
    await message.answer(MESSAGES[lang]["enter_subdomain"])


@router.message(RedirectStates.waiting_for_subdomain)
async def process_subdomain(message: Message, state: FSMContext):
    """
    Сюда пользователь вводит желаемый субдомен (например, "mylink").
    """
    lang = Config.DEFAULT_LANGUAGE
    subdomain = message.text.lower().strip()

    if not subdomain.isalnum():
        await message.answer(MESSAGES[lang]["invalid_subdomain"])
        return

    existing = await db.get_redirect(subdomain)
    if existing:
        await message.answer(MESSAGES[lang]["subdomain_exists"])
        return

    await state.update_data(subdomain=subdomain)
    await state.set_state(RedirectStates.waiting_for_url)
    await message.answer(MESSAGES[lang]["enter_url"])


@router.message(RedirectStates.waiting_for_url)
async def process_url(message: Message, state: FSMContext):
    lang = Config.DEFAULT_LANGUAGE
    url = message.text.strip()
    print(f"DEBUG: got message.text = {url}")

    if not validators.url(url):
        print("DEBUG: validators.url returned False.")
        await message.answer(MESSAGES[lang]["error_invalid_url"])
        return

    data = await state.get_data()
    subdomain = data["subdomain"]
    print(f"DEBUG: Adding redirect: subdomain={subdomain}, url={url}")

    try:
        await db.add_redirect(subdomain, url, message.from_user.id)
        print("DEBUG: add_redirect() done.")
    except Exception as e:
        print("ERROR while adding redirect:", e)
        print("TRACEBACK:", traceback.format_exc())
        await message.answer("⚠️ Internal error while adding redirect.")
        return

    await state.clear()
    print("DEBUG: State cleared.")

    try:
        await message.answer(
            MESSAGES[lang]["success"].format(
                subdomain=f"{subdomain}.{Config.DOMAIN}",
                url=url
            ),
            reply_markup=get_main_keyboard(lang)
        )
        print("DEBUG: Successfully sent 'redirect created' message.")
    except Exception as e:
        print("ERROR while sending success message:", e)
        print("TRACEBACK:", traceback.format_exc())



# ----------- ДОБАВЛЕНИЕ ВРЕМЕННОГО РЕДИРЕКТА -----------
@router.message(F.text.regexp(r"^🕒"))
async def start_temp_redirect(message: Message, state: FSMContext):
    """
    Ловим нажатие кнопки "🕒 Создать временный"
    """
    lang = Config.DEFAULT_LANGUAGE
    await state.set_state(RedirectStates.waiting_for_temp_length)
    await message.answer(MESSAGES[lang]["enter_temp_length"])


@router.message(RedirectStates.waiting_for_temp_length)
async def process_temp_length(message: Message, state: FSMContext):
    """
    Сюда пользователь вводит длину случайного субдомена (количество символов).
    """
    lang = Config.DEFAULT_LANGUAGE
    try:
        length = int(message.text)
        if not 1 <= length <= Config.MAX_TEMP_REDIRECT_LENGTH:
            raise ValueError()
    except ValueError:
        await message.answer(MESSAGES[lang]["invalid_length"])
        return

    # Генерируем случайный субдомен
    random_link = db.generate_random_link(length)
    await state.update_data(length=length, random_link=random_link)

    await message.answer(
        MESSAGES[lang]["random_generated"].format(
            link=f"{random_link}.{Config.DOMAIN}"
        ),
        reply_markup=get_yes_no_keyboard(lang)
    )
    await state.set_state(RedirectStates.confirm_random)


@router.callback_query(RedirectStates.confirm_random, F.data.startswith("yes"))
async def confirm_random_link_yes(callback: CallbackQuery, state: FSMContext):
    """
    Пользователь подтвердил использование сгенерированного субдомена (yes).
    """
    lang = Config.DEFAULT_LANGUAGE
    await state.set_state(RedirectStates.waiting_for_temp_url)
    await callback.message.answer(MESSAGES[lang]["enter_url"])
    await callback.answer()


@router.callback_query(RedirectStates.confirm_random, F.data.startswith("no"))
async def confirm_random_link_no(callback: CallbackQuery, state: FSMContext):
    """
    Пользователь захотел перегенерировать ссылку (no).
    """
    lang = Config.DEFAULT_LANGUAGE
    data = await state.get_data()
    length = data.get('length')

    random_link = db.generate_random_link(length)
    await state.update_data(random_link=random_link)

    await callback.message.edit_text(
        MESSAGES[lang]["random_generated"].format(
            link=f"{random_link}.{Config.DOMAIN}"
        ),
        reply_markup=get_yes_no_keyboard(lang)
    )
    await callback.answer()


@router.message(RedirectStates.waiting_for_temp_url)
async def process_temp_url(message: Message, state: FSMContext):
    """
    Сюда пользователь вводит URL для временного редиректа.
    """
    lang = Config.DEFAULT_LANGUAGE
    url = message.text.strip()
    if not validators.url(url):
        await message.answer(MESSAGES[lang]["error_invalid_url"])
        return

    await state.update_data(url=url)
    await message.answer(
        MESSAGES[lang]["select_expiry"],
        reply_markup=get_expiry_keyboard(lang)
    )
    await state.set_state(RedirectStates.waiting_for_expiry)


@router.callback_query(RedirectStates.waiting_for_expiry, ExpiryCallback.filter())
async def process_expiry(callback: CallbackQuery, callback_data: ExpiryCallback, state: FSMContext):
    """
    Выбираем срок действия (1, 7, 30, 90 дней).
    """
    lang = Config.DEFAULT_LANGUAGE
    days = callback_data.days
    data = await state.get_data()

    link = await db.add_temp_redirect(
        data["url"],
        callback.from_user.id,
        days,
        data.get("length")
    )

    expires = datetime.now() + timedelta(days=days)

    await callback.message.answer(
        MESSAGES[lang]["temp_success"].format(
            link=f"{link}.{Config.DOMAIN}",
            expires=expires.strftime("%d.%m.%Y %H:%M")
        ),
        reply_markup=get_main_keyboard(lang)
    )
    await state.clear()
    await callback.answer()


# ----------- СПИСОК РЕДИРЕКТОВ -----------
@router.message(F.text.regexp(r"^📋"))
async def list_redirects(message: Message):
    """
    Выводим список всех редиректов пользователя.
    """
    lang = Config.DEFAULT_LANGUAGE
    user_redirects = await db.get_user_redirects(message.from_user.id)

    if not user_redirects:
        await message.answer(MESSAGES[lang]["no_redirects"])
        return

    for subdomain, data in user_redirects.items():
        text = f"🔗 {subdomain}.{Config.DOMAIN}\n"
        text += f"📍 {data['url']}\n"
        if "expires_at" in data:
            expires = datetime.fromisoformat(data["expires_at"])
            text += f"⏰ {MESSAGES[lang].get('expires_at', 'Истекает')}: {expires.strftime('%d.%m.%Y %H:%M')}\n"

        kb = get_redirect_keyboard(lang, subdomain)
        await message.answer(text, reply_markup=kb)


# ----------- УДАЛЕНИЕ РЕДИРЕКТА -----------
@router.callback_query(RedirectCallback.filter(F.action == "delete"))
async def delete_redirect_confirm(callback: CallbackQuery, callback_data: RedirectCallback):
    """
    Показываем подтверждение удаления.
    """
    lang = Config.DEFAULT_LANGUAGE
    subdomain = callback_data.subdomain

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ " + MESSAGES[lang].get("confirm_delete_btn", "Подтвердить удаление"),
                    callback_data=f"confirm_delete_{subdomain}"
                ),
                InlineKeyboardButton(
                    text="❌ " + MESSAGES[lang].get("cancel_delete_btn", "Отмена"),
                    callback_data="cancel_delete"
                )
            ]
        ]
    )
    text_del = MESSAGES[lang].get("delete_confirm", "Вы уверены, что хотите удалить?").format(
        subdomain=f"{subdomain}.{Config.DOMAIN}"
    )
    await callback.message.edit_text(text_del, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_"))
async def delete_redirect(callback: CallbackQuery):
    lang = Config.DEFAULT_LANGUAGE
    subdomain = callback.data.replace("confirm_delete_", "")

    if await db.delete_redirect(subdomain, callback.from_user.id):
        await callback.message.edit_text(MESSAGES[lang]["delete_success"])
    else:
        await callback.message.edit_text(MESSAGES[lang].get("delete_error", "Ошибка удаления."))

    await callback.answer()


@router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery):
    lang = Config.DEFAULT_LANGUAGE
    await callback.message.edit_text(MESSAGES[lang].get("delete_cancelled", "Удаление отменено."))
    await callback.answer()


# ----------- ПОКАЗ СТАТИСТИКИ -----------
@router.message(F.text.regexp(r"^📊"))
async def show_stats(message: Message):
    lang = Config.DEFAULT_LANGUAGE
    user_redirects = await db.get_user_redirects(message.from_user.id)

    if not user_redirects:
        await message.answer(MESSAGES[lang]["no_redirects"])
        return

    stats_text = MESSAGES[lang].get("stats_header_all", "📊 Статистика по вашим редиректам:\n\n")
    for subdomain, data in user_redirects.items():
        stats = data.get("stats", {})
        stats_text += f"🔗 {subdomain}.{Config.DOMAIN}\n"
        stats_text += f"👆 {MESSAGES[lang].get('clicks', 'Клики')}: {stats.get('clicks', 0)}\n"
        if stats.get("last_click"):
            last_click = datetime.fromisoformat(stats["last_click"])
            stats_text += f"🕒 {MESSAGES[lang].get('last_click', 'Последний клик')}: {last_click.strftime('%d.%m.%Y %H:%M')}\n"

        if stats.get("countries"):
            top_countries = sorted(
                stats["countries"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            stats_text += f"🌍 {MESSAGES[lang].get('top_countries', 'Топ стран')}:\n"
            for country, clicks in top_countries:
                stats_text += f"   {country}: {clicks}\n"

        if stats.get("referrers"):
            top_referrers = sorted(
                stats["referrers"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            stats_text += f"🔍 {MESSAGES[lang].get('top_referrers', 'Топ источников')}:\n"
            for referrer, clicks in top_referrers:
                stats_text += f"   {referrer}: {clicks}\n"

        stats_text += "\n"

    await message.answer(stats_text)


@router.callback_query(RedirectCallback.filter(F.action == "stats"))
async def show_redirect_stats(callback: CallbackQuery, callback_data: RedirectCallback):
    lang = Config.DEFAULT_LANGUAGE
    subdomain = callback_data.subdomain

    try:
        redirect_data = await db.get_redirect(subdomain)
        if not redirect_data:
            await callback.answer(MESSAGES[lang].get("redirect_not_found", "Редирект не найден"))
            return

        stats = redirect_data.get("stats", {})
        stats_text = f"📊 {MESSAGES[lang].get('stats_for', 'Статистика для')} {subdomain}.{Config.DOMAIN}\n\n"

        stats_text += f"👆 {MESSAGES[lang].get('clicks', 'Клики')}: {stats.get('clicks', 0)}\n"

        if stats.get("last_click"):
            last_click = datetime.fromisoformat(stats["last_click"])
            stats_text += f"🕒 {MESSAGES[lang].get('last_click', 'Последний клик')}: {last_click.strftime('%d.%m.%Y %H:%M')}\n"

        if stats.get("countries"):
            stats_text += f"\n🌍 {MESSAGES[lang].get('top_countries', 'Топ стран')}:\n"
            top_countries = sorted(
                stats["countries"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            for country, clicks in top_countries:
                stats_text += f"   {country}: {clicks}\n"

        if stats.get("referrers"):
            stats_text += f"\n🔍 {MESSAGES[lang].get('top_referrers', 'Топ источников')}:\n"
            top_referrers = sorted(
                stats["referrers"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            for referrer, clicks in top_referrers:
                stats_text += f"   {referrer}: {clicks}\n"

        if "expires_at" in redirect_data:
            expires = datetime.fromisoformat(redirect_data["expires_at"])
            stats_text += f"\n⏰ {MESSAGES[lang].get('expires_at', 'Истекает')}: {expires.strftime('%d.%m.%Y %H:%M')}"

        current_text = callback.message.text
        if current_text != stats_text:
            await callback.message.edit_text(
                stats_text,
                reply_markup=get_redirect_keyboard(lang, subdomain)
            )
        else:
            await callback.answer(MESSAGES[lang].get("stats_updated", "Статистика обновлена"))

    except Exception as e:
        print(f"Error in show_redirect_stats: {e}")
        await callback.answer(MESSAGES[lang].get("error_getting_stats", "Ошибка при получении статистики"))

    await callback.answer()



async def main():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

