import logging.config
import shutil
import os
import telebot
import vimeo
import pathlib

import dropbox
from dropbox.exceptions import AuthError

import settings as s

# from video_helper import download_video, create_clip

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('app.py')


def trim_text(query, max_len):
    trimmed = (query[:max_len - 5] + '..') if len(query) > max_len else query
    return trimmed


class PublishManager:
    def __init__(self, chunk):
        # self.video_back = download_video()
        self.chunk = chunk
        self.db = chunk.db
        self.telegram_bots = s.TELEGRAM.BOTS
        self.sign = s.TELEGRAM.SIGNATURE
        self.key = s.TELEGRAM.API_KEY
        self.queued = self.db.queued
        self.bot = telebot.TeleBot(self.key, parse_mode=None)
        if self.queued:
            self.broadcast()
        else:
            logger.info("No messages to send")

    def broadcast(self):
        logger.info("Starting PublishManager messaging")
        for lang in s.LINGUISTIC.LANGUAGES:
            text = self.chunk.texter.texts["result"][lang]
            query = self.chunk.texter.texts["query"][lang]
            post = f"{text}\n\n___\n{self.sign}\n<i>{query}</i>"
            logger.info(f"Creating video clip for {lang} language")
            out_clip = self.chunk.files.video['srt'][lang]

            if s.POST.TELEGRAM:
                self.post_telegram(out_clip, lang, query, post)
            if s.POST.VIMEO:
                self.post_vimeo(out_clip, lang, query, text)
            if s.POST.DROPBOX:
                self.store_dropbox(lang)
            if s.POST.LOCAL:
                self.store_local(self.chunk.files.video['srt'][lang], lang)
            if s.POST.TELEGRAM or s.POST.VIMEO or s.POST.LOCAL or s.POST.DROPBOX:
                self.db.update_status("published", True)
        logger.info("Finished PublishManager messaging")

    def store_dropbox(self, lang):
        logger.info(f"Storing to dropbox for {lang} language")
        file = self.chunk.files.video['srt'][lang]
        filename = os.path.basename(file)
        dropbox_upload_file(s.LOCAL.VIDEO, filename, f'/poopoo/{lang}/{filename}')

    def store_local(self, out_clip, lang):
        logger.info(f"Storing local")
        shutil.move(out_clip, f"{s.LOCAL.STORAGE}{lang}/")

    def post_vimeo(self, out_clip, lang, query, text):
        logger.info(f"Posting to vimeo for {lang} language")
        if lang in s.VIMEO.LANGUAGES:
            client = vimeo.VimeoClient(
                token=s.VIMEO.TOKEN,
                key=s.VIMEO.KEY,
                secret=s.VIMEO.SECRET
            )
            data = {
                "name": trim_text(query, s.VIMEO.TITLE_LENGTH),
                "description": trim_text(text, s.VIMEO.DESCRIPTION_LENGTH)
            }
            print(data)
            video_id = client.upload(out_clip, data=data)
            video_url = f"https://vimeo.com/{video_id.split('/')[-1]}"
            if video_id:
                self.db.update_status(f"vimeo", video_url)
            return video_url
        else:
            logger.info(f"{lang} language is not supported")
            return None

    def post_telegram(self, out_clip, lang, query, post):
        logger.info(f"Posting to telegram for {lang} language")
        video_urls = []
        chat_id = self.telegram_bots[lang]
        if s.TELEGRAM.POST_TEXT:
            post_response = self.bot.send_message(chat_id, post, parse_mode='HTML')
        if s.POST.CREATE_AUDIO:
            logger.info(f"Uploading audio file for {lang} language")

            if s.POST.CREATE_VIDEO:
                logger.info(f"Creating video clip for {lang} language")
                clip = open(out_clip, 'rb')
                if s.TELEGRAM.POST_TEXT:
                    tg_video = self.bot.send_video(chat_id, clip,
                                                   caption=query,
                                                   reply_to_message_id=post_response.message_id)
                else:
                    tg_video = self.bot.send_video(chat_id, clip,
                                                   caption=query)
                video_url = self.bot.get_file_url(tg_video.video.file_id)
                if video_url:
                    video_urls.append({"url": video_url})

        if s.POST.CREATE_VIDEO:
            self.db.update_status(f"{lang}_v", video_urls)
        logger.info(f"Finished posting to telegram for {lang} language")


def dropbox_connect():
    try:
        dbx = dropbox.Dropbox(s.DROPBOX.TOKEN)
    except AuthError as e:
        print('Error connecting to Dropbox with access token: ' + str(e))
    return dbx


def dropbox_upload_file(local_path, local_file, dropbox_file_path):
    """Upload a file from the local machine to a path in the Dropbox app directory.

    Args:
        local_path (str): The path to the local file.
        local_file (str): The name of the local file.
        dropbox_file_path (str): The path to the file in the Dropbox app directory.

    Example:
        dropbox_upload_file('.', 'test.csv', '/stuff/test.csv')

    Returns:
        meta: The Dropbox file metadata.
    """

    try:
        dbx = dropbox_connect()
        local_file_path = pathlib.Path(local_path) / local_file
        with local_file_path.open("rb") as f:
            meta = dbx.files_upload(f.read(), dropbox_file_path, mode=dropbox.files.WriteMode("overwrite"))
            return meta
    except Exception as e:
        print('Error uploading file to Dropbox: ' + str(e))
