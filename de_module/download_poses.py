import urllib.request
import tarfile
import os

url = "https://datasets.sigma-sign-language.com/poses/holistic/signsuisse.tar"
extract_path = r".\lexicon"

os.makedirs(extract_path, exist_ok=True)

archive_path = os.path.join(extract_path, "signsuisse.tar")

print("Начинаю скачивание архива...")
urllib.request.urlretrieve(url, archive_path)
print("Скачивание завершено.")

print("Распаковка архива...")
with tarfile.open(archive_path, "r") as tar:
    tar.extractall(path=extract_path)
print("Распаковка завершена.")

os.remove(archive_path)
print("Архив удален. Готово.")