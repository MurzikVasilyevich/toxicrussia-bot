import logging
from datetime import datetime
from airtable_helper import Airtable
from audio_helper import download_music, create_voice_srt
from openai_helper import open_ai
from words_helper import Words
from translation_helper import Translations
import settings as s

from video_helper import download_video, create_video_clip

import logging.config
logging.config.fileConfig('logging.conf')
logger = logging.getLogger('app.py')


class Chunk:
    def __init__(self, generate=False):
        self.generated_on = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        self.generate = generate
        self.db = Airtable(self)
        self.record = None
        self.confirmed = None
        if not self.generate:
            self.record = self.db.get_confirmed()
        if self.record:
            self.confirmed = self.record["fields"]["confirmed"]
            self.source = Source(self)
            self.texter = Texter(self)
            self.id = self.record["id"]
            self.id_s = f"{self.record['fields']['id']:06}"
            self.files = Files(self, download_video(), download_music())
        else:
            if not self.generate:
                logger.info("No queued records found")
            else:
                logger.info("Starting to generate records")
            self.source = Source(self)
            self.texter = Texter(self)
            self.record = self.db.post()
            self.id = self.record["id"]
            self.id_s = f"{self.record['fields']['id']:06}"


class Source:
    def __init__(self, chunk):
        self.genre = None
        self.format = None
        logging.info("Getting source")
        self.chunk = chunk
        
        if not self.chunk.confirmed:
            self.get_format()
            self.get_genre()

    def get_format(self):
        self.format = self.chunk.db.get_format()

    def get_genre(self):
        self.genre = self.chunk.db.get_genre()


class Texter:
    def __init__(self, chunk):
        self.texts = {}
        logging.info("Getting texter")
        self.languages = s.LINGUISTIC.LANGUAGES
        self.chunk = chunk
        self.texts = {"query": {}, "result": {}}
        if chunk.confirmed:
            self.query = self.chunk.record["fields"][f"{self.languages[0]}_q"]
            self.open_ai_result = self.chunk.record["fields"][f"{self.languages[0]}"]
            for lang in self.languages:
                self.texts['query'][lang] = self.chunk.record["fields"][f"{lang}_q"]
                self.texts['result'][lang] = self.chunk.record["fields"][f"{lang}"]
        else:
            # self.words = Words()
            self.query = Words(self.chunk.source.format["fields"]["Format"]).result
            # self.query = (prepare_fmt(self.chunk.source.format["fields"]["Format"])).format(**vars(self.words)["words"])
            self.open_ai_result = open_ai(f"Write a {self.chunk.source.genre['fields']['Name']} about how" +
                                          self.query).strip()
            self.texts = Translations(self, self.languages).texts


class Files:
    def __init__(self, chunk, video, music):
        logging.info("Getting files")
        self.chunk = chunk
        self.src = {
            "video": video,
            "music": music
        }
        self.texter = chunk.texter
        self.text = {"voice": {}, "srt": {}}
        self.video = {"voice": {}, "srt": {}}
        for lang in self.texter.languages:
            self.create_text(lang)
            self.create_video(lang)

    def create_text(self, lang):
        logging.info("Creating text record")
        voice, srt_file = create_voice_srt(lang, self)
        self.text["voice"][lang] = voice
        self.text["srt"][lang] = srt_file

    def create_video(self, lang):
        logging.info("Creating video record")
        clip, clip_srt = create_video_clip(lang, self)
        self.video["voice"][lang] = clip
        self.video["srt"][lang] = clip_srt

