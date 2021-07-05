import speech_recognition as sr
import threading
from facialpc import winhandler
import os
from word2number import w2n
import time
import wave
import pyaudio

GOOGLE_CLOUD_JSON_FILE_PATH = os.path.realpath(os.path.join(os.path.dirname(
    os.path.realpath(__file__)),'..\\data\\new.json'))
with open(GOOGLE_CLOUD_JSON_FILE_PATH) as f:
    JSON_KEY = f.read()

CUE_IN_PATH = os.path.realpath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),'..\\data\\cue_intro.wav'))

CUE_OUT_PATH = os.path.realpath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),'..\\data\\cue_outro.wav'))

SYNC_FILE = os.path.realpath(os.path.join(os.path.dirname(
    os.path.realpath(__file__)),'..\\data\\cloudsync.wav'))

def play_sound(filename):
    # Set chunk size of 1024 samples per data frame
    chunk = 35000  
    
    # Open the sound file 
    wf = wave.open(filename, 'rb')
    
    # Create an interface to PortAudio
    p = pyaudio.PyAudio()
    
    # Open a .Stream object to write the WAV file to
    # 'output = True' indicates that the sound will be played rather than recorded
    stream = p.open(format = p.get_format_from_width(wf.getsampwidth()),
                    channels = wf.getnchannels(),
                    rate = wf.getframerate(),
                    output = True)
    
    # Read data in chunks
    data = wf.readframes(chunk)
    
    stream.write(data)
    
    # Close and terminate the stream
    stream.close()
    p.terminate()

