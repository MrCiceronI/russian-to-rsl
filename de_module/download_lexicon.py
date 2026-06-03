#!/usr/bin/env python3
import argparse
import csv
import os
import sys
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

from pose_format import Pose, PoseHeader
from pose_format.numpy import NumPyPoseBody
from pose_format.utils.reader import BufferReader

LEXICON_INDEX = ["path", "spoken_language", "signed_language", "start", "end", "words", "glosses", "priority"]


def init_index(index_path: str):
    if not os.path.isfile(index_path):
        # Create csv file with specified header
        with open(index_path, "w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(LEXICON_INDEX)


def find_existing_poses(directory_path: str) -> dict:
    """Ищет уже существующие pose файлы в директории"""
    poses_dir = Path(directory_path)
    existing_poses = {}
    
    # Ищем все .pose файлы рекурсивно
    pose_files = list(poses_dir.rglob("*.pose"))
    
    for pose_file in pose_files:
        # Получаем относительный путь от directory_path
        rel_path = pose_file.relative_to(poses_dir)
        existing_poses[str(rel_path)] = {
            "full_path": pose_file,
            "size": pose_file.stat().st_size
        }
    
    return existing_poses


def load_existing_poses(directory_path: str) -> list[dict[str, str]]:
    """Загружает уже существующие pose файлы без повторной загрузки"""
    
    # Папка с распакованными позами (ищем в стандартных местах)
    possible_paths = [
        Path(directory_path) / "extracted" / "poses",
        Path(directory_path) / "poses",
        Path(directory_path),
        Path(directory_path) / "signsuisse" / "poses",
    ]
    
    poses_dir = None
    for path in possible_paths:
        if path.exists() and any(path.rglob("*.pose")):
            poses_dir = path
            print(f"✅ Найдены pose файлы в: {poses_dir}")
            break
    
    if not poses_dir:
        raise FileNotFoundError(
            f"Не найдены pose файлы в {directory_path}\n"
            f"Убедитесь, что вы распаковали архив в одну из папок:\n"
            f"  - {directory_path}/extracted/poses/\n"
            f"  - {directory_path}/poses/\n"
            f"  - {directory_path}/"
        )
    
    # Ищем все pose файлы
    pose_files = list(poses_dir.rglob("*.pose"))
    print(f"🔍 Найдено {len(pose_files)} pose файлов")
    
    # Загружаем заголовок pose (нужен будет для чтения)
    try:
        from sign_language_datasets.datasets.signsuisse.signsuisse import _POSE_HEADERS
        with open(_POSE_HEADERS["holistic"], "rb") as buffer:
            pose_header = PoseHeader.read(BufferReader(buffer.read()))
    except ImportError:
        # Если нет sign_language_datasets, создаем заголовок из первого файла
        print("⚠️ Не удалось загрузить заголовок, пытаемся прочитать из первого файла...")
        if pose_files:
            with open(pose_files[0], "rb") as f:
                pose = Pose.read(f.read())
                pose_header = pose.header
        else:
            raise Exception("Не найден ни один pose файл")
    
    # Маппинг языков
    iana_tags = {
        "sgg": "sgg",  # German Swiss Sign Language
        "ssr": "ssr",  # French Swiss Sign Language  
        "slf": "slf",  # Italian Swiss Sign Language
        "ch-de": "sgg",
        "ch-fr": "ssr",
        "ch-it": "slf",
    }
    
    successful_items = []
    failed_files = []
    
    for pose_file in tqdm(pose_files, desc="Обработка pose файлов"):
        try:
            # Получаем относительный путь
            rel_path = pose_file.relative_to(directory_path)
            
            # Определяем язык из пути или имени файла
            signed_language = "sgg"  # по умолчанию
            path_str = str(pose_file).lower()
            for code, tag in iana_tags.items():
                if code in path_str:
                    signed_language = tag
                    break
            
            # Читаем pose файл для получения длительности
            with open(pose_file, "rb") as f:
                pose = Pose.read(f.read())
            
            duration = len(pose.body.data) / pose.body.fps
            
            # Пытаемся извлечь слова из имени файла
            # Формат обычно: ss<md5>.pose или что-то подобное
            words = pose_file.stem
            
            successful_items.append({
                "path": str(rel_path),
                "spoken_language": "de",  # язык по умолчанию, можно определить из контекста
                "signed_language": signed_language,
                "words": words,
                "start": "0",
                "end": str(duration),
                "glosses": "",
                "priority": "",
            })
            
        except Exception as e:
            print(f"❌ Ошибка при обработке {pose_file}: {e}")
            failed_files.append(str(pose_file))
    
    if failed_files:
        print(f"⚠️ Не удалось обработать {len(failed_files)} файлов")
        if len(failed_files) <= 10:
            for f in failed_files:
                print(f"  - {f}")
    
    print(f"✅ Успешно обработано {len(successful_items)} pose файлов")
    return successful_items


def normalize_row(row: dict[str, str]):
    """Нормализация строки (опционально)"""
    if row["glosses"] == "" and row["words"] != "":
        try:
            from spoken_to_signed.text_to_gloss.simple import text_to_gloss
            sentences = text_to_gloss(text=row["words"], language=row["spoken_language"])
            glosses = [g for sentence in sentences for w, g in sentence]
            row["glosses"] = " ".join(glosses)
        except ImportError:
            # Если модуль недоступен, пропускаем
            pass
        except ValueError as e:
            if not ("Language" in str(e) and "not supported" in str(e)):
                print(f"⚠️ Ошибка нормализации для {row['words']}: {e}")


def get_data(name: str, directory: str):
    """Получение данных в зависимости от источника"""
    data_loaders = {
        "signsuisse": load_existing_poses,
    }
    if name not in data_loaders:
        raise NotImplementedError(f"{name} is unknown.")
    
    return data_loaders[name](directory)


def add_data(data: list[dict[str, str]], directory: str):
    """Добавление данных в индекс"""
    if not data:
        print("⚠️ Нет данных для добавления")
        return
    
    index_path = os.path.join(directory, "index.csv")
    os.makedirs(directory, exist_ok=True)
    init_index(index_path)
    
    # Проверяем уже существующие записи
    existing_paths = set()
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                existing_paths.add(row["path"])
    
    # Добавляем новые записи
    with open(index_path, "a", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        new_count = 0
        
        for row in tqdm(data, desc="Сохранение в индекс"):
            if row["path"] in existing_paths:
                continue
            
            normalize_row(row)
            writer.writerow([row[key] for key in LEXICON_INDEX])
            new_count += 1
    
    print(f"✅ Добавлено {new_count} новых записей в {index_path}")
    print(f"📊 Всего записей в индексе: {len(existing_paths) + new_count}")


def main():
    parser = argparse.ArgumentParser(description="Process existing sign language lexicon poses")
    parser.add_argument("--name", choices=["signsuisse"], required=True, 
                       help="Name of the lexicon to process")
    parser.add_argument("--directory", type=str, required=True, 
                       help="Directory containing the extracted poses")
    args = parser.parse_args()
    
    print(f"🚀 Обработка {args.name} в {args.directory}")
    print("=" * 60)
    
    # Проверяем существование директории
    if not os.path.exists(args.directory):
        print(f"❌ Директория не существует: {args.directory}")
        sys.exit(1)
    
    start_time = datetime.now()
    
    try:
        data = get_data(args.name, args.directory)
        add_data(data, args.directory)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print("=" * 60)
        print(f"✨ Обработка завершена за {elapsed:.1f} секунд!")
        print(f"📁 Данные сохранены в: {os.path.abspath(args.directory)}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()