import shutil
import os

# Определяем пути к файлам
files_to_replace = [
    (r".\download_lexicon.py", r".\.venv\Lib\site-packages\spoken_to_signed\download_lexicon.py"),
    (r".\lookup.py", r".\.venv\Lib\site-packages\spoken_to_signed\gloss_to_pose\lookup\lookup.py")
]

# Выполняем замену
for source, destination in files_to_replace:
    try:
        # Проверяем, существует ли исходный файл
        if not os.path.exists(source):
            print(f"Ошибка: Исходный файл не найден: {source}")
            continue
        
        # Создаем директорию назначения, если она не существует
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        # Копируем файл (заменяя существующий)
        shutil.copy2(source, destination)
        print(f"Успешно заменен: {destination}")
        
    except Exception as e:
        print(f"Ошибка при замене {destination}: {e}")

print("Готово!")