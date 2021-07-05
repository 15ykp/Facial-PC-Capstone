import pyaudio
import speech_recognition as sr
import time

def play_sound(audio):
    # Set chunk size of 1024 samples per data frame
    chunk = 35000  
    
    # Create an interface to PortAudio
    p = pyaudio.PyAudio()
    
    # Open a .Stream object to write the WAV file to
    # 'output = True' indicates that the sound will be played rather than recorded
    stream = p.open(format = 8,
                    channels = 1,
                    rate = audio.sample_rate,
                    output = True)
    
    stream.write(audio.get_raw_data())
    
    # Close and terminate the stream
    stream.close()
    p.terminate()
    
microphone = sr.Microphone(device_index=(3))
recognizer = sr.Recognizer()
print('talk now')
with microphone as s:
    audio = recognizer.listen(s, 1, 10)
print('Will playback in 2 secs')
time.sleep(2)
play_sound(audio)