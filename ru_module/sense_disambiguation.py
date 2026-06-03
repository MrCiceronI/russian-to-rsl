# context_disambiguator.py

import json
import torch
from transformers import AutoTokenizer, AutoModel
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Загрузка модели
tokenizer = AutoTokenizer.from_pretrained("DeepPavlov/rubert-base-cased")
model = AutoModel.from_pretrained("DeepPavlov/rubert-base-cased")

def get_embeddings(texts):
    """Получение эмбеддингов для списка текстов"""
    if isinstance(texts, str):
        texts = [texts]
    
    encoded = tokenizer(
        texts,
        padding=True,
        truncation=True,
        return_tensors='pt',
        max_length=64
    )
    
    with torch.no_grad():
        outputs = model(**encoded)
        # Используем [CLS] токен как эмбеддинг предложения
        embeddings = outputs.last_hidden_state[:, 0, :].numpy()
    
    return embeddings

def select_gloss_by_context(word, original_sentence, gloss_dict):
    """Выбор наиболее подходящего глосса по контексту"""
    
    entry = word['lemma_dict']
    values = gloss_dict[entry]['значения']
    
    # Формируем контекстные описания для каждого значения
    context_descriptions = []
    glosses = []
    
    for val in values:
        gloss = val.get('глосс', '')
        desc = val.get('описание', '')
        contexts = val.get('контекст', [])
        
        # Создаем текстовое описание значения
        text_parts = [desc]
        if contexts:
            text_parts.append("например: " + ", ".join(contexts))
        context_descriptions.append(" ".join(text_parts))
        glosses.append(gloss)
    
    # Получаем эмбеддинги
    # Эмбеддинг исходного предложения
    sent_embedding = get_embeddings(original_sentence)
    
    # Эмбеддинги описаний значений
    desc_embeddings = get_embeddings(context_descriptions)
    
    # Вычисляем косинусное сходство
    similarities = cosine_similarity(sent_embedding, desc_embeddings)[0]
    
    # Выбираем наиболее похожий
    best_idx = np.argmax(similarities)
    
    word['gloss'] = glosses[best_idx]
    
    return word