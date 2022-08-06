from pyairtable import Table

import settings as s
import logging.config
import random

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('app.py')


class Airtable:
    def __init__(self, chunk):
        self.chunk = chunk
        self.key = s.AIRTABLE.KEY
        self.base = s.AIRTABLE.BASE
        self.tables = {
            "records": self.set_table(s.AIRTABLE.TABLE_RECORDS),
            "formats": self.set_table(s.AIRTABLE.TABLE_FORMATS),
            "genres": self.set_table(s.AIRTABLE.TABLE_GENRES)
        }
        # self.id = self.post()
        self.queued = self.get_confirmed()

    def set_table(self, table):
        return Table(self.key, self.base, table)

    def get_format(self):
        formats = self.tables["formats"].all(formula="Enabled")
        fmt = random.choice(formats)
        return fmt

    def get_genre(self):
        genres = self.tables["genres"].all(formula="Enabled")
        gnr = random.choice(genres)
        return gnr

    def post(self):
        logging.info("Posting to Airtable")
        # translations = dict(self.chunk.texter.texts)
        translations = {"Format": [self.chunk.source.format["id"]], "Genre": [self.chunk.source.genre["id"]],
                        "datetime": self.chunk.generated_on}
        for lang in self.chunk.texter.languages:
            translations[lang] = self.chunk.texter.texts["result"][lang]
            translations[f"{lang}_q"] = self.chunk.texter.texts["query"][lang]
        return self.tables["records"].create(translations)

    def get_confirmed(self):
        queued = self.tables["records"].first(view="Queue")
        if not queued:
            logging.info("!!!No queued records!!!")
        return queued

    def update_status(self, field, value):
        resp = self.tables["records"].update(str(self.queued["id"]), {field: value})
        logging.info(f"Updating {field}: {resp}")
