from rapidfuzz import process, fuzz
import json

prefixes = [
    "без", "бес", "в", "во", "вз", "взо", "вс",
    "вне", "внутри", "воз", "возо", "вос", "все",
    "вы", "до", "за", "из", "изо", "ис", "испод",
    "к", "кое", "кой", "меж", "междо", "между",
    "на", "над", "надо", "наи", "не", "небез", 
    "небес", "недо", "ни", "низ", "низо", "нис",
    "о", "об", "обо", "обез", "обес", "около",
    "от", "ото", "па", "пере", "по", "под", "подо",
    "поза", "после", "пра", "пре", "пред", "предо",
    "преди", "при", "про", "противо", "раз", "разо", 
    "рас", "роз", "рос", "с", "со", "сверх", "среди",
    "су", "сыз", "тре", "у", "чрез", "через", "черес"
]

with open('verb_aspects.json', 'r', encoding='utf-8') as file_verb_aspects:
    verb_aspects = json.load(file_verb_aspects)

def fuzzy_match(word, candidates):
    result = process.extractOne(word, candidates, scorer=fuzz.ratio)
    return result  # (match, score, index)

def map_to_lemma(word: dict, gloss_dict: dict) -> str:
    # Точный матч по лемме
    if word['lemma'] in gloss_dict:
        word['lemma_dict'] = word['lemma']
        return word

    if word["upos"] == 'VERB' and word['lemma'] in verb_aspects:
        word['lemma_dict'] = verb_aspects[word['lemma']]
        return word
    
    for len_prefix in range(8, 1, -1):
        if len(word['lemma']) > len_prefix:
            if word['lemma'][:len_prefix] in prefixes:
                word_without_prefix = word['lemma'][len_prefix:]
                if word_without_prefix in gloss_dict:
                    word['lemma_dict'] = word_without_prefix
                    word["prefix"] = word['lemma'][:len_prefix]
                    return word
                if word["upos"] == 'VERB' and word_without_prefix in verb_aspects:
                    word['lemma_dict'] = verb_aspects[word_without_prefix]
                    word["prefix"] = word['lemma'][:len_prefix]
                    return word
                
    best_match = fuzzy_match(word['lemma'], gloss_dict.keys())
    if best_match and best_match[1] > 60:  # порог сходства
        print(best_match, best_match[1], "тест")
        word['lemma_dict'] = best_match[0]
        return word
    
    word['gloss'] = f"<{word['lemma']}>"
    return word

if __name__ == "__main__":
    word = {'text': 'закупила', 'lemma': 'закупить', 'upos': 'VERB'}
    print(map_to_lemma(word))