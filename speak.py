import sounddevice as sd
import numpy as np
import torch
import pyttsx3
import io
import wave
import whisper
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

device = "cuda" if torch.cuda.is_available() else "cpu"
stt_model = whisper.load_model("small", device=device)

def speak(text: str):
    if not text:
        return
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 180)
        voices = engine.getProperty('voices')
        
        for v in voices:
            if "russian" in v.name.lower() or "ru" in v.id.lower():
                engine.setProperty('voice', v.id)
                break

        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"Error in 'speak' ({e})")

def listen_and_transcribe(duration=4, samplerate=16000) -> str:
    try:
        audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype="int16")
        sd.wait()

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(samplerate)
            wf.writeframes(audio.tobytes())
        
        wav_buffer.seek(0)
        audio_data = np.frombuffer(wav_buffer.read(), dtype=np.int16).astype(np.float32) / 32768.0

        result = stt_model.transcribe(audio_data, language="ru")
        text = result.get("text", "")

        return text.strip().lower()
        
    except Exception as e:
        print(f"Error in 'listen_and_transcribe' ({e})")
        return ""