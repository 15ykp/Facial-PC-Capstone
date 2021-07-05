# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 11:57:23 2020

@author: Brandon Caron
"""

import speech_recognition as sr

# this is called from the background thread
def callback(recognizer, audio):
    # received audio data, now we'll recognize it using Google Speech Recognition
    # try:
    # for testing purposes, we're just using the default API key
    # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
    # instead of `r.recognize_google(audio)`
    voice_to_text = recognizer.recognize_sphinx(audio)
    print("Google Speech Recognition thinks you said: " + voice_to_text)
    
    text_split = voice_to_text.lower().split()

    if (('hey' in text_split or 'hi' in text_split or 'okay' in text_split) and ('computer' in text_split)):
        cue = True
    else:
        cue = False
    
    if cue:
        print("We now:\n\t1. Wait for voice input\n\t"+
              "2. Convert to string\n\t"+
              "3. Return string\n")
        
        m = sr.Microphone()
        with m as source:
            print("Now listening for input...")
            audio2 = r.listen(source)
            print("Done!")
        voice2_to_text = recognizer.recognize_google(audio2)
        print("your input is: " + voice2_to_text)    
            
    # except sr.UnknownValueError:
    #     pass
    #     #print("Google Speech Recognition could not understand audio")
    # except sr.RequestError as e:
    #     print("Could not request results from Google Speech Recognition service; {0}".format(e))

r = sr.Recognizer()
m = sr.Microphone()
with m as source:
    print('Calibrating...')
    r.adjust_for_ambient_noise(source)  # we only need to calibrate once, before we start listening
    print('Done!')
# start listening in the background (note that we don't have to do this inside a `with` statement)
stop_listening = r.listen_in_background(m, callback, 3)
print('Now listening')
# `stop_listening` is now a function that, when called, stops background listening

# do some unrelated computations
input("Press enter to end...")  

# calling this function requests that the background listener stop listening
print('Stoping listening...')
stop_listening(wait_for_stop=True)
print('Done!')

