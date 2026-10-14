"""Мини-справочник мест (координаты + IANA-зона).

Для любых других мест передавайте lat/lon/tz явно. Если известна только пара
координат, зону можно определить через timezonefinder (см. tz_for_coords).
"""
from __future__ import annotations

PLACES: dict[str, dict] = {
    "moscow":           {"name": "Москва",            "lat": 55.7558, "lon": 37.6173, "tz": "Europe/Moscow"},
    "saint petersburg": {"name": "Санкт-Петербург",   "lat": 59.9343, "lon": 30.3351, "tz": "Europe/Moscow"},
    "kyiv":             {"name": "Киев",              "lat": 50.4501, "lon": 30.5234, "tz": "Europe/Kyiv"},
    "minsk":            {"name": "Минск",             "lat": 53.9006, "lon": 27.5590, "tz": "Europe/Minsk"},
    "chisinau":         {"name": "Кишинёв",           "lat": 47.0105, "lon": 28.8638, "tz": "Europe/Chisinau"},
    "almaty":           {"name": "Алматы",            "lat": 43.2220, "lon": 76.8512, "tz": "Asia/Almaty"},
    "tashkent":         {"name": "Ташкент",           "lat": 41.2995, "lon": 69.2401, "tz": "Asia/Tashkent"},
    "tbilisi":          {"name": "Тбилиси",           "lat": 41.7151, "lon": 44.8271, "tz": "Asia/Tbilisi"},
    "yerevan":          {"name": "Ереван",            "lat": 40.1792, "lon": 44.4991, "tz": "Asia/Yerevan"},
    "baku":             {"name": "Баку",              "lat": 40.4093, "lon": 49.8671, "tz": "Asia/Baku"},
    "riga":             {"name": "Рига",              "lat": 56.9496, "lon": 24.1052, "tz": "Europe/Riga"},
    "vilnius":          {"name": "Вильнюс",           "lat": 54.6872, "lon": 25.2797, "tz": "Europe/Vilnius"},
    "tallinn":          {"name": "Таллин",            "lat": 59.4370, "lon": 24.7536, "tz": "Europe/Tallinn"},
    "novosibirsk":      {"name": "Новосибирск",       "lat": 55.0084, "lon": 82.9357, "tz": "Asia/Novosibirsk"},
    "yekaterinburg":    {"name": "Екатеринбург",      "lat": 56.8389, "lon": 60.6057, "tz": "Asia/Yekaterinburg"},
    "kazan":            {"name": "Казань",            "lat": 55.7961, "lon": 49.1064, "tz": "Europe/Moscow"},
    "samara":           {"name": "Самара",            "lat": 53.1959, "lon": 50.1002, "tz": "Europe/Samara"},
    "volgograd":        {"name": "Волгоград",         "lat": 48.7080, "lon": 44.5133, "tz": "Europe/Volgograd"},
    "krasnoyarsk":      {"name": "Красноярск",        "lat": 56.0153, "lon": 92.8932, "tz": "Asia/Krasnoyarsk"},
    "irkutsk":          {"name": "Иркутск",           "lat": 52.2870, "lon": 104.3050, "tz": "Asia/Irkutsk"},
    "vladivostok":      {"name": "Владивосток",       "lat": 43.1155, "lon": 131.8855, "tz": "Asia/Vladivostok"},
    "omsk":             {"name": "Омск",              "lat": 54.9885, "lon": 73.3242, "tz": "Asia/Omsk"},
    "beijing":          {"name": "Пекин",             "lat": 39.9042, "lon": 116.4074, "tz": "Asia/Shanghai"},
    "hong kong":        {"name": "Гонконг",           "lat": 22.3193, "lon": 114.1694, "tz": "Asia/Hong_Kong"},
    "london":           {"name": "Лондон",            "lat": 51.5074, "lon": -0.1278, "tz": "Europe/London"},
    "new york":         {"name": "Нью-Йорк",          "lat": 40.7128, "lon": -74.0060, "tz": "America/New_York"},
    "ulm":              {"name": "Ульм",              "lat": 48.4011, "lon": 9.9876, "tz": "Europe/Berlin"},
    "berlin":           {"name": "Берлин",            "lat": 52.5200, "lon": 13.4050, "tz": "Europe/Berlin"},
    "paris":            {"name": "Париж",             "lat": 48.8566, "lon": 2.3522, "tz": "Europe/Paris"},
    "new delhi":        {"name": "Нью-Дели",          "lat": 28.6139, "lon": 77.2090, "tz": "Asia/Kolkata"},
}

_ALIASES = {
    "москва": "moscow", "санкт-петербург": "saint petersburg", "спб": "saint petersburg",
    "петербург": "saint petersburg", "ленинград": "saint petersburg", "киев": "kyiv", "kiev": "kyiv",
    "минск": "minsk", "кишинёв": "chisinau", "кишинев": "chisinau", "алматы": "almaty", "алма-ата": "almaty",
    "ташкент": "tashkent", "тбилиси": "tbilisi", "ереван": "yerevan", "баку": "baku", "рига": "riga",
    "вильнюс": "vilnius", "таллин": "tallinn", "новосибирск": "novosibirsk", "екатеринбург": "yekaterinburg",
    "свердловск": "yekaterinburg", "казань": "kazan", "самара": "samara", "куйбышев": "samara",
    "волгоград": "volgograd", "красноярск": "krasnoyarsk", "иркутск": "irkutsk", "владивосток": "vladivostok",
    "омск": "omsk", "пекин": "beijing", "гонконг": "hong kong", "лондон": "london", "нью-йорк": "new york",
    "ульм": "ulm", "берлин": "berlin", "париж": "paris", "нью-дели": "new delhi", "st petersburg": "saint petersburg",
}


def resolve_place(name: str) -> dict | None:
    key = name.strip().lower()
    key = _ALIASES.get(key, key)
    return PLACES.get(key)


def tz_for_coords(lat: float, lon: float) -> str | None:
    """IANA-зона по координатам (нужен пакет timezonefinder)."""
    try:
        from timezonefinder import TimezoneFinder
    except ImportError:  # pragma: no cover
        return None
    return TimezoneFinder().timezone_at(lat=lat, lng=lon)
