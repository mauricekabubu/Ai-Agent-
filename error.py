import sys
import pyttsx3 as ptx

engine = ptx.init()

def handle_exception(exc_type, exc_value, exc_traceback):
    engine.say("Maurice! shit your code crashed manh!")
    engine.runAndWait()
    
sys.excepthook = handle_exception

print("Running")
x = 5/0