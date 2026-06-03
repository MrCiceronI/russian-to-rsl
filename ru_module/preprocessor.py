import stanza
import re
from reordering import reorder_to_rsl

# stanza.download('ru')
nlp = stanza.Pipeline('ru', processors='tokenize,pos,lemma,depparse')

stop_upos = ['ADP', 'CCONJ', 'SCONJ', 'PUNCT']
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