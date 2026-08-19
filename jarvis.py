import asyncio
import datetime
import os
import subprocess
import sys
import tempfile
import threading
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

# None = Windows default microphone
MICROPHONE_DEVICE_INDEX = None

# Faster listening
LISTEN_TIMEOUT = 4
PHRASE_TIME_LIMIT = 7

# Voice
TTS_RATE = "-4%"
TTS_PITCH = "+0Hz"
TTS_VOLUME = "+0%"

# Number of Edge TTS attempts
TTS_RETRIES = 2


# ============================================================
# GLOBAL OBJECTS
# ============================================================

recognizer = sr.Recognizer()

recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.6
recognizer.phrase_threshold = 0.2
recognizer.non_speaking_duration = 0.3

audio_ready = False

try:
    pygame.mixer.init()
    audio_ready = True
except Exception:
    audio_ready = False


# ============================================================
# CACHE DIRECTORY
# ============================================================

CACHE_DIR = os.path.join(
    tempfile.gettempdir(),
    "hella_tts_cache"
)

os.makedirs(CACHE_DIR, exist_ok=True)


# ============================================================
# TTS
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


def play_audio(filename):

    if not audio_ready:
        raise RuntimeError("Audio unavailable")

    pygame.mixer.music.stop()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(30)

    try:
        pygame.mixer.music.unload()
    except Exception:
        pass


def windows_fallback(text):

    if pyttsx3 is None:
        return False

    try:

        engine = pyttsx3.init()

        voices = engine.getProperty("voices")

        for voice in voices:

            name = str(
                getattr(voice, "name", "")
            ).lower()

            voice_id = str(
                getattr(voice, "id", "")
            ).lower()

            if (
                "zira" in name
                or "female" in name
                or "heera" in name
                or "aarti" in name
                or "india" in name
                or "zira" in voice_id
                or "heera" in voice_id
            ):
                engine.setProperty(
                    "voice",
                    voice.id
                )
                break

        engine.setProperty("rate", 180)
        engine.setProperty("volume", 1.0)

        engine.say(text)
        engine.runAndWait()
        engine.stop()

        return True

    except Exception:
        return False


def speak(text):

    if not text:
        return

    # Only one short console line
    print(f"Hella: {text}")

    # Cache filename based on text
    safe_name = str(
        abs(hash(
            f"{VOICE}|{TTS_RATE}|{text}"
        ))
    )

    filename = os.path.join(
        CACHE_DIR,
        safe_name + ".mp3"
    )

    # --------------------------------------------------------
    # USE CACHED VOICE
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
            pass

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    windows_fallback(text)


# ============================================================
# MICROPHONE
# ============================================================

microphone = None


def initialize_microphone():

    global microphone

    try:

        microphone = sr.Microphone(
            device_index=MICROPHONE_DEVICE_INDEX
        )

        # IMPORTANT:
        # Do this ONLY ONCE at startup.
        with microphone as source:

            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.2
            )

        return True

    except Exception as error:

        print("Microphone error:", error)

        return False


# ============================================================
# LISTEN
# ============================================================

def listen():

    if microphone is None:
        return ""

    try:

        with microphone as source:

            audio = recognizer.listen(
                source,
                timeout=LISTEN_TIMEOUT,
                phrase_time_limit=PHRASE_TIME_LIMIT
            )

        try:

            command = recognizer.recognize_google(
                audio,
                language=LANGUAGE
            )

            return command.lower().strip()

        except sr.UnknownValueError:

            return ""

        except sr.RequestError:

            speak(
                "Speech recognition is unavailable."
            )

            return ""

    except sr.WaitTimeoutError:

        return ""

    except OSError:

        return ""

    except Exception:

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
    speak(f"Opening {name}.")


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
        "https://youtu.be/aroZ0SSNoEo?si=LtnwYpomM5Q-A_rl"
    )


# ============================================================
# GOOGLE SEARCH
# ============================================================

def google_search(command):

    query = command.replace(
        "search",
        "",
        1
    ).strip()

    if not query:

        speak("What should I search for?")
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

    topic = command.replace(
        "wikipedia",
        "",
        1
    ).strip()

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

        speak("Opening Notepad.")

    except Exception:

        speak("I couldn't open Notepad.")


def open_calculator():

    try:

        subprocess.Popen(
            ["calc.exe"]
        )

        speak("Opening Calculator.")

    except Exception:

        speak("I couldn't open Calculator.")


def open_vscode():

    try:

        subprocess.Popen(
            ["code"],
            shell=True
        )

        speak("Opening Visual Studio Code.")

    except Exception:

        speak("I couldn't open Visual Studio Code.")


# ============================================================
# INTRODUCTION
# ============================================================

