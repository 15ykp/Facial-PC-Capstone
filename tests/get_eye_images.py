# -*- coding: utf-8 -*-
"""
Created on Mon Mar 29 17:07:42 2021

@author: Brandon Caron
"""

import cv2
import os
import sys
up1 = os.path.abspath('..')
if up1 not in sys.path: sys.path.insert(0, up1)
from facialpc import facialrecog
import time
from facialpc import speechrecog

watcher = facialrecog.Watcher()

while watcher.limit_x_left == 0:
    watcher.detect_face()
    watcher.calibrate()
        
while watcher.prev_eyes[0] == 1 or watcher.prev_eyes[1] == 1:
    watcher.detect_face()
    watcher.calibrate()
    watcher.detect_eyes()
    
folder = r'C:\Users\Brandon Caron\Pictures\ClosedEyes'
print('here')
time.sleep(2)
i=0
while i in range(600):
    print(i)
    watcher.detect_face()
    if len(watcher.face) > 0:
        watcher.detect_eyes()
        if True:
            f=1
            # update eye images with prev_eyes coordinates. This keeps the
            # image of the closed eye if it is not detected.
            ex = watcher.prev_eyes[f][0]
            ey = watcher.prev_eyes[f][1]
            ew = watcher.prev_eyes[f][2]
            eh = watcher.prev_eyes[f][3]
            watcher.framed_eyes[f] = watcher.roi_gray[ey:ey+eh, ex:ex+ew]
                
            if (watcher.frame_eyes[f].shape == (69,69)):
                # left_path = os.path.join(folder, 'left_eye_' + str(i) + '.png')
                # cv2.imwrite(left_path, watcher.framed_eyes[0])
                
                right_path = os.path.join(folder, 'right_eye_' + str(i) + '.png')
                cv2.imwrite(right_path, watcher.framed_eyes[1])
                
                i+=1
                time.sleep(0.025)
            
watcher.cap.release()
speechrecog.play_sound(speechrecog.CUE_IN_PATH)
            
            
        