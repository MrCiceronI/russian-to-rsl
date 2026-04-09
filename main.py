from preprocessor import preprocessing
from mapping import map_to_lemma
import json
from sense_disambiguation import select_gloss_by_context
#from reordering import reorder_to_rsl

with open('gloss_dict.json', 'r', encoding='utf-8') as file_gloss_dict:
    gloss_dict = json.load(file_gloss_dict)

s = "Мама учит сына по красивой книжечке."

tokens = preprocessing(s)

map_tokens = []
for token in tokens:
    print(token)
    map_tokens.append(map_to_lemma(token, gloss_dict))

for number_token in range(len(map_tokens)):
    if 'lemma_dict' in map_tokens[number_token]:
        if 'значения' in gloss_dict[map_tokens[number_token]['lemma_dict']]:
            map_tokens[number_token] = select_gloss_by_context(map_tokens[number_token], s, gloss_dict)
        else:
            map_tokens[number_token]["gloss"] = gloss_dict[map_tokens[number_token]['lemma_dict']]['глосс']
        
        if 'number' in map_tokens[number_token] and map_tokens[number_token]['number'] == 'Plur':
            map_tokens[number_token]["gloss"] = f"+{map_tokens[number_token]["gloss"]}"

for token in tokens:
   print(token['gloss'])

#gloss_list = reorder_to_rsl(map_tokens, s)
#print(" ".join(gloss_list))