class Listener():
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.running = [False]
        self.output = []
        self.print_output = []
        self.cmds_output = []
        self.listener_thread = None
        self.handler_thread = None
        self.keyword = 'computer'
        self.Handler = winhandler.Handler()
        
        # we only need to calibrate once, before we start listening
        self.calibrate()
        self.listen_in_background()
        
    def calibrate(self):
        with self.microphone as source:
            print('Calibrating...')
            self.recognizer.adjust_for_ambient_noise(source)
            print('...Done!')
            
        print('Syncing with Google Cloud...')
        audio_file = SYNC_FILE
        
        with sr.AudioFile(audio_file) as source:
            audio = self.recognizer.record(source)
            
        try:
            self.recognizer.recognize_google_cloud(audio, JSON_KEY, 
                preferred_phrases=self.Handler.COMMANDS)
        except sr.UnknownValueError:
            # Speech Recognition could not understand audio
            pass
        else:
            print('...Done!')
        return
        
    def stop_listening(self,wait_for_stop=False):
        self.running=[False]
        if wait_for_stop:
            # Block until the background thread is done.
            self.listener_thread.join()
        return
    
    def listen_in_background(self, phrase_time_limit=3):
        """
        Spawns a thread to repeatedly record phrases from `source' (an 
        AudioSource instance) into an AudioData instance and call callback with
        that AudioData instance as soon as each phrase are detected.

        Returns a function object that, when called, requests that the 
        background listener thread stop. The background thread is a daemon and
        will not stop the program from exiting if there are no other non-daemon
        threads. The function accepts one parameter, `wait_for_stop`: if 
        truthy, the function will wait for the background listener to stop 
        before returning, otherwise it will return immediately and the 
        background listener thread might still be running for a second or two 
        afterwards. Additionally, if you are using a truthy value for 
        wait_for_stop, you must call the function from the same thread you 
        originally called `listen_in_background` from.

        Phrase recognition uses the exact same mechanism as 
        `recognizer_instance.listen(source)`. The `phrase_time_limit` parameter
        works in the same way as the `phrase_time_limit` parameter for 
        `recognizer_instance.listen(source)`, as well.

        The `callback` parameter is a function that should accept two 
        parameters - the ``recognizer_instance``, and an ``AudioData`` instance
        representing the captured audio. Note that ``callback`` function will
        be called from a non-main thread.
        """
        
        # Source must be an audio source
        assert isinstance(self.microphone, sr.AudioSource)
        self.running = [True]

        def threaded_listen():
            with self.microphone as s:
                while self.running[0]:
                    try:  
                        # listen for 1 second, then check again if the stop 
                        # function has been called
                        audio = self.recognizer.listen(
                            s, 1, phrase_time_limit)
                    except sr.WaitTimeoutError:  
                        # listening timed out, just try again
                        pass
                    else:
                        if self.running[0]: self.callback(audio,s)
            return

        listener_thread = threading.Thread(target=threaded_listen, 
                                           name='speech_recog')
        listener_thread.daemon = True
        listener_thread.start()
        self.listener_thread = listener_thread
        
        handler_thread = threading.Thread(target=self.decoder,
                                          name='speech_recog_handler')
        handler_thread.daemon = True
        handler_thread.start()
        self.handler_thread = handler_thread
        return
        
    def callback(self, audio, s):
        # We have received audio data and now we'll recognize it
        try:
            voice_to_text = self.recognizer.recognize_sphinx(
                audio, keyword_entries=[('hey',0.1),('hi',0.1),('okay',0.1),
                                        (self.keyword,1)])
            
            text_split = voice_to_text.lower().split()
            
            if (('hey' or 'hi' or 'okay' in text_split) and 
                (self.keyword in text_split)):
                play_sound(CUE_IN_PATH)
                audio_op = self.recognizer.listen(s, phrase_time_limit=20)
                play_sound(CUE_OUT_PATH)
                self.handle_audio(audio_op)
                
        except sr.UnknownValueError:
            # could not understand audio
            pass
        
    def handle_audio(self, audio):
        try:
            voice_to_text = self.recognizer.recognize_google_cloud(
                audio, JSON_KEY, preferred_phrases=self.Handler.COMMANDS)
        except sr.UnknownValueError:
            print("Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print("Could not request results from Google Cloud " +
                  "service; {0}".format(e))
        else:
            self.print_output.append(voice_to_text)
            self.output.append(voice_to_text)
            
    def pop(self):
        if len(self.output)>0:
            out = self.output[0]
            self.output.remove(out)
        else:
            out=None
        return out
    
    def decoder(self):
        while self.running[0]:
            if len(self.output)>0:
                cmd = False; i=0; prefix=None; modifiers=[]
                text = self.pop()
                text_split = text.split(' ')
                for msg in text_split:
                    if msg.lower() in self.Handler.COMMANDS:
                        cmd=msg.lower(); cmd_idx = i
                        break
                    i+=1
                    
                # Extract relevant modifiers and prefixes
                if bool(cmd):
                    send_to_handler = True
                    # Press command decoder
                    if cmd == 'press' or cmd == 'hold':
                        i=cmd_idx+1
                        for msg in text_split:
                            if msg.lower()=='click':
                                cmd = 'click'
                                break
                            elif msg.lower()=='hold':
                                cmd='hold'
                            elif (msg.lower() in self.Handler.KEY_LIST) and (
                                    msg.lower()!='space'):
                                modifiers.append(msg.lower())
                            elif msg.lower()=='control':
                                modifiers.append('ctrl')
                            elif msg.lower()=='back':
                                modifiers.append('backspace')
                            elif msg.lower()=='space':
                                if text_split[i-1]=='back':
                                    modifiers.append('backspace')
                                else:
                                    modifiers.append('space')
                            elif msg.lower()=='alternate':
                                modifiers.append('alt')
                            else:
                                try:
                                    num=w2n.word_to_num(msg.lower())
                                    modifiers.append(num)
                                except(ValueError):
                                    pass
                            i+=1
                                
                    # Click command decoder
                    if cmd == 'click':
                        if (cmd_idx-1>=0):
                            # look for prefix
                            if text_split[cmd_idx-1].lower()=='right':
                                prefix='right'
                            elif text_split[cmd_idx-1].lower()=='middle':
                                prefix='middle'
                                
                        # look for modifier
                        for mod in text_split:
                            if mod.lower() == 'hold':
                                modifiers.append(mod.lower())
                            elif mod.lower() == 'double':
                                modifiers.append(2)
                            else:
                                try:
                                    num=w2n.word_to_num(mod.lower())
                                    modifiers.append(num)
                                except(ValueError):
                                    pass
                            
                                
                    # Open and close commands decoder
                    elif cmd == 'open' or cmd == 'close':
                        msg = ' '.join(text_split[cmd_idx+1::])
                        modifiers.append(msg)
                    
                    # Type command decoder
                    elif cmd == 'type':
                        msg = ' '.join(text_split[cmd_idx+1::])
                        modifiers.append(msg)
                        
                    # Move command decoder
                    elif cmd == 'move':
                        pass
                    
                    # Release command decoder
                    elif cmd == 'release':
                        for msg in text_split:
                            if msg.lower()=='right' or msg.lower()=='left':
                                prefix=msg.lower()
                            elif msg.lower()=='click' or msg.lower()=='mouse':
                                modifiers.append('click')
                            elif msg.lower()=='control' or msg.lower()=='ctrl':
                                modifiers.append('ctrl')
                            elif msg.lower()=='delete':
                                modifiers.append('delete')
                            elif msg.lower()=='back':
                                modifiers.append('backspace')
                            elif msg.lower()=='space':
                                if text_split[i-1]=='back':
                                    pass
                                else:
                                    modifiers.append('space')
                            elif msg.lower()=='enter':
                                modifiers.append('enter')
                            elif msg.lower()=='alt' or msg.lower()=='alternate':
                                modifiers.append('alt')
                            elif msg.lower()=='escape':
                                modifiers.append('esc')
                            elif msg.lower()=='shift':
                                modifiers.append('shift')
                                
                    elif cmd == 'sensitivity' or cmd == 'dead':
                        send_to_handler = False
                        absolute = 0
                        prefix = 'both'
                        for mod in text_split:
                            for letter in mod:
                                if letter == '%':
                                    modifiers.append('percent')
                                    mod = mod[0:mod.index(letter)]
                                    
                            if mod.lower() == 'x' or mod.lower() == 'y':
                                prefix = mod.lower()
                                
                            elif (mod.lower() == 'percent' or 
                                  mod.lower() == 'decrease' or 
                                  mod.lower() == 'increase'):
                                modifiers.append(mod.lower())
                                
                            elif (mod.lower() == 'set') or (
                                    mod.lower() == 'to'):
                                absolute += 1
                                
                            else:
                                try:
                                    num=w2n.word_to_num(mod.lower())
                                    modifiers.append(num)
                                except(ValueError):
                                    pass
                                
                        if (absolute > 0) and ('percent' not in modifiers):
                            modifiers.append('absolute')
                                
                        self.cmds_output.append([cmd,prefix,modifiers])
                        
                    elif (cmd == 'start' or cmd == 'stop' or 
                          cmd == 'calibrate' or cmd == 'recalibrate' or
                          cmd == 'invert'):
                        send_to_handler = False
                        self.cmds_output.append([cmd,prefix,modifiers])
                        
                    if send_to_handler:
                        self.Handler.execute(cmd,prefix,modifiers)
                else:
                    self.print_output.append('No command found in string')
            else:
                time.sleep(1)
        return
        
        
        
        
        