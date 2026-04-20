import stanza
import re
from reordering import reorder_to_rsl

# stanza.download('ru')
nlp = stanza.Pipeline('ru', processors='tokenize,pos,lemma,depparse')

stop_upos = ['ADP', 'CCONJ', 'SCONJ', 'PART', 'PUNCT']
time_adverbs = ["сейчас", "сегодня", "вчера", "завтра",
                "утром", "днем", "вечером", "ночью"]

def preprocessing(sent: str) -> list:

    tokens = []
    doc = nlp(sent)

    for word in doc.sentences[0].words:
        if word.text in time_adverbs:
            tokens.append({'id': f'{word.id}', 'head': f'{word.head}' if word.head else None, 'text': f'{word.text}', 'lemma': f'{word.text.lower()}', 'upos': 'ADV', 'deprel': f'{word.deprel}'})
            continue
        if word.upos not in stop_upos:
            lemma = word.lemma.lower()
            token = {'id': f'{word.id}', 'head': f'{word.head}' if word.head else None, 'text': f'{word.text}', 'lemma': f'{lemma}', 'upos': f'{word.upos}', 'deprel': f'{word.deprel}'}
            if word.upos == "NOUN":
                token['number'] = re.search(r'Number=(Sing|Plur)', word.feats).group(1)
            tokens.append(token)

    tokens = reorder_to_rsl(tokens)

    return tokens
if __name__ == "__main__":
    """
    for s in ["Я подобрался, и передал книжечку!", "Завтра я пойду в школу утром", "Где мой телефон?"]:
        tokens = preprocessing(s)
        result = []
        for i in tokens:
            result.append(i['lemma'])
        print(result)"""

    s = "Мама купила мне книги."
    tokens = preprocessing(s)
    print(tokens)
