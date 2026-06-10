import os
import subprocess
import sys
from pathlib import Path

DE_MODULE_DIR = Path(__file__).parent


def run(text):
    """Запускает перевод текста в видео"""

    os.chdir(DE_MODULE_DIR)
    sys.path.insert(0, str(DE_MODULE_DIR))

    from spoken_to_signed.bin import text_to_gloss_to_pose_to_video

    lexicon_path = DE_MODULE_DIR / "lexicon"

    # Добавляем venv в PATH
    original_path = os.environ.get("PATH", "")
    venv_scripts = DE_MODULE_DIR / ".venv" / "Scripts"
    os.environ["PATH"] = str(venv_scripts) + os.pathsep + original_path

    # Временное видео (сырое)
    temp_video = DE_MODULE_DIR / "de_temp.mp4"
    # Финальное видео (перекодированное)
    final_video = DE_MODULE_DIR / "de.mp4"

    sys.argv = [
        "text_to_gloss_to_pose_to_video",
        "--text",
        text,
        "--glosser",
        "simple",
        "--lexicon",
        str(lexicon_path),
        "--spoken-language",
        "de",
        "--signed-language",
        "sgg",
        "--video",
        str(temp_video),
    ]

    print(f"Creating video for: {text}")

    try:
        # Создаём сырое видео
        text_to_gloss_to_pose_to_video()
        print("Raw video created")

        # Перекодируем в H.264 для браузера
        if temp_video.exists():
            print("Converting to H.264...")
            cmd = [
                "ffmpeg",
                "-i",
                str(temp_video),
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                "-y",
                str(final_video),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"FFmpeg error: {result.stderr}")
                # Если перекодирование не удалось, используем сырое видео
                import shutil

                shutil.move(str(temp_video), str(final_video))
            else:
                # Удаляем временный файл
                temp_video.unlink()

            print(f"SUCCESS: {final_video}")
        else:
            raise Exception("Video file not created")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()
        raise
    finally:
        os.environ["PATH"] = original_path


if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else "Hallo"
    run(text)
