import asyncio
import datetime
import hashlib
import os
import subprocess
import sys
import tempfile
import urllib.parse
import webbrowser

import edge_tts
import pygame
import speech_recognition as sr
import wikipedia

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None


# ============================================================
# CONFIG
# ============================================================

ASSISTANT_NAME = "Hella"

VOICE = "en-IN-AartiNeural"
LANGUAGE = "en-IN"

# None = default microphone
MICROPHONE_DEVICE_INDEX = None

# Listening
LISTEN_TIMEOUT = 3
PHRASE_TIME_LIMIT = 6

# Speech recognition
ENERGY_THRESHOLD = 250

# TTS
TTS_RATE = "-4%"
TTS_PITCH = "+0Hz"
TTS_VOLUME = "+0%"

TTS_RETRIES = 2


# ============================================================
# GLOBALS
# ============================================================

recognizer = sr.Recognizer()
microphone = None

recognizer.energy_threshold = ENERGY_THRESHOLD
recognizer.dynamic_energy_threshold = True

# Lower values make Hella stop listening sooner
recognizer.pause_threshold = 0.55
recognizer.phrase_threshold = 0.15
recognizer.non_speaking_duration = 0.25

# Prevent overly long silence waiting
recognizer.operation_timeout = 5


# ============================================================
# AUDIO
# ============================================================

audio_ready = False

try:
    pygame.mixer.init()
    audio_ready = True
except Exception:
    audio_ready = False


# ============================================================
# TTS CACHE
# ============================================================

CACHE_DIR = os.path.join(
    tempfile.gettempdir(),
    "hella_tts_cache"
)

os.makedirs(CACHE_DIR, exist_ok=True)


# ============================================================
# EDGE TTS
# ============================================================

async def generate_voice(text, filename):

    communicator = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate=TTS_RATE,
        pitch=TTS_PITCH,
        volume=TTS_VOLUME
    )

    await communicator.save(filename)


# ============================================================
# PLAY AUDIO
# ============================================================

def play_audio(filename):

    if not audio_ready:
        raise RuntimeError("Audio system unavailable")

    pygame.mixer.music.stop()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(30)

    try:
        pygame.mixer.music.unload()
    except Exception:
        pass


# ============================================================
# WINDOWS TTS FALLBACK
# ============================================================

def windows_fallback(text):

    if pyttsx3 is None:
        return False

    try:

        engine = pyttsx3.init()

        voices = engine.getProperty("voices")

        preferred = None

        for voice in voices:

            name = str(
                getattr(voice, "name", "")
            ).lower()

            voice_id = str(
                getattr(voice, "id", "")
            ).lower()

            if any(word in name or word in voice_id for word in (
                "zira",
                "female",
                "heera",
                "aarti",
                "india"
            )):

                preferred = voice.id
                break

        if preferred:
            engine.setProperty(
                "voice",
                preferred
            )

        engine.setProperty(
            "rate",
            180
        )

        engine.setProperty(
            "volume",
            1.0
        )

        engine.say(text)
        engine.runAndWait()
        engine.stop()

        return True

    except Exception:
        return False


# ============================================================
# SPEAK
# ============================================================

def speak(text):

    if not text:
        return

    print(f"\nHella: {text}")

    # Stable cache filename
    cache_key = hashlib.md5(
        f"{VOICE}|{TTS_RATE}|{text}".encode()
    ).hexdigest()

    filename = os.path.join(
        CACHE_DIR,
        cache_key + ".mp3"
    )

    # --------------------------------------------------------
    # CACHE
    # --------------------------------------------------------

    if os.path.exists(filename):

        try:
            play_audio(filename)
            return

        except Exception:
            pass

    # --------------------------------------------------------
    # EDGE TTS
    # --------------------------------------------------------

    for _ in range(TTS_RETRIES):

        try:

            asyncio.run(
                generate_voice(
                    text,
                    filename
                )
            )

            if (
                os.path.exists(filename)
                and os.path.getsize(filename) > 0
            ):

                play_audio(filename)
                return

        except Exception:
            continue

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    windows_fallback(text)


# ============================================================
# MICROPHONE INITIALIZATION
# ============================================================

