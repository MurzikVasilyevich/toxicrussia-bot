import logging.config
import random
import nltk
import requests
from nltk.corpus import wordnet as wn
import settings as s
from transliterate import translit

nltk.download('wordnet')
nltk.download('omw-1.4')
logging.config.fileConfig('logging.conf')
logger = logging.getLogger('app.py')


def make_3sg_form(verb_phrase):
    verb = verb_phrase.split(" ")[0]
    if verb.endswith('y'):
        verb_sg_form = verb[:-1] + 'ies'
    elif verb.endswith(("o", "ch", "s", "sh", "x", "z")):
        verb_sg_form = verb + 'es'
    else:
        verb_sg_form = verb + 's'
    return verb_phrase.replace(verb, verb_sg_form)


def get_word(pos):
    words = random.sample(list(wn.all_lemma_names(getattr(wn, pos))), 5)
    return [i.replace("_", " ") for i in words]


def get_int_org():
    request = requests.get("https://petscan.wmflabs.org/?psid=22536371&format=plain")
    company = request.text.split("\n")[0]
    company_transl = translit(company, "ru", reversed=True)
    return [company_transl]


def get_rus_org():
    nouns = (requests.get("https://petscan.wmflabs.org/?psid=22536392&format=plain")).text.split("\n")
    joined_nouns = " ".join(nouns[0:2]).title().replace(" ", "")
    company = f"Рос{joined_nouns}"
    company_transl = translit(company, "ru", reversed=True)
    return [company_transl]


class Words:
    def __init__(self, fmt):
        self.words = {}
        self.get_words()
        self.format = fmt
        self.fmt = self.prepare_fmt()
        self.result = self.fmt.format(**self.words)

    def get_words(self):
        logging.info("Getting random words")
        poss = s.LINGUISTIC.PARTS_OF_SPEECH
        for pos in poss:
            self.words[pos] = get_word(pos)
        self.words["VERB"] = [make_3sg_form(i) for i in self.words["VERB"]]
        self.words["INT_ORG"] = get_int_org()
        self.words["RUS_ORG"] = get_rus_org()

    def prepare_fmt(self):
        fmt = self.format
        poss = list(self.words.keys())
        for pos in poss:
            op = 0
            while fmt.find(f"{{{pos}}}") != -1:
                fmt = fmt.replace(f"{{{pos}}}", f"{{{pos}[{op}]}}", 1)
                op += 1
        return fmt
