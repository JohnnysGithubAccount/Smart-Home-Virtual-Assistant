import speech_recognition as sr
import winsound

# === Initialize speech recognizer ===
recognizer = sr.Recognizer()


def listen():
    with sr.Microphone() as source:
        print("[INFO] 🎤 Listening...")
        # speak('listening')
        winsound.Beep(1000, 300)

        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        print(f"🗣 User: {text}")
        return text
    except sr.UnknownValueError:
        print("❌ Could not understand audio")
        return None
    except sr.RequestError as e:
        print(f"⚠️ Could not request results; {e}")
        return None