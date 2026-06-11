import json
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_models = {}
_initialized = False

# Добавляем текущую директорию для импорта модулей
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from mapping import map_to_lemma
from preprocessor import preprocessing
from sense_disambiguation import select_gloss_by_context
from visualisation import concatenate_videos, play_video


def _initialize_models():
    """Однократная инициализация всех тяжелых моделей"""
    global _initialized, _models

    if _initialized:
        return

    print("🔧 Инициализация моделей RSL (первый и последний раз)...")

    try:
        from mapping import map_to_lemma
        from preprocessor import preprocessing
        from sense_disambiguation import select_gloss_by_context
        from visualisation import concatenate_videos, play_video

        _models["map_to_lemma"] = map_to_lemma
        _models["preprocessing"] = preprocessing
        _models["select_gloss_by_context"] = select_gloss_by_context
        _models["concatenate_videos"] = concatenate_videos
        _models["play_video"] = play_video

        # Загрузка словаря
        gloss_dict_path = os.path.join(CURRENT_DIR, "gloss_dict.json")
        with open(gloss_dict_path, "r", encoding="utf-8") as file_gloss_dict:
            _models["gloss_dict"] = json.load(file_gloss_dict)

        _initialized = True
        print("✅ Модели RSL инициализированы")

    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        raise


def get_model(name):
    """Получить модель (с ленивой загрузкой)"""
    if not _initialized:
        _initialize_models()
    return _models.get(name)


def process_text_to_rsl(text: str, output_video_path: str = "result.mp4"):
    """Обрабатывает текст с использованием лениво загруженных моделей"""

    # Гарантируем загрузку моделей
    if not _initialized:
        _initialize_models()

    gloss_dict = _models["gloss_dict"]
    map_to_lemma = _models["map_to_lemma"]
    preprocessing = _models["preprocessing"]
    select_gloss_by_context = _models["select_gloss_by_context"]
    concatenate_videos = _models["concatenate_videos"]

    print(f"Начинаем обработку текста: {text}")

    # Токенизация и предобработка
    tokens = preprocessing(text)
    print(f"Токены: {tokens}")

    # Маппинг токенов
    map_tokens = []
    for token in tokens:
        map_tokens.append(map_to_lemma(token, gloss_dict))

    # Обработка каждого токена
    for number_token in range(len(map_tokens)):
        if "lemma_dict" in map_tokens[number_token]:
            if "значения" in gloss_dict[map_tokens[number_token]["lemma_dict"]]:
                map_tokens[number_token] = select_gloss_by_context(
                    map_tokens[number_token], text, gloss_dict
                )
            else:
                map_tokens[number_token]["gloss"] = gloss_dict[
                    map_tokens[number_token]["lemma_dict"]
                ]["глосс"]

            if (
                "number" in map_tokens[number_token]
                and map_tokens[number_token]["number"] == "Plur"
            ):
                map_tokens[number_token]["gloss"] = (
                    f"+{map_tokens[number_token]['gloss']}"
                )

    # Собираем видео
    video_paths = []
    word_list = []
    processed_tokens = []

    for i, token in enumerate(tokens):
        if "lemma_dict" not in token:
            continue

        lemma = token["lemma_dict"]
        if lemma in gloss_dict:
            if "видео" in gloss_dict[lemma]:
                video_path = gloss_dict[lemma]["видео"]
                video_paths.append(video_path)
            elif "значения" in gloss_dict[lemma] and i < len(map_tokens):
                word_values = gloss_dict[lemma]["значения"]
                for value in word_values:
                    if value["глосс"] == map_tokens[i].get("gloss", ""):
                        video_paths.append(value["видео"])
                        break
            else:
                print(f"Предупреждение: нет видео для леммы {lemma}")
                continue

        word_list.append(token["text"])
        processed_tokens.append(
            {
                "original": token["text"],
                "gloss": map_tokens[i].get("gloss", "") if i < len(map_tokens) else "",
                "video": video_paths[-1] if video_paths else None,
            }
        )

    if not video_paths:
        raise ValueError("Не найдено видео для обработки текста")

    print(f"Создаем видео из {len(video_paths)} фрагментов")
    print(f"Пути для видео: {video_paths}")

    # Создаем видео
    concatenate_videos(video_paths, word_list, text)

    # Перемещаем результат в нужную папку
    import shutil

    temp_result = "result.mp4"
    if os.path.exists(temp_result):
        os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
        shutil.move(temp_result, output_video_path)
        print(f"Видео сохранено: {output_video_path}")

    return {
        "success": True,
        "original_text": text,
        "tokens": processed_tokens,
        "video_path": output_video_path,
        "word_count": len(word_list),
        "char_count": len(text),
    }


# Флаг для проверки инициализации
is_ready = False


def ensure_initialized():
    """Принудительная инициализация (для проверки при старте)"""
    global is_ready
    if not _initialized:
        _initialize_models()
    is_ready = True
    return is_ready


if __name__ == "__main__":
    # Тестирование
    s = "Мама учит сына по книжке"
    result = process_text_to_rsl(s)
    print(f"Обработано {result['word_count']} слов")
