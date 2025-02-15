class Config:
    # Основные настройки
    DOMAIN = "r.test.local:8000"
    MAIN_REDIRECT = "https://t.me/LinkBridgerBot"

    # Настройки безопасности
    WHITELIST_ENABLED = True
    WHITELIST_USERS = ["@tokishu"]

    # Настройки Telegram
    BOT_TOKEN = "sdomafdumaouidjsudvhmsi1082u312m8ur18um8012jnj"

    # API

    API_KEY = "api_key"

    # Языковые настройки
    DEFAULT_LANGUAGE = "en"
    AVAILABLE_LANGUAGES = ["ru", "en"]

    # Настройки временных редиректов
    MAX_TEMP_REDIRECT_LENGTH = 90
    RANDOM_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

MESSAGES = {
    "ru": {
        "welcome": "👋 Добро пожаловать в Redirect Bot!\nВыберите действие:",
        "add_redirect": "Создать редирект",
        "add_temp": "Создать временный",
        "list_redirects": "Мои редиректы",
        "stats": "Статистика",

        "enter_subdomain": "Введите поддомен для редиректа (например: github):",
        "invalid_subdomain": "❌ Некорректный поддомен. Разрешены только буквы и цифры.",
        "subdomain_exists": "❌ Такой поддомен уже существует. Введите другой:",

        "enter_url": "Введите URL, куда будет направлен редирект:",
        "error_invalid_url": "❌ Некорректный URL. Попробуйте снова.",
        "success": "✅ Редирект успешно создан!\n\nПоддомен: {subdomain}\nURL: {url}",

        "not_authorized": "⚠️ У вас нет доступа к боту.",
        "my_redirects": "📋 Ваши редиректы:",
        "no_redirects": "У вас пока нет редиректов.",

        "delete_success": "🗑 Редирект успешно удален.",
        "delete_error": "❌ Ошибка при удалении редиректа.",

        "enter_temp_length": "Введите желаемую длину временной ссылки (до 90 символов):",
        "enter_expiry": "Выберите срок действия временного редиректа:",
        "select_expiry": "Выберите срок действия временного редиректа:",
        "temp_success": "🕒 Временный редирект создан!\n\nСсылка: {link}\nИстекает: {expires}",
        "invalid_length": "❌ Неверная длина. Введите число от 1 до 90.",

        "random_generated": "🎲 Сгенерированная ссылка: {link}\nИспользовать эту?",
        "delete_confirm": "Вы уверены, что хотите удалить редирект {subdomain}?",
        "delete_cancelled": "Удаление отменено.",

        "day": "день",
        "days": "дней",
        "yes": "Да",
        "no": "Сгенерировать новую",
        "confirm_delete_btn": "Подтвердить удаление",
        "cancel_delete_btn": "Отмена",
        "stats_button": "Статистика",
        "delete_button": "Удалить",

        "stats_header_all": "📊 Статистика по вашим редиректам:\n\n",
        "clicks": "Клики",
        "last_click": "Последний клик",
        "top_countries": "Топ стран",
        "top_referrers": "Топ источников",
        "expires_at": "Истекает"
    },

    "en": {
        "welcome": "👋 Welcome to Redirect Bot!\nChoose an action:",
        "add_redirect": "Add redirect",
        "add_temp": "Add temporary",
        "list_redirects": "My redirects",
        "stats": "Statistics",

        "enter_subdomain": "Enter subdomain for redirect (example: github):",
        "invalid_subdomain": "❌ Invalid subdomain. Only alphanumeric characters are allowed.",
        "subdomain_exists": "❌ That subdomain already exists. Try another:",

        "enter_url": "Enter the URL where redirect will point to:",
        "error_invalid_url": "❌ Invalid URL. Please try again.",
        "success": "✅ Redirect successfully created!\n\nSubdomain: {subdomain}\nURL: {url}",

        "not_authorized": "⚠️ You don't have access to this bot.",
        "my_redirects": "📋 Your redirects:",
        "no_redirects": "You don't have any redirects yet.",

        "delete_success": "🗑 Redirect successfully deleted.",
        "delete_error": "❌ Error while deleting redirect.",

        "enter_temp_length": "Enter the desired length of the temporary link (up to 90 characters):",
        "enter_expiry": "Select the expiration for the temporary redirect:",
        "select_expiry": "Select the expiration for the temporary redirect:",
        "temp_success": "🕒 Temporary redirect created!\n\nLink: {link}\nExpires: {expires}",
        "invalid_length": "❌ Invalid length. Please enter a number between 1 and 90.",

        "random_generated": "🎲 Generated link: {link}\nUse this one?",
        "delete_confirm": "Are you sure you want to delete the redirect {subdomain}?",
        "delete_cancelled": "Deletion canceled.",

        "day": "day",
        "days": "days",
        "yes": "Yes",
        "no": "Generate a new one",
        "confirm_delete_btn": "Confirm deletion",
        "cancel_delete_btn": "Cancel",
        "stats_button": "Stats",
        "delete_button": "Delete",

        "stats_header_all": "📊 Statistics for your redirects:\n\n",
        "clicks": "Clicks",
        "last_click": "Last click",
        "top_countries": "Top countries",
        "top_referrers": "Top referrers",
        "expires_at": "Expires at"
    }
}
