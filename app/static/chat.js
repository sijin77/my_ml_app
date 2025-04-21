const socket = new WebSocket("ws://localhost:8000/ws");
const iriskaEmojis = ["💋", "🔥", "🎩", "👾", "🍪", "🤖", "💃", "🐍"];

// Проверка подключения
socket.onopen = () => {
    console.log("Чат подключён! 🔥");
    document.getElementById("status").textContent = "🟢";
};

socket.onerror = (error) => {
    console.error("Ошибка WebSocket:", error);
    document.getElementById("status").textContent = "🔴";
};

// Получение сообщений
socket.onmessage = (event) => {
    const chatDiv = document.getElementById("chat");
    const messageElement = document.createElement("div");
    messageElement.className = "message";
    messageElement.textContent = event.data;
    chatDiv.appendChild(messageElement);
    chatDiv.scrollTop = chatDiv.scrollHeight;  // Автоскролл
};

// Отправка сообщений
function sendMessage() {
    const input = document.getElementById("messageInput");
    if (input.value.trim() !== "") {
        socket.send(input.value);
        input.value = "";
    }
}

// Отправка по Enter
document.getElementById("messageInput").addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        sendMessage();
    }
});

// Кнопка эмодзи
document.getElementById("emojiBtn").addEventListener("click", () => {
    const randomEmoji = iriskaEmojis[Math.floor(Math.random() * iriskaEmojis.length)];
    document.getElementById("messageInput").value += randomEmoji;
});

// Голосовые сообщения (если браузер поддерживает)
if ("webkitSpeechRecognition" in window) {
    const recognition = new webkitSpeechRecognition();
    recognition.lang = "ru-RU";

    recognition.onresult = (event) => {
        const voiceText = event.results[0][0].transcript;
        socket.send(voiceText);
    };

    document.getElementById("voiceBtn").addEventListener("click", () => {
        recognition.start();
    });
} else {
    document.getElementById("voiceBtn").style.display = "none";
}