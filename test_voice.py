import pyttsx3

engine = pyttsx3.init()
engine.setProperty("rate", 140)
engine.setProperty("volume", 1.0)

engine.say("bye")
engine.runAndWait()

print("Test completed.")