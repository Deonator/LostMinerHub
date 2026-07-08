from locales import ru, en, es, pt_br

LANGS = {
    "ru": ru.TEXTS,
    "en": en.TEXTS,
    "es": es.TEXTS,
    "pt_br": pt_br.TEXTS,
}


def t(key: str, lang: str = "ru"):
    return LANGS.get(lang, LANGS["ru"]).get(key, key)
