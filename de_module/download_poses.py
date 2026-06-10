import os
import tarfile

import wget

url = "https://datasets.sigma-sign-language.com/poses/holistic/signsuisse.tar"
extract_path = r".\lexicon"

os.makedirs(extract_path, exist_ok=True)

# wget автоматически поддерживает докачку
filename = wget.download(url, out=extract_path, bar=wget.bar_adaptive)

print("\nРаспаковка...")
with tarfile.open(os.path.join(extract_path, "signsuisse.tar"), "r") as tar:
    tar.extractall(path=extract_path)

os.remove(os.path.join(extract_path, "signsuisse.tar"))
print("Готово!")