def introduce():

    speak(
        "I am Hella your personal AI assistant."
    )


# ============================================================
# STATUS
# ============================================================

def how_are_you():

    speak(
        "I am functioning perfectly boss."
    )


# ============================================================
# HELP
# ============================================================

def show_help():

    speak(
        "I can open websites, search Google, "
        "search Wikipedia, tell time and date, "
        "open Windows apps, and play your song."
    )


# ============================================================
# COMMAND PROCESSOR
# ============================================================

def process_command(command):

    if not command:
        return True

    # --------------------------------------------------------
    # EXIT
    # --------------------------------------------------------

    if (
        command in (
            "exit",
            "bye",
            "quit",
            "stop",
            "shutdown"
        )
        or "goodbye" in command
    ):

        speak(
            "Goodbye boss."
        )

        return False

    # --------------------------------------------------------
    # TIME
    # --------------------------------------------------------

    if (
        command == "time"
        or "what is the time" in command
        or "what's the time" in command
        or "tell me the time" in command
    ):

        tell_time()
        return True

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    if (
        command == "date"
        or "what is the date" in command
        or "what's the date" in command
        or "today's date" in command
        or "tell me the date" in command
    ):

        tell_date()
        return True

    # --------------------------------------------------------
    # YOUTUBE
    # --------------------------------------------------------

    if (
        command == "youtube"
        or "open youtube" in command
    ):

        open_youtube()
        return True

    # --------------------------------------------------------
    # GOOGLE
    # --------------------------------------------------------

    if (
        command == "google"
        or "open google" in command
    ):

        open_google()
        return True

    # --------------------------------------------------------
    # LINKEDIN
    # --------------------------------------------------------

    if (
        "open linkedin" in command
        or "open linked in" in command
    ):

        open_linkedin()
        return True

    # --------------------------------------------------------
    # GITHUB
    # --------------------------------------------------------

    if (
        command == "github"
        or "open github" in command
    ):

        open_github()
        return True

    # --------------------------------------------------------
    # LMS
    # --------------------------------------------------------

    if (
        "open lms" in command
        or "open my lms" in command
        or "open dashboard" in command
    ):

        open_lms()
        return True

    # --------------------------------------------------------
    # SONG
    # --------------------------------------------------------

    if (
        "play my favourite song" in command
        or "play my favorite song" in command
        or "play my song" in command
    ):

        play_favourite_song()
        return True

    # --------------------------------------------------------
    # GOOGLE SEARCH
    # --------------------------------------------------------

    if command == "search":

        speak(
            "What should I search for?"
        )

        return True

    if command.startswith("search "):

        google_search(command)

        return True

    # --------------------------------------------------------
    # WIKIPEDIA
    # --------------------------------------------------------

    if command == "wikipedia":

        speak(
            "What should I search for?"
        )

        return True

    if command.startswith("wikipedia "):

        wikipedia_search(command)

        return True

    # --------------------------------------------------------
    # NOTEPAD
    # --------------------------------------------------------

    if (
        "open notepad" in command
        or "open note pad" in command
    ):

        open_notepad()
        return True

    # --------------------------------------------------------
    # CALCULATOR
    # --------------------------------------------------------

    if "open calculator" in command:

        open_calculator()
        return True

    # --------------------------------------------------------
    # VS CODE
    # --------------------------------------------------------

    if (
        "open vs code" in command
        or "open vscode" in command
        or "open visual studio code" in command
    ):

        open_vscode()
        return True

    # --------------------------------------------------------
    # INTRODUCTION
    # --------------------------------------------------------

    if (
        "introduce yourself" in command
        or "who are you" in command
        or "what are you" in command
    ):

        introduce()
        return True

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    if "how are you" in command:

        how_are_you()
        return True

    # --------------------------------------------------------
    # HELP
    # --------------------------------------------------------

    if (
        command == "help"
        or "what can you do" in command
    ):

        show_help()
        return True

    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    speak(
        "I don't know that command yet."
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
        "I am Hella. How can I help?"
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
# MAIN
# ============================================================

def main():

    # Initialize microphone ONCE
    if not initialize_microphone():

        speak(
            "I couldn't access the microphone."
        )

        return

    startup()

    while True:

        command = listen()

        if command:

            if not process_command(command):
                break

    cleanup()


# ============================================================
# MICROPHONE DIAGNOSTICS
# ============================================================

def show_microphones():

    try:

        microphones = (
            sr.Microphone
            .list_microphone_names()
        )

        print("\nAvailable microphones:\n")

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
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    if "--mics" in sys.argv:

        show_microphones()

    else:

        try:

            main()

        except KeyboardInterrupt:

            cleanup()