let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let selectedLanguage = "ru";

const textInput = document.getElementById("textInput");
const submitBtn = document.getElementById("submitBtn");
const voiceBtn = document.getElementById("voiceBtn");
const videoBlock = document.getElementById("videoBlock");
const resultVideo = document.getElementById("resultVideo");
const statusDiv = document.getElementById("status");

// Обработчик переключения радиокнопок
const radioButtons = document.querySelectorAll('input[name="language"]');
radioButtons.forEach((radio) => {
  radio.addEventListener("change", (e) => {
    selectedLanguage = e.target.value;
    const langName =
      selectedLanguage === "ru" ? "Русский → РЖЯ" : "Deutsch → DGS";
    showStatus(`🌐 Выбран язык: ${langName}`, "info");

    // Обновляем placeholder
    textInput.placeholder =
      selectedLanguage === "ru"
        ? "Введите текст на русском или используйте голосовой ввод..."
        : "Geben Sie Text auf Deutsch ein oder verwenden Sie Spracheingabe...";
  });
});

function showStatus(message, type = "info") {
  statusDiv.textContent = message;
  statusDiv.className = `status ${type}`;
  statusDiv.style.display = "block";
  setTimeout(() => {
    if (statusDiv.style.display !== "none") {
      statusDiv.style.display = "none";
    }
  }, 5000);
}

async function submitText(text) {
  if (!text.trim()) {
    showStatus("Пожалуйста, введите текст", "error");
    return false;
  }

  // Скрываем предыдущее видео
  videoBlock.style.display = "none";
  submitBtn.disabled = true;
  submitBtn.textContent = "Отправка...";

  try {
    const formData = new FormData();
    formData.append("userText", text);
    formData.append("target_lang", selectedLanguage); // Добавляем язык перевода

    const response = await fetch("/api/process-text", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      throw new Error(data.error || "Ошибка обработки");
    }

    // Показываем видео
    if (data.video_url) {
      resultVideo.src = data.video_url;
      resultVideo.load();
      videoBlock.style.display = "block";
    }

    showStatus("✅ Видео готово!", "success");

    return true;
  } catch (error) {
    console.error("Ошибка:", error);
    showStatus(`❌ Ошибка: ${error.message}`, "error");
    return false;
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "🤟 Перевести в жесты";
  }
}

async function startRecording() {
  audioChunks = [];

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    // Пробуем разные форматы
    let mimeType = "";
    if (MediaRecorder.isTypeSupported("audio/webm")) {
      mimeType = "audio/webm";
    } else if (MediaRecorder.isTypeSupported("audio/mp4")) {
      mimeType = "audio/mp4";
    } else {
      mimeType = "";
    }

    mediaRecorder = new MediaRecorder(stream, { mimeType });

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data);
      }
    };

    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach((track) => track.stop());

      if (audioChunks.length === 0) {
        showStatus("Не удалось записать аудио", "error");
        return;
      }

      const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
      await sendAudioToServer(audioBlob);
    };

    mediaRecorder.start(1000);
    isRecording = true;
    voiceBtn.classList.add("recording");
    voiceBtn.textContent = "⏹️ Остановить запись";
    showStatus(
      `🎙️ Говорите на ${selectedLanguage === "ru" ? "русском" : "немецком"}...`,
      "info",
    );
  } catch (error) {
    console.error("Ошибка:", error);
    showStatus("❌ Нет доступа к микрофону", "error");
  }
}

function stopRecording() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    isRecording = false;
    voiceBtn.classList.remove("recording");
    voiceBtn.textContent = "🎤 Голосовой ввод";
    showStatus("⏳ Обработка...", "info");
  }
}

async function sendAudioToServer(audioBlob) {
  voiceBtn.disabled = true;

  try {
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.webm");
    formData.append("language", selectedLanguage);

    const response = await fetch("/api/speech-to-text", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Ошибка сервера");
    }

    if (data.success) {
      textInput.value = data.text;
      showStatus(`✅ Распознано: "${data.text}"`, "success");
      await submitText(data.text);
    } else {
      showStatus(`❌ ${data.error}`, "error");
    }
  } catch (error) {
    console.error("Ошибка:", error);
    showStatus(`❌ ${error.message}`, "error");
  } finally {
    voiceBtn.disabled = false;
  }
}

submitBtn.addEventListener("click", () => submitText(textInput.value));
voiceBtn.addEventListener("click", () => {
  if (isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
});

// Проверка поддержки
if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
  voiceBtn.disabled = true;
  showStatus("❌ Голосовой ввод не поддерживается", "error");
}
