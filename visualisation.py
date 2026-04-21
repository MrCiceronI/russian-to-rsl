import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def concatenate_videos(video_paths, word_list, sent):
    out = cv2.VideoWriter("result.mp4", cv2.VideoWriter_fourcc(*'mp4v'), 30, (1280, 720))

    # Склеиваем
    for path, word in zip(video_paths, word_list):
        parts = sent.split(word)
        cap = cv2.VideoCapture(f"videos\{path}")

        try:
            font = ImageFont.truetype("arial.ttf", 48)
        except:
            font = ImageFont.load_default()

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.resize(frame, (1280, 720))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            draw = ImageDraw.Draw(pil_img)
            # Рисуем текст частями
            x = 100
            y = 600
            
            # Первая часть (белым)
            if parts[0]:
                draw.text((x, y), parts[0], font=font, fill=(255, 255, 255))
                # Примерная ширина текста (зависит от шрифта)
                bbox = draw.textbbox((x, y), parts[0], font=font)
                x = bbox[2]
            
                    # Выделенное слово (желтое)
            draw.text((x, y), word, font=font, fill=(255, 0, 0))
            bbox = draw.textbbox((x, y), word, font=font)
            x = bbox[2]
            
            # Вторая часть (белая)
            if len(parts) > 1 and parts[1]:
                draw.text((x, y), parts[1], font=font, fill=(255, 255, 255))
            
            frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            out.write(frame)
        cap.release()

    out.release()
    print("видео сохранено как result.mp4")

def play_video(video_path):
    # Воспроизвести склеенное видео
    cap = cv2.VideoCapture(video_path)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow('Video', cv2.resize(frame, (1280, 720)))
        if cv2.waitKey(30) & 0xFF == 27:  # ESC для выхода
            break
    cap.release()
    cv2.destroyAllWindows()