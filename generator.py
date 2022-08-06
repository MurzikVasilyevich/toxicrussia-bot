import os
import shutil

import settings as s


def init_folder(folder):
    shutil.rmtree(folder, ignore_errors=True)
    os.path.exists(folder) or os.makedirs(folder)


class Generator:
    def __init__(self):
        init_folder(s.LOCAL.SOUND)
        init_folder(s.LOCAL.VIDEO)
        init_folder(s.LOCAL.STORAGE)

        for lang in s.LINGUISTIC.LANGUAGES:
            init_folder(f"{s.LOCAL.STORAGE}/{lang}")
