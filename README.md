# Перевод в глоссы языков жестов 
Веб-приложение для перевода текста и речи на русском и немецком языках в язык жестов (РЖЯ и DGS).

## Требования
1) [Python 3.11](https://www.python.org/downloads/release/python-3119/)
2) [FFmpeg](https://ffmpeg.org/download.html)

## Установка

### 1. Клонируйте репозиторий

```sh 
git clone https://github.com/MrCiceronI/russian-to-rsl.git
cd russian-to-rsl
```

### 2. Настройте русский модуль

```sh
cd ru_module
pip install -r requirements.txt
cd ..
```

### 3. Настройте немецкий модуль в отдельном окружении

Скачайте позы [signsuisse.tar](https://datasets.sigma-sign-language.com/poses/holistic/signsuisse.tar) и распакуйте в de_module/lexicon.

```sh
cd de_module
python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt

python replace_files.py

download_lexicon --name signsuisse --directory "./lexicon"

cd ..
```

### 4. Настройте веб-приложение

Скачайте модели [vosk-model-small-ru-0.22.zip](https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip) и [vosk-model-small-de-0.15.zip](https://alphacephei.com/vosk/models/vosk-model-small-de-0.15.zip) для распознавания речи, затем распакуйте в web.

```sh 
cd web
pip install -r requirements.txt
```

### 5. Запустите локальный сервер
```sh 
uvicorn main:app --reload
```

Откройте браузер:
http://127.0.0.1:8000

## Использование

1. Выберите язык (русский или немецкий).
2. Введите текст или нажмите кнопку голосового ввода.
3. Нажмите "Перевести в жесты".