def initialize_microphone():

    global microphone

    try:

        microphone = sr.Microphone(
            device_index=MICROPHONE_DEVICE_INDEX
        )

        print("\n🎤 Preparing microphone...")

        # Calibrate only ONCE
        with microphone as source:

            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.5
            )

        # Don't allow threshold to become too high
        if recognizer.energy_threshold > 600:
            recognizer.energy_threshold = 350

        print(
            f"🎤 Microphone ready "
            f"(threshold: {int(recognizer.energy_threshold)})"
        )

        return True

    except Exception as error:

        print(
            "\n❌ Microphone error:",
            error
        )

        return False


# ============================================================
# LISTEN
# ============================================================

def listen():

    if microphone is None:
        return ""

    try:

        print(
            "\n🎤 Listening...",
            end=" ",
            flush=True
        )

        with microphone as source:

            audio = recognizer.listen(
                source,
                timeout=LISTEN_TIMEOUT,
                phrase_time_limit=PHRASE_TIME_LIMIT
            )

        print(
            "🔄",
            end=" ",
            flush=True
        )

        try:

            command = recognizer.recognize_google(
                audio,
                language=LANGUAGE
            )

            command = command.lower().strip()

            if command:

                print(
                    f"You: {command}"
                )

                return command

        except sr.UnknownValueError:

            # Don't print a large error every time
            print(
                "..."
            )

        except sr.RequestError:

            print(
                "Internet/recognition problem."
            )

        return ""

    except sr.WaitTimeoutError:

        # Normal silence
        return ""

    except OSError:

        print(
            "\n❌ Microphone disconnected."
        )

        return ""

    except Exception as error:

        print(
            f"\n❌ Listening error: {error}"
        )

        return ""


# ============================================================
# TIME
# ============================================================

def tell_time():

    current_time = datetime.datetime.now().strftime(
        "%I:%M %p"
    )

    speak(
        f"The time is {current_time}."
    )


# ============================================================
# DATE
# ============================================================

def tell_date():

    current_date = datetime.datetime.now().strftime(
        "%A, %d %B %Y"
    )

    speak(
        f"Today is {current_date}."
    )


# ============================================================
# OPEN WEBSITE
# ============================================================

def open_website(url, name):

    webbrowser.open(url)

    speak(
        f"Opening {name}."
    )


# ============================================================
# WEBSITES
# ============================================================

def open_youtube():

    open_website(
        "https://www.youtube.com",
        "YouTube"
    )


def open_google():

    open_website(
        "https://www.google.com",
        "Google"
    )


def open_linkedin():

    open_website(
        "https://www.linkedin.com/feed/",
        "LinkedIn"
    )


def open_github():

    open_website(
        "https://github.com",
        "GitHub"
    )


def open_lms():

    open_website(
        "https://lms.codinggita.in/student",
        "your LMS"
    )


# ============================================================
# FAVOURITE SONG
# ============================================================

def play_favourite_song():

    speak(
        "Playing your favourite song."
    )

    webbrowser.open(
        "https://youtu.be/aroZ0SSNoEo"
    )


# ============================================================
# GOOGLE SEARCH
# ============================================================

def google_search(command):

    query = command

    search_words = [
        "search for",
        "search",
        "google"
    ]

    for word in search_words:

        if query.startswith(word):

            query = query[len(word):].strip()
            break

    if not query:

        speak(
            "What should I search for?"
        )

        return

    url = (
        "https://www.google.com/search?q="
        + urllib.parse.quote_plus(query)
    )

    webbrowser.open(url)

    speak(
        f"Searching for {query}."
    )


# ============================================================
# WIKIPEDIA
# ============================================================

def wikipedia_search(command):

    topic = command

    for word in (
        "wikipedia search",
        "search wikipedia",
        "wikipedia"
    ):

        if topic.startswith(word):

            topic = topic[len(word):].strip()
            break

    if not topic:

        speak(
            "What should I search for?"
        )

        return

    try:

        wikipedia.set_lang("en")

        result = wikipedia.summary(
            topic,
            sentences=2,
            auto_suggest=True
        )

        speak(result)

    except wikipedia.exceptions.DisambiguationError:

        speak(
            "Please be more specific."
        )

    except wikipedia.exceptions.PageError:

        speak(
            "I couldn't find that topic."
        )

    except Exception:

        speak(
            "Wikipedia is unavailable."
        )


