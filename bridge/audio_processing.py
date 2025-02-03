import speech_recognition as sr



recognizer = sr.Recognizer()

def capture_voice_input():
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
    return audio 

def convert_voice_to_text(audio):
    try:
        text = recognizer.recognize_whisper(audio, language="english")
        print("You said: " + text)
    except sr.UnknownValueError:
        text = ""
        print("Sorry, I didn't understand that.")
    except sr.RequestError as e:
        text = ""
        print("Error, {0}".format(e))
    return text 

def process_voice_commands(text):
    # we add a 0 at the end to tell the micro it was a voice command
    if "on" in text.lower():
        return b'255,255,255,0\n'
    if "off" in text.lower():
        return b'0,0,0,0\n'
    if "red" in text.lower():
        return b'255,0,0,0\n'
    if "green" in text.lower():
        return b'0,255,0,0\n'
    if "blue" in text.lower():
        return b'0,0,255,0\n'
    if "yellow" in text.lower():
        return b'255,255,0,0\n'
    if "orange" in text.lower():
        return b'255,128,0,0\n'
    if "purple" in text.lower():
        return b'127,0,255,0\n'
    if "pink" in text.lower():
        return b'255,0,127,0\n'