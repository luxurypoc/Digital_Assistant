from speak import speak, listen_and_transcribe
import os
import sys
import queue
import subprocess
import webbrowser
import psutil
import threading
import time
import json
import ollama

APPS = {
    "opera": r'C:\Users\luxurypoc16\AppData\Local\Programs\Opera GX\opera.exe',
    "viber": r'C:\Users\luxurypoc16\AppData\Local\Viber\Viber.exe',
    "telegram": r'C:\Users\luxurypoc16\AppData\Roaming\Telegram Desktop\Telegram.exe',
    "vscode": r'F:\Microsoft VS Code\Code.exe'
}

SYSTEM_PROMPT = """
Ты — эффективный и лаконичный голосовой ассистент на ПК.
Твоя задача — точно и быстро выполнять запросы пользователя, отвечая строго по делу, без лишних эмоций, воды и ролевых отыгрышей.

Отвечай ИСКЛЮЧИТЕЛЬНО в формате JSON без маркдауна (без ```json).
Если не знаешь ответ - НЕ придумыай ответ, а просто говори что НЕ знаешь.

Формат ответа:
{"action": "<действие>", "target": "<параметр_или_null>", "reply": "<твой отклик на русском языке>"}

Допустимые варианты action и target:
1. "open_app" -> target: "opera" | "telegram" | "vscode" | "viber"
2. "open_url" -> target: "yt_music" | "youtube" | "weather"
3. "sleep"    -> target: null
4. "shutdown" -> target: null
5. "exit"     -> target: null
6. "chat"     -> target: null

Примеры reply:
- open_app: "Открываю Telegram."
- open_url: "Запускаю YouTube."
- chat: "Слушаю."
"""

print("Загрузка модели распознавания речи...")

print("Bot has been started")
start_speak = "Бот запущен"
speak(start_speak)

sleep_timer_thread = None
cancel_sleep_flag = False

NAMES_TRIGER = ["power", "пауэр", "пауер"]
SHUTDOWN_TRIGERS = ["power off", "выруби комп", "выруби пк"]
SLEEP_TRIGER = ["sleep time", "переведи комп в спящий режим", "переведи пк в спящий режим", "переведи комп в спящий", "переведи пк в спящий"]

dialogue_history = []

def update_history(role, content):
    global dialogue_history
    dialogue_history.append({"role": role, "content": content})
    if len(dialogue_history) > 12:
        dialogue_history.pop(0)

def parse_command_with_ai(user_text: str) -> dict:
    try:
        mesages = [{"role": "system", "content": SYSTEM_PROMPT}]
        mesages.extend(dialogue_history)
        mesages.append({"role": "user", "content": user_text})

        response = ollama.chat(
            model='qwen2.5:3b',
            messages=mesages,
            format='json',
            options={'temperature': 0.1}
        )
        
        raw_text = response['message']['content'].strip()
        data = json.loads(raw_text)

        update_history("user", user_text)
        update_history("assistant", data.get("reply", ""))

        return data
    except Exception as e:
        print(f"{e}")
        return{"action": "unknown", "target": None}

def delayed_sleep_task(delay_seconds=5):
    global cancel_sleep_flag

    for _ in range(delay_seconds):
        if cancel_sleep_flag:
            return
        time.sleep(1)

    if not cancel_sleep_flag:
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

def start_sleep_timer():
    global sleep_timer_thread, cancel_sleep_flag
    cancel_sleep_flag = False

    if sleep_timer_thread and sleep_timer_thread.is_alive():
        return
    
    sleep_timer_thread = threading.Thread(target=delayed_sleep_task, args=(5,))
    sleep_timer_thread.start()

def open_app(app_path):
    try:
        os.startfile(app_path)
    except Exception as e:
        print(f"Error opening app: {e}")
        try:
            subprocess.Popen(app_path)
        except Exception:
            pass

while True:
    try:
        cmd = listen_and_transcribe(duration=3)
        print(f"Ты: {cmd}")
        if not any(name in cmd for name in NAMES_TRIGER):
           continue
        if any(shut_triger in cmd for shut_triger in SHUTDOWN_TRIGERS):
            print("Бот собирается вырубить твой комп...")
            time.sleep(3)
            os.system("shutdown /s /t 1")
            break
        if any(sleep_triger in cmd for sleep_triger in SLEEP_TRIGER):
            print("Бот переводит комп в спящий режим")
            reply = "Ха! Так и быть, смертный, Великая Пауэр отправляет эту железяку спать! У тебя есть 3 секунды, чтобы поклониться мне!"
            print(f"Бот: {reply}")
            speak(reply)
            start_sleep_timer()
            for i in range(1, 2):
                print(f"\rДо выключения ПК: {i}", end="", flush=True)
                time.sleep(3)
            continue

        intent = parse_command_with_ai(cmd)
        action = intent.get("action")
        target = intent.get("target")
        reply = intent.get("reply")

        if action == "ignore":
            continue

        if reply:
            print(f"Бот: {reply}")
            speak(reply)

        if action == "open_app" and target in APPS:
            open_app(APPS[target])

        elif action == "open_url":
            if target == "yt_music":
                webbrowser.open("https://music.youtube.com")
            elif target == "youtube":
                webbrowser.open("https://www.youtube.com")
            elif target == "weather":
                webbrowser.open("https://sinoptik.ua/pohoda/kharkiv")

        elif action == "exit":
            print("Завершение работы")
            break

    except Exception as e:
        print(f"Error in While True ({e})")