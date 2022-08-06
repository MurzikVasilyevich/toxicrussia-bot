import codecs
import logging.config
import random
import textwrap
from datetime import timedelta

import pandas as pd
import requests
from google.cloud.texttospeech_v1beta1 import VoiceSelectionParams, AudioConfig, AudioEncoding, \
    SynthesizeSpeechRequest, SynthesisInput, TextToSpeechClient, SsmlVoiceGender
from moviepy.editor import *
from srt import Subtitle, compose

import settings as s

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('app.py')


def text_to_ssml(t):
    text_split = textwrap.wrap(t, s.CLIP.TEXT_WRAP)
    ret = {"text": text_split}
    text_ssml = []
    for i in range(len(text_split)):
        text_ssml.append(f"<mark name=\"{i}\"/>{text_split[i]}")
    text_joined = f"<speak>{' '.join(text_ssml)}.<mark name=\"{i + 1}\"/></speak>"
    ret['ssml'] = text_joined
    return ret


def create_voice_srt(language, files):
    text = files.texter.texts["result"][language]
    id_s = files.chunk.id_s
    logger.info(f"Creating {language} audio for {id_s}")
    voice_file = os.path.join(s.LOCAL.SOUND, f"{id_s}_{language}.mp3")
    srt_file = os.path.join(s.LOCAL.VIDEO, f"{id_s}_{language}.srt")

    client = TextToSpeechClient()
    text_ssml = text_to_ssml(text)
    synthesis_input = SynthesisInput(ssml=text_ssml["ssml"])
    voice = VoiceSelectionParams(language_code=s.LINGUISTIC.LANGUAGE_CODES[language],
                                 ssml_gender=random.choice(list(SsmlVoiceGender)))
    audio_config = AudioConfig(audio_encoding=AudioEncoding.MP3)
    request = SynthesizeSpeechRequest(input=synthesis_input, voice=voice, audio_config=audio_config,
                                      enable_time_pointing=[SynthesizeSpeechRequest.TimepointType.SSML_MARK])
    response = client.synthesize_speech(request=request)
    time_points = list(response.timepoints)
    with open(voice_file, "wb") as out:
        out.write(response.audio_content)
        print(f'Audio content written to file "{voice_file}"')
    subs = []
    for i in range(len(time_points) - 1):
        point = time_points[i]
        point_next = time_points[i + 1]
        subs.append(Subtitle(
            index=int(point.mark_name),
            start=timedelta(seconds=point.time_seconds + s.CLIP.AUDIO_START),
            end=timedelta(seconds=point_next.time_seconds - 0.2 + s.CLIP.AUDIO_START),
            content=text_ssml['text'][i]
        ))
    composed = compose(subs)
    with codecs.open(srt_file, "w", "utf-8") as out:
        out.write(composed)
        print(f'Subtitles written to file {srt_file}')
    return voice_file, srt_file


def download_music():
    logger.info("Downloading random music")
    offs = random.randint(1, 100)
    url = f"http://ccmixter.org/api/query?f=csv&dataview=links_dl&limit=30&offset={offs}&type=instrumentals"
    df = pd.read_csv(url)
    audio_url = df[df['download_url'].str.contains(".mp3")].sample(1).iloc[0]['download_url']
    payload = {}
    headers = {
        'Referer': 'http://ccmixter.org/'
    }
    filename = os.path.join(s.LOCAL.SOUND, audio_url.split("/")[-1])
    r = requests.get(audio_url, payload, headers=headers)
    open(filename, 'wb').write(r.content)
    logger.info(filename)
    return filename