# ============================================================
# WINDOWS APPLICATIONS
# ============================================================

def open_notepad():

    try:

        subprocess.Popen(
            ["notepad.exe"]
        )

        speak(
            "Opening Notepad."
        )

    except Exception:

        speak(
            "I couldn't open Notepad."
        )


def open_calculator():

    try:

        subprocess.Popen(
            ["calc.exe"]
        )

        speak(
            "Opening Calculator."
        )

    except Exception:

        speak(
            "I couldn't open Calculator."
        )


def open_vscode():

    try:

        subprocess.Popen(
            "code",
            shell=True
        )

        speak(
            "Opening Visual Studio Code."
        )

    except Exception:

        speak(
            "I couldn't open Visual Studio Code."
        )


# ============================================================
# INTRODUCTION
# ============================================================

def introduce():

    speak(
        "I am Hella, your personal AI assistant."
    )


# ============================================================
# STATUS
# ============================================================

def how_are_you():

    speak(
        "I am functioning perfectly, boss."
    )


# ============================================================
# HELP
# ============================================================

def show_help():

    speak(
        "I can open websites, search Google, "
        "search Wikipedia, tell time and date, "
        "open Notepad, Calculator and Visual Studio Code, "
        "play your favourite song, and open your LMS."
    )


# ============================================================
# PARTIAL COMMAND PROCESSING
# ============================================================

def process_command(command):

    if not command:
        return True

    command = command.lower().strip()

    # --------------------------------------------------------
    # EXIT
    # --------------------------------------------------------

    if (
        command.startswith("exit")
        or command.startswith("quit")
        or command.startswith("bye")
        or command.startswith("stop")
        or command.startswith("shutdown")
        or "goodbye" in command
    ):

        speak(
            "Goodbye boss."
        )

        return False

    # --------------------------------------------------------
    # TIME
    # --------------------------------------------------------

    if any(word in command for word in (
        "time",
        "what time",
        "tell time",
        "current time"
    )):

        tell_time()
        return True

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    if any(word in command for word in (
        "date",
        "what date",
        "today date",
        "today's date",
        "current date"
    )):

        tell_date()
        return True

    # --------------------------------------------------------
    # YOUTUBE
    # --------------------------------------------------------

    if any(word in command for word in (
        "youtube",
        "you tube",
        "open you",
        "open yo"
    )):

        open_youtube()
        return True

    # --------------------------------------------------------
    # GOOGLE
    # --------------------------------------------------------

    if any(word in command for word in (
        "google",
        "open goo",
        "open gog"
    )):

        open_google()
        return True

    # --------------------------------------------------------
    # LINKEDIN
    # --------------------------------------------------------

    if any(word in command for word in (
        "linkedin",
        "linked in",
        "open link",
        "open linked"
    )):

        open_linkedin()
        return True

    # --------------------------------------------------------
    # GITHUB
    # --------------------------------------------------------

    if any(word in command for word in (
        "github",
        "git hub",
        "open git"
    )):

        open_github()
        return True

    # --------------------------------------------------------
    # LMS / DASHBOARD
    # --------------------------------------------------------

    if any(word in command for word in (
        "lms",
        "open lm",
        "dashboard",
        "open dash",
        "my dashboard",
        "coding gita"
    )):

        open_lms()
        return True

    # --------------------------------------------------------
    # SONG
    # --------------------------------------------------------

    if any(word in command for word in (
        "favourite song",
        "favorite song",
        "play my song",
        "play song",
        "play my fav",
        "play my favourite",
        "play my favorite"
    )):

        play_favourite_song()
        return True

    # --------------------------------------------------------
    # GOOGLE SEARCH
    # --------------------------------------------------------

    if (
        command == "search"
        or command.startswith("search ")
        or command.startswith("search for ")
        or command.startswith("google search ")
    ):

        google_search(command)
        return True

    # --------------------------------------------------------
    # WIKIPEDIA
    # --------------------------------------------------------

    if (
        command == "wikipedia"
        or command.startswith("wikipedia ")
        or command.startswith("search wikipedia ")
    ):

        wikipedia_search(command)
        return True

    # --------------------------------------------------------
    # NOTEPAD
    # --------------------------------------------------------

    if any(word in command for word in (
        "notepad",
        "note pad",
        "open note",
        "open not"
    )):

        open_notepad()
        return True

    # --------------------------------------------------------
    # CALCULATOR
    # --------------------------------------------------------

    if any(word in command for word in (
        "calculator",
        "calc",
        "open cal"
    )):

        open_calculator()
        return True

    # --------------------------------------------------------
    # VS CODE
    # --------------------------------------------------------

    if any(word in command for word in (
        "vs code",
        "vscode",
        "visual studio",
        "open vs",
        "open visual"
    )):

        open_vscode()
        return True

    # --------------------------------------------------------
    # INTRODUCTION
    # --------------------------------------------------------

    if any(word in command for word in (
        "who are you",
        "who are",
        "what are you",
        "introduce yourself",
        "introduce"
    )):

        introduce()
        return True

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    if any(word in command for word in (
        "how are you",
        "how are"
    )):

        how_are_you()
        return True

    # --------------------------------------------------------
    # HELP
    # --------------------------------------------------------

    if (
        command == "help"
        or "what can you do" in command
        or command.startswith("help me")
    ):

        show_help()
        return True

    # --------------------------------------------------------
    # EXTRA COMMANDS
    # --------------------------------------------------------

    # Open browser
    if any(word in command for word in (
        "open browser",
        "browser"
    )):

        webbrowser.open(
            "https://www.google.com"
        )

        speak(
            "Opening the browser."
        )

        return True

    # Open Gmail
    if any(word in command for word in (
        "gmail",
        "open mail",
        "open gmail"
    )):

        open_website(
            "https://mail.google.com",
            "Gmail"
        )

        return True

    # Open ChatGPT
    if any(word in command for word in (
        "chatgpt",
        "chat gpt",
        "open chat"
    )):

        open_website(
            "https://chatgpt.com",
            "ChatGPT"
        )

        return True

    # Open Figma
    if any(word in command for word in (
        "figma",
        "open figma"
    )):

        open_website(
            "https://www.figma.com",
            "Figma"
        )

        return True

    # Open Instagram
    if any(word in command for word in (
        "instagram",
        "open instagram"
    )):

        open_website(
            "https://www.instagram.com",
            "Instagram"
        )

        return True

    # Open WhatsApp Web
    if any(word in command for word in (
        "whatsapp",
        "open whatsapp"
    )):

        open_website(
            "https://web.whatsapp.com",
            "WhatsApp"
        )

        return True

    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    speak(
        "I didn't catch that command."
    )

    return True


