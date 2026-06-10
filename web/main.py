import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
import wave
from pathlib import Path

import vosk
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Добавляем родительскую директорию в путь для импорта
# Поднимаемся на уровень выше (из web/ в project/)
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from ru_module.rsl_main import ensure_initialized as ensure_ru_initialized
from ru_module.rsl_main import process_text_to_rsl

# Импортируем немецкий модуль
try:
    from de_module.translate_text import translate_text_to_video

    DE_MODULE_AVAILABLE = True
    print("✅ Немецкий модуль загружен")
except ImportError as e:
    DE_MODULE_AVAILABLE = False
    print(f"⚠️ Немецкий модуль не загружен: {e}")

app = FastAPI()


# ИНИЦИАЛИЗАЦИЯ ПРИ ЗАПУСКЕ (один раз)
@app.on_event("startup")
async def startup_event():
    """Выполняется один раз при запуске сервера"""
    print("🚀 Запуск сервера, инициализация моделей...")
    try:
        ensure_ru_initialized()
        print("✅ Все модели загружены успешно")
    except Exception as e:
        print(f"❌ Ошибка загрузки моделей: {e}")


# Создаём папки для видео
VIDEO_DIR_RU = Path(__file__).parent / "videos_ru"
VIDEO_DIR_DE = Path(__file__).parent / "videos_de"
VIDEO_DIR_RU.mkdir(exist_ok=True)
VIDEO_DIR_DE.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount(
    "/videos_ru", StaticFiles(directory=str(VIDEO_DIR_RU.absolute())), name="videos_ru"
)
app.mount(
    "/videos_de", StaticFiles(directory=str(VIDEO_DIR_DE.absolute())), name="videos_de"
)

templates = Jinja2Templates(directory="templates")

# Загружаем модели Vosk для распознавания речи
vosk_models = {}

model_paths = {
    "ru": "vosk-model-small-ru-0.22",
    "de": "vosk-model-small-de-0.15",
}

# Загружаем модели
for lang, path in model_paths.items():
    if os.path.exists(path):
        try:
            vosk_models[lang] = vosk.Model(path)
            print(f"✅ Модель для языка '{lang}' загружена")
        except Exception as e:
            print(f"❌ Ошибка загрузки модели для '{lang}': {e}")
    else:
        print(f"⚠️ Модель для языка '{lang}' не найдена по пути: {path}")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/api/process-text")
async def process_text(userText: str = Form(...), target_lang: str = Form("ru")):
    """
    Обрабатывает текст и создает видео с демонстрацией языка жестов
    Поддерживает русский (ru) и немецкий (de) языки
    """
    try:
        print(f"📝 Обработка текста: {userText[:50]}...")
        print(f"🌐 Целевой язык: {target_lang}")

        if target_lang == "ru":
            # Русский язык - используем ru_module
            video_filename = f"{uuid.uuid4().hex}.mp4"
            video_path = VIDEO_DIR_RU / video_filename

            result = process_text_to_rsl(userText, str(video_path))

            video_url = f"/videos_ru/{video_filename}"

            return JSONResponse(
                content={
                    "success": True,
                    "video_url": video_url,
                    "language": "ru",
                }
            )

        elif target_lang == "de":
            # Немецкий язык - используем de_module
            if not DE_MODULE_AVAILABLE:
                return JSONResponse(
                    status_code=503,
                    content={
                        "success": False,
                        "error": "Немецкий модуль временно недоступен",
                    },
                )

            # Устанавливаем переменную окружения для веб-вызова
            os.environ["RSL_WEB_CALL"] = "1"

            # Немецкий модуль создаёт файл de.mp4, нужно переименовать
            temp_video = Path(__file__).parent / "de.mp4"
            video_filename = f"{uuid.uuid4().hex}.mp4"
            video_path = VIDEO_DIR_DE / video_filename

            # Вызываем немецкий модуль
            translate_text_to_video(text=userText)

            # Перемещаем созданное видео
            if temp_video.exists():
                shutil.move(str(temp_video), str(video_path))
            else:
                # Проверяем в папке de_module
                de_module_video = Path(__file__).parent.parent / "de_module" / "de.mp4"
                if de_module_video.exists():
                    shutil.move(str(de_module_video), str(video_path))
                else:
                    raise Exception("Немецкий модуль не создал видео файл")

            video_url = f"/videos_de/{video_filename}"

            # Для немецкого языка пока нет детального разбора токенов
            return JSONResponse(
                content={
                    "success": True,
                    "video_url": video_url,
                    "language": "de",
                }
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": f"Неподдерживаемый язык: {target_lang}",
                },
            )

    except Exception as e:
        print(f"❌ Ошибка обработки: {e}")
        import traceback

        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Ошибка обработки: {str(e)}"},
        )


