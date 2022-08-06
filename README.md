[![py](https://github.com/MurzikVasilyevich/goodpupu/actions/workflows/docker-image.yml/badge.svg)](https://github.com/MurzikVasilyevich/goodpupu/actions/workflows/docker-image.yml)

# Poopoo
The main reason of creating this program is to generate texts about Putin's death.

For me as a proud Citizen of Ukraine, this is something very personal.

Glory to Ukraine! 🇺🇦


Post at Medium: [Death of Putin by AI](https://medium.com/@vasilyevichmurzik/death-of-putin-by-ai-351857745641)

Twitter: [MurzikVasich](https://twitter.com/MurzikVasich)

Telegram channels:
- [Dead Khuilo (EN)](https://t.me/goodpoopoo)
- [Дохле Хуйло (UA)](https://t.me/goodpupua)
- [Дохлое Хуйло (RU)](https://t.me/goodpupu)

## Workflow

1. Creating a query from random words.
2. Fixing the query to be aligned with the English language using OpenAI.
3. Requesting OpenAI to write a text using query as theme.
4. Translating the result from English.
5. Posting results to Telegram channel.

### 1. Creating a query from random words
Words are taken randomly from the categories of Wiktionary: adjective, verb, noun, adverb.
Style is taken randomly from the appropriate Wikipedia categories.
Format of the query is:

`Write a {genre} about how {adjective} Person {verb} by {noun} and {adverb} sleeps.`

### 2. Fixing the query
Query is fixed by request to OpenAI:

`Correct this to standard English: {query}`
