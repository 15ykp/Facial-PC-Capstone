from facialpc import speechrecog
from facialpc import facialrecog
from facialpc import guihandler
        
if __name__ == '__main__':
    listener = speechrecog.Listener()
    watcher = facialrecog.Watcher()
    app = guihandler.App(listener, watcher)
    
    while watcher.limit_x_left == 0:
        watcher.detect_face()
        watcher.calibrate()
        
    while watcher.prev_eyes[0] == 1 or watcher.prev_eyes[1] == 1:
        watcher.detect_face()
        watcher.calibrate()
        watcher.detect_eyes()
        
    while True:
        # Read the frame
        watcher.detect_face()
        if len(watcher.face) > 0:
            watcher.detect_eyes()
            watcher.check_eyes()
            if watcher.start:
                watcher.move_mouse()
                watcher.click_mouse()
            
        if not app.isAlive():
            break

    # Release the VideoCapture object
    watcher.cap.release()
    # Stop the listener
    listener.stop_listening()