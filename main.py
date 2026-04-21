from preprocessor import preprocessing
from mapping import map_to_lemma
import json
from sense_disambiguation import select_gloss_by_context
from visualisation import play_video, concatenate_videos

with open('gloss_dict.json', 'r', encoding='utf-8') as file_gloss_dict:
    gloss_dict = json.load(file_gloss_dict)

s = "Мама учит сына по книжке"

tokens = preprocessing(s)

map_tokens = []
for token in tokens:
    map_tokens.append(map_to_lemma(token, gloss_dict))

for number_token in range(len(map_tokens)):
    if 'lemma_dict' in map_tokens[number_token]:
        if 'значения' in gloss_dict[map_tokens[number_token]['lemma_dict']]:
            map_tokens[number_token] = select_gloss_by_context(map_tokens[number_token], s, gloss_dict)
        else:
            map_tokens[number_token]["gloss"] = gloss_dict[map_tokens[number_token]['lemma_dict']]['глосс']
        
        if 'number' in map_tokens[number_token] and map_tokens[number_token]['number'] == 'Plur':
            map_tokens[number_token]["gloss"] = f"+{map_tokens[number_token]["gloss"]}"

video_pathes = []
word_list = []
for token in tokens:
    print(token)
    if "lemma_dict" not in token:
        continue
    if "видео" in gloss_dict[token["lemma_dict"]]:
        video_pathes.append(gloss_dict[token["lemma_dict"]]['видео'])
    else:
        word_values = gloss_dict[token["lemma_dict"]]["значения"]
        for value in word_values:
            if value["глосс"] == token["gloss"]:
                video_pathes.append(value["видео"])
    word_list.append(token['text'])

concatenate_videos(video_pathes, word_list, s)
play_video("result.mp4")