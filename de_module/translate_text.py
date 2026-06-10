# import sys

# from spoken_to_signed.bin import text_to_gloss_to_pose_to_video


# def translate_text_to_video(text):
#     """Удобная функция для перевода текста в видео"""

#     # Сохраняем оригинальный sys.argv
#     original_argv = sys.argv.copy()

#     # Устанавливаем новые аргументы
#     sys.argv = [
#         "text_to_gloss_to_pose_to_video",  # имя скрипта
#         "--text",
#         text,
#         "--glosser",
#         "simple",
#         "--lexicon",
#         "./lexicon",
#         "--spoken-language",
#         "de",
#         "--signed-language",
#         "sgg",
#         "--video",
#         "de.mp4",
#     ]

#     try:
#         # Вызываем функцию
#         text_to_gloss_to_pose_to_video()
#         print(f"Видео успешно создано: de.mp4")
#     except Exception as e:
#         print(f"Ошибка: {e}")
#         raise
#     finally:
#         # Восстанавливаем оригинальный sys.argv
#         sys.argv = original_argv


# # Использование
# if __name__ == "__main__":
#     translate_text_to_video(
#         text="Entschuldigen sie, haben Sie Deutsch?",
#     )

import os
import subprocess
import sys
from pathlib import Path


def translate_text_to_video(text):
    """Удобная функция для перевода текста в видео"""

    # Определяем директорию модуля
    DE_MODULE_DIR = Path(__file__).parent.absolute()

    # Проверяем, вызываем ли мы из веба
    is_web_call = os.environ.get("RSL_WEB_CALL") == "1"

    if is_web_call:
        # Режим 2: Запуск через отдельный процесс (для веба)
        return _run_in_subprocess(text, DE_MODULE_DIR)
    else:
        # Режим 1: Прямой запуск (оригинальный функционал)
        return _run_direct(text)


def _run_direct(text):
    """Оригинальный способ - прямая работа с sys.argv"""

    from spoken_to_signed.bin import text_to_gloss_to_pose_to_video

    original_argv = sys.argv.copy()

    sys.argv = [
        "text_to_gloss_to_pose_to_video",
        "--text",
        text,
        "--glosser",
        "simple",
        "--lexicon",
        "./lexicon",
        "--spoken-language",
        "de",
        "--signed-language",
        "sgg",
        "--video",
        "de.mp4",
    ]

    try:
        text_to_gloss_to_pose_to_video()
        print(f"Видео успешно создано: de.mp4")
        return True
    except Exception as e:
        print(f"Ошибка: {e}")
        raise
    finally:
        sys.argv = original_argv


def _run_in_subprocess(text, de_module_dir):
    """Запуск в отдельном процессе с правильным окружением"""

    # Путь к Python в venv de_module
    venv_python = de_module_dir / ".venv" / "Scripts" / "python.exe"

    if not venv_python.exists():
        raise FileNotFoundError(f"Python в venv не найден: {venv_python}")

    print(f"Используем Python: {venv_python}")

    # Путь к run_de.py
    run_script = de_module_dir / "run_de.py"

    if not run_script.exists():
        raise FileNotFoundError(f"run_de.py не найден: {run_script}")

    try:
        # Запускаем процесс через venv Python
        result = subprocess.run(
            [str(venv_python), str(run_script), text],
            cwd=str(de_module_dir),
            capture_output=True,
            text=True,
        )

        print(f"stdout: {result.stdout}")
        if result.stderr:
            print(f"stderr: {result.stderr}")

        if result.returncode != 0:
            raise Exception(
                f"Процесс завершился с кодом {result.returncode}: {result.stderr}"
            )

        # Проверяем, создалось ли видео
        video_path = de_module_dir / "de.mp4"
        if not video_path.exists():
            raise Exception("Видео не было создано")

        print(f"Видео успешно создано: {video_path}")
        return True

    except Exception as e:
        print(f"Ошибка в подпроцессе: {e}")
        raise


# Использование
if __name__ == "__main__":
    # При прямом запуске используем оригинальный режим
    translate_text_to_video(
        text="Sie",
    )
