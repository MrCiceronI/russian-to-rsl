import sys
from spoken_to_signed.bin import text_to_gloss_to_pose_to_video

def translate_text_to_video(text):
    """Удобная функция для перевода текста в видео"""
    
    # Сохраняем оригинальный sys.argv
    original_argv = sys.argv.copy()
    
    # Устанавливаем новые аргументы
    sys.argv = [
        "text_to_gloss_to_pose_to_video",  # имя скрипта
        "--text", text,
        "--glosser", "simple",
        "--lexicon", "./lexicon",
        "--spoken-language", "de",
        "--signed-language", "sgg",
        "--video", "de.mp4"
    ]
    
    try:
        # Вызываем функцию
        text_to_gloss_to_pose_to_video()
        print(f"Видео успешно создано: de.mp4")
    except Exception as e:
        print(f"Ошибка: {e}")
        raise
    finally:
        # Восстанавливаем оригинальный sys.argv
        sys.argv = original_argv

# Использование
if __name__ == "__main__":
    translate_text_to_video(
        text="Kleine Kinder essen Pizza in Zürich.",
    )