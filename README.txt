============================================================
                  HELLA AI ASSISTANT
                    SETUP GUIDE
============================================================


1. PYTHON
------------------------------------------------------------

Use Python 3.11.

Check:

py --version

You should see:

Python 3.11.x


2. CREATE VIRTUAL ENVIRONMENT
------------------------------------------------------------

Open the Hella_AI folder in VS Code.

Open:

Terminal > New Terminal

Run:

py -3.11 -m venv venv


3. ACTIVATE VENV
------------------------------------------------------------

PowerShell:

.\venv\Scripts\Activate.ps1

You MUST see:

(venv)


4. INSTALL PACKAGES
------------------------------------------------------------

Run:

python -m pip install --upgrade pip

Then:

pip install -r requirements.txt


5. CHECK PACKAGES
------------------------------------------------------------

Run:

python -c "import edge_tts, pygame, speech_recognition, wikipedia, pyttsx3; print('ALL MODULES OK')"

Expected:

ALL MODULES OK


6. SELECT PYTHON IN VS CODE
------------------------------------------------------------

Press:

Ctrl + Shift + P

Search:

Python: Select Interpreter

Select:

.\venv\Scripts\python.exe


7. CHECK PYTHON
------------------------------------------------------------

Run:

python -c "import sys; print(sys.executable)"

It should show something like:

C:\Users\YourName\Desktop\Hella_AI\venv\Scripts\python.exe


8. CHECK MICROPHONES
------------------------------------------------------------

Run:

python jarvis.py --mics

Find your microphone.

By default Hella uses:

MICROPHONE_DEVICE_INDEX = None

This means Windows default microphone.


9. RUN HELLA
------------------------------------------------------------

Run:

python jarvis.py


10. TEST AARTI VOICE
------------------------------------------------------------

Run:

edge-tts --voice en-IN-AartiNeural --text "Hello boss, I am Hella." --write-media test_voice.mp3

If test_voice.mp3 is created, Edge TTS is working.


============================================================
                    HELLA COMMANDS
============================================================

What is the time?

What is the date?

Open YouTube

Open Google

Open LinkedIn

Open GitHub

Open LMS

Play my favourite song

Search Python tutorials

Wikipedia Python

Open Notepad

Open Calculator

Open VS Code

Who are you?

How are you?

What can you do?

Help

Bye

Goodbye

Shutdown


============================================================
                      VOICE
============================================================

Primary voice:

en-IN-AartiNeural

This is the Indian English female Edge TTS voice.

Edge TTS requires an internet connection.

If Edge TTS fails, Hella tries the Windows TTS fallback.


============================================================
                  IMPORTANT
============================================================

Do NOT run Hella from a ZIP file.

Do NOT run it from:

AppData\Local\Temp\...\zip...

Your project should be in a permanent folder.

Example:

C:\Users\YourName\Desktop\Hella_AI


The final project should look like:

Hella_AI
│
├── venv
│
├── jarvis.py
├── requirements.txt
└── README.txt


Every time you reopen the project:

1. Open Hella_AI in VS Code.
2. Open Terminal.
3. Activate venv:

   .\venv\Scripts\Activate.ps1

4. Run:

   python jarvis.py