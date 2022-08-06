import logging.config
from deep_translator import GoogleTranslator

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('app.py')


def g_translate(lang, text):
    return GoogleTranslator(target=lang).translate(text)


class Translations:
    def __init__(self, texter, languages):
        self.languages = languages
        self.texter = texter
        self.texts = {
            "query":
                {"en": self.texter.query},
            "result":
                {"en": self.texter.open_ai_result}
        }
        self.generate_translations(self.languages)

    def generate_translations(self, languages):
        logging.info("Translating languages")
        for lang in list(filter(lambda x: x != "en", languages)):
            self.texts["query"][lang] = g_translate(lang, self.texter.query)
            self.texts["result"][lang] = g_translate(lang, self.texter.open_ai_result)
            logging.info(f"{lang}..DONE")
        logging.info("Translations generated")