@app.post("/api/speech-to-text")
async def speech_to_text(audio: UploadFile = File(...), language: str = Form("ru")):
    """
    Принимает WebM аудио, конвертирует через ffmpeg и распознает
    """
    print(f"Получен файл: {audio.filename}, язык: {language}")

    # Проверяем модель Vosk
    if language not in vosk_models:
        return JSONResponse(
            status_code=400,
            content={"error": f"Модель для языка '{language}' не загружена"},
        )

    try:
        # Читаем аудио
        audio_data = await audio.read()
        print(f"Размер аудио: {len(audio_data)} байт")

        if len(audio_data) < 1000:
            return JSONResponse(
                status_code=400, content={"error": "Аудио слишком короткое"}
            )

        # Создаем временные файлы
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp_input:
            tmp_input.write(audio_data)
            input_path = tmp_input.name

        output_path = input_path.replace(".webm", ".wav")

        # Конвертируем webm в wav с помощью ffmpeg
        cmd = [
            "ffmpeg",
            "-i",
            input_path,
            "-acodec",
            "pcm_s16le",  # 16-bit PCM
            "-ar",
            "16000",  # 16kHz
            "-ac",
            "1",  # моно
            "-y",  # перезаписывать выходной файл
            output_path,
        ]

        print(f"Запуск ffmpeg: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"FFmpeg ошибка: {result.stderr}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Ошибка конвертации аудио. Проверьте установку ffmpeg."
                },
            )

        # Проверяем, что выходной файл создан
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            return JSONResponse(
                status_code=500, content={"error": "Не удалось сконвертировать аудио"}
            )

        print(f"WAV файл создан, размер: {os.path.getsize(output_path)} байт")

        # Распознаем через Vosk
        wf = wave.open(output_path, "rb")

        # Проверяем параметры WAV
        print(f"WAV параметры: {wf.getnchannels()} каналов, {wf.getframerate()} Hz")

        # Создаем распознаватель
        rec = vosk.KaldiRecognizer(vosk_models[language], wf.getframerate())

        texts = []

        # Читаем и распознаем блоками
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                if res.get("text"):
                    texts.append(res["text"])

        # Финальный результат
        final = json.loads(rec.FinalResult())
        if final.get("text"):
            texts.append(final["text"])

        wf.close()

        # Удаляем временные файлы
        os.unlink(input_path)
        os.unlink(output_path)

        recognized_text = " ".join(texts).strip()
        print(f"Распознанный текст: '{recognized_text}'")

        if not recognized_text:
            return JSONResponse(
                content={
                    "success": False,
                    "text": "",
                    "error": "Не удалось распознать речь. Говорите четче.",
                }
            )

        return JSONResponse(
            content={"success": True, "text": recognized_text, "language": language}
        )

    except Exception as e:
        print(f"Ошибка распознавания Vosk: {e}")
        return JSONResponse(
            status_code=500, content={"error": f"Ошибка распознавания: {str(e)}"}
        )


@app.get("/api/languages")
async def get_languages():
    """Возвращает список доступных языков для распознавания и перевода"""
    languages = []

    # Русский
    languages.append(
        {
            "code": "ru",
            "name": "Русский",
            "available_for_speech": "ru" in vosk_models,
            "available_for_translation": True,
        }
    )

    # Немецкий
    languages.append(
        {
            "code": "de",
            "name": "Deutsch",
            "available_for_speech": "de" in vosk_models,
            "available_for_translation": DE_MODULE_AVAILABLE,
        }
    )

    return JSONResponse(content={"languages": languages})
