import glob
import os
import random

import ffmpeg
from internetarchive import search_items, download
from moviepy import editor as mpe
from moviepy.audio.fx.audio_fadein import audio_fadein
from moviepy.audio.fx.audio_fadeout import audio_fadeout
from moviepy.audio.fx.audio_normalize import audio_normalize
from moviepy.audio.fx.volumex import volumex
from moviepy.audio.io.AudioFileClip import AudioFileClip

import settings as s


def download_video():
    res = search_items('collection:(movies) AND mediatype:(movies) AND format:(mpeg4)',
                       params={"rows": 50, "page": random.randint(1, 100)},
                       fields=['identifier', 'item_size', 'downloads'])
    retries = 0
    while True:
        retries += 1
        item = random.choice(list(res))
        if item['item_size'] > s.OPENARCHIVE.MAX_SIZE and retries < s.OPENARCHIVE.MAX_RETRIES:
            print(f"Item is too big, skipping {item['identifier']}")
            continue
        download(item['identifier'], verbose=True, glob_pattern=f"*[0-9].mp4",
                 destdir=s.LOCAL.VIDEO, no_directory=True)
        test = glob.glob(os.path.join(s.LOCAL.VIDEO, f"{item['identifier']}*.mp4"))
        if not test and retries < s.OPENARCHIVE.MAX_RETRIES:
            print("Download failed, trying again")
            continue
        else:
            downloaded = test[0]
            return downloaded


def create_video_clip(language, files, srt_lang="en"):
    id_s = files.chunk.id_s
    back_video = files.src['video']
    music_file = files.src['music']
    voice_file = files.text["voice"][language]
    print(f"Creating {language} clip for {id_s}")
    out_clip = f"./videos/{id_s}_{language}.mp4"
    audio_background, music_background, my_clip = create_video(back_video, music_file, voice_file)
    srt_file = files.text["srt"][srt_lang]
    out_clip_srt = f"./videos/{id_s}_{language}_srt_{srt_lang}.mp4"
    final_audio = mpe.CompositeAudioClip([audio_background.set_start(s.CLIP.AUDIO_START), music_background])
    final_audio.duration = audio_background.duration + 3
    final_clip = my_clip.set_audio(final_audio)
    final_clip.duration = audio_background.duration + 3
    final_clip.write_videofile(out_clip, temp_audiofile='temp-audio.m4a', remove_temp=True,
                               codec="libx264", audio_codec="aac")
    video = ffmpeg.input(out_clip)
    audio = video.audio
    add_srt(video, audio, srt_file, out_clip_srt)
    return out_clip, out_clip_srt


def add_srt(video, audio, srt, out_clip_srt):
    ffmpeg.concat(video.filter('subtitles', srt), audio, v=1, a=1).output(out_clip_srt).run(overwrite_output=True)


def create_video(back_video, music_file, voice_file):
    my_clip = mpe.VideoFileClip(back_video)
    audio_background = AudioFileClip(voice_file)
    music_background = AudioFileClip(music_file)
    music_background = audio_normalize(music_background)
    music_background = audio_fadein(music_background, 1)
    music_background = audio_fadeout(music_background, 2)
    music_background = volumex(music_background, 0.2)
    music_background.duration = audio_background.duration + 3
    if my_clip.duration > audio_background.duration:
        start = random.randint(0, int(my_clip.duration - audio_background.duration))
        my_clip = my_clip.subclip(start, start + audio_background.duration)
    else:
        my_clip = my_clip.loop(duration=audio_background.duration)
    my_clip.resize(width=480)
    return audio_background, music_background, my_clip