# ============================================================
# STARTUP
# ============================================================

def startup():

    hour = datetime.datetime.now().hour

    if hour < 12:

        greeting = "Good morning, boss."

    elif hour < 18:

        greeting = "Good afternoon, boss."

    else:

        greeting = "Good evening, boss."

    speak(greeting)

    speak(
        "I am Hella. How can I help you?"
    )


# ============================================================
# CLEANUP
# ============================================================

def cleanup():

    try:

        pygame.mixer.music.stop()
        pygame.mixer.quit()

    except Exception:
        pass


# ============================================================
# MICROPHONE DIAGNOSTICS
# ============================================================

def show_microphones():

    try:

        microphones = (
            sr.Microphone
            .list_microphone_names()
        )

        print(
            "\nAvailable microphones:\n"
        )

        for index, name in enumerate(
            microphones
        ):

            print(
                f"{index}: {name}"
            )

    except Exception as error:

        print(
            "Microphone error:",
            error
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n================================"
    )

    print(
        "       HELLA AI ASSISTANT"
    )

    print(
        "================================"
    )

    # --------------------------------------------------------
    # MICROPHONE
    # --------------------------------------------------------

    if not initialize_microphone():

        speak(
            "I couldn't access the microphone."
        )

        return

    # --------------------------------------------------------
    # STARTUP
    # --------------------------------------------------------

    startup()

    # --------------------------------------------------------
    # MAIN LOOP
    # --------------------------------------------------------

    while True:

        command = listen()

        if not command:
            continue

        if not process_command(command):
            break

    cleanup()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    if "--mics" in sys.argv:

        show_microphones()

    else:

        try:

            main()

        except KeyboardInterrupt:

            print(
                "\n\nHella stopped."
            )

            cleanup()