import cv2
import pyautogui
import os
import copy
import tensorflow as tf
import numpy as np

pyautogui.FAILSAFE=False

FACE_CLASSIFIER_PATH = os.path.realpath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    '..\\data\\haarcascade_frontalface_default.xml'))

EYE_CLASSIFIER_PATH = os.path.realpath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    '..\\data\\haarcascade_eye.xml'))

EYE_MODEL_PATH = os.path.realpath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    '..\\data\\saved_model\\'))

class Watcher():
    
    def __init__(self, x_sens=50, y_sens=50):
        # Initalize settings
        self.sens_x = x_sens
        self.sens_y = y_sens
        self.scale_factor = 1.14
        self.min_neighbours = 5
        self.dead_x = 35
        self.dead_y = 20
        self.move_time = 0.1
        self.flipped = 1
        self.start = 0
        
        # Declare face properties
        self.limit_x_left = 0
        self.limit_x_right = 1
        self.limit_y_up = 0
        self.limit_y_down = 1
        self.center_x = 0
        self.center_y = 0
        self.cap = cv2.VideoCapture(0)
        self.face = []
        
        # Declare eye properties
        self.framed_eyes = [[-1,-1,-1,-1]]*2
        self.prev_eyes = [[-1,-1,-1,-1]]*2
        self.left_closed_count = 0
        self.right_closed_count = 0
        self.right_new = 0
        self.left_new = 0
        self.eye_min_count = 0
        self.eye_max_count = 10
        
        # Declare other properties
        self.img = self.cap.read()
        self.img_gray = []
        self.img_draw = copy.copy(self.img)
        self.roi_colour = []
        self.roi_gray = []
        self.framecount = 0
        
        # Load the classifiers and model
        self.face_cascade = cv2.CascadeClassifier(FACE_CLASSIFIER_PATH)
        self.eye_cascade = cv2.CascadeClassifier(EYE_CLASSIFIER_PATH)
        self.eye_model = tf.keras.models.load_model(EYE_MODEL_PATH)
        
        # Detect initial face
        while len(self.face)==0:
            self.detect_face()
        
        self.calibrate()
        return
        
    def detect_face(self):
        if not self.cap:
            self.cap = cv2.VideoCapture(0)
        self.framecount += 1
        # Read the frame
        _, img1 = self.cap.read()
        
        if self.flipped:
            self.img = cv2.flip(img1, 1)
        else:
            self.img = img1
        
        # Convert to grayscale
        self.img_gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        # Detect the faces
        faces = self.face_cascade.detectMultiScale(self.img_gray,
                                                   self.scale_factor,
                                                   self.min_neighbours)
        if len(faces) > 0:
            face_gap = 0
            #prev_face = copy.copy(self.face)
            for face in faces:
                #if len(prev_face)>0:
                if (face[2]*face[3] > face_gap): #and (
                        #(face[2]*face[3]) > 
                        #(prev_face[2]*prev_face[3] - 625)):
                    face_gap = face[2]*face[3]
                    self.face = face
                        
                # elif (face[2]*face[3] > face_gap):
                #     face_gap = face[2]*face[3]
                #     self.face = face
            
            # if len(self.face)>0 and len(prev_face)>0:
            #     if (self.face == prev_face).all():
            #         self.face = []
                    
            # if len(self.face)>0:
            (x, y, w, h) = self.face
            self.center_x = x+w//2
            self.center_y = y+h//2
            self.img_draw = copy.copy(self.img)
            self.roi_colour = self.img[y:y+h, x:x+w]
            self.roi_gray = self.img_gray[y:y+h, x:x+w]
            self.draw_face_rectangle()
            self.draw_dead_rectangle()
            self.draw_eye_rectangles()
            
        else:
            self.face = []
        return
            
    def detect_eyes(self):
        self.right_new = 0; self.left_new = 0;
        eyes = self.eye_cascade.detectMultiScale(self.roi_gray, 1.05, 9)
        newX, newY = self.roi_gray.shape
        for (ex,ey,ew,eh) in eyes:
            #Eye detection filtration
            if ex == -1 or ey == -1:
                pass
            elif((ey+eh) < (3*newY/5)):
                if(ew < 35 or eh < 35):
                    # Too small
                    pass
                
                elif(ew > 80 or eh > 80):
                    # Too big
                    pass
                    
                else:
                    if (ex+ew//2 > newX//2): 
                        #right eye
                        #frame and resize the image
                        ex, ey, ew, eh = self.frame_eye(ex,ey,ew,eh)
                        # new image of eye
                        self.framed_eyes[1] = self.roi_gray[ey:ey+eh, ex:ex+ew]
                        # keep track of last eye detected
                        self.prev_eyes[1] = (ex,ey,ew,eh)
                        self.right_new = 1
                    else:
                        #left eye
                        #frame and resize the image
                        ex, ey, ew, eh = self.frame_eye(ex,ey,ew,eh)
                        # new image of eye
                        self.framed_eyes[0] = self.roi_gray[ey:ey+eh, ex:ex+ew]
                        # keep track of last eye detected
                        self.prev_eyes[0] = (ex,ey,ew,eh)
                        self.left_new = 1
                      
    def check_eyes(self):
        for f in range(2):
            # update eye images with prev_eyes coordinates. This keeps the
            # image of the closed eye if it is not detected.
            ex = self.prev_eyes[f][0]
            ey = self.prev_eyes[f][1]
            ew = self.prev_eyes[f][2]
            eh = self.prev_eyes[f][3]
            self.framed_eyes[f] = self.roi_gray[ey:ey+eh, ex:ex+ew]
            
        #reformat picture arrays for neural network input            
        left_eye_array = np.asarray(self.framed_eyes[0])
        left_eye_array = (np.expand_dims(left_eye_array,0))
        left_eye_array = (np.expand_dims(left_eye_array,3))
        
        #predict status of left eye
        if left_eye_array.shape[1::] == (69,69,1):
            left_eye = self.eye_model.predict([left_eye_array])
            left_eye_pred = np.argmax(left_eye[0])
        else:
            # left_eye_array formating failed
            left_eye_pred = -1
        
        #reformat picture arrays for neural network input   
        right_eye_array = np.asarray(self.framed_eyes[1])
        right_eye_array = (np.expand_dims(right_eye_array,0))
        right_eye_array = (np.expand_dims(right_eye_array,3))
        
        #predict status of right eye
        if right_eye_array.shape[1::] == (69,69,1):
            right_eye = self.eye_model.predict([right_eye_array])
            right_eye_pred = np.argmax(right_eye[0])
        else:
            # right_eye_array formating failed
            right_eye_pred = -1
        
        # print(self.left_closed_count, self.right_closed_count)
        # Check left eye
        if(left_eye_pred == 0):
            # left eye closed
            self.left_closed_count += 1
        elif (left_eye_pred == -1):
            pass
        else:
            # left eye open
            self.left_closed_count = 0
            
        # Check right eye
        if(right_eye_pred == 0):
            # right eye closed
            self.right_closed_count += 1
        elif (right_eye_pred == -1):
            pass
        else:
            # right eye open
            self.right_closed_count = 0
        
        return
    
    def frame_eye(self, x, y, w, h): 
        #Function used to resize eye image to match neural network input size,
        # as well as center the eye in the resized image.
        xmarg = (69 - w)//2
        ymarg = (69 - h)//2
        newx = x - xmarg
        newy = y - ymarg
        neww = 69
        newh = 69
        return(newx, newy, neww, newh)
    
    def calibrate(self):
        if len(self.face) > 0:
            (x, y, w, h) = self.face
            self.center_x = x+w//2
            self.center_y = y+h//2
            self.limit_x_left = self.center_x - self.dead_x
            self.limit_x_right = self.center_x + self.dead_x
            self.limit_y_up = self.center_y - self.dead_y
            self.limit_y_down = self.center_y + self.dead_y
        else:
            # Cannot calibrate, no face was detected
            pass
        return
            
    def move_mouse(self):
        dist_x_left = (abs(self.center_x-self.limit_x_left)*self.sens_x*0.05)
        dist_x_right = (abs(self.center_x-self.limit_x_right)*self.sens_x*0.05)
        dist_y_up = (abs(self.center_y-self.limit_y_up)*self.sens_y*0.1)
        dist_y_down = (abs(self.center_y-self.limit_y_down)*self.sens_y*0.1)
        
        if (self.center_x > self.limit_x_right) and (
                self.center_y > self.limit_y_down):
            pyautogui.move(int(dist_x_right), int(dist_y_down), 
                            self.move_time)
        
        elif (self.center_x > self.limit_x_right) and (
                self.center_y < self.limit_y_up):
            pyautogui.move(int(dist_x_right), -1*int(dist_y_up), 
                            self.move_time)
        
        elif (self.center_x < self.limit_x_left) and (
                self.center_y > self.limit_y_down):
            pyautogui.move(-1*int(dist_x_left), int(dist_y_down), 
                            self.move_time)
        
        elif (self.center_x < self.limit_x_left) and (
                self.center_y < self.limit_y_up):
            pyautogui.move(-1*int(dist_x_left), -1*int(dist_y_up), 
                            self.move_time)
        
        elif self.center_x > self.limit_x_right:
            pyautogui.move(int(dist_x_right), 0, self.move_time)
            
        elif self.center_x < self.limit_x_left:
            pyautogui.move(-1*int(dist_x_left), 0, self.move_time)
            
        elif self.center_y > self.limit_y_down:
            pyautogui.move(0, int(dist_y_down), self.move_time)
        
        elif self.center_y < self.limit_y_up:
            pyautogui.move(0, -1*int(dist_y_up), self.move_time)
        return
            
    def click_mouse(self):
        if self.face_in_dead():
            if(self.left_closed_count >= self.eye_max_count) and (
                    self.right_closed_count <= self.eye_min_count):
                # Left click
                pyautogui.click(button='left')
                self.left_closed_count = 0
                
            elif(self.right_closed_count >= self.eye_max_count) and (
                    self.left_closed_count <= self.eye_min_count):
                # Right Click
                pyautogui.click(button='right')
                self.right_closed_count = 0
        else:
            self.right_closed_count = 0
            self.left_closed_count = 0
        return
    
    def draw_face_rectangle(self):
        if len(self.face)>0:
            (x, y, w, h) = self.face
            cv2.rectangle(self.img_draw, (x, y), (x+w, y+h), 
                          (255, 0, 0), 2)
        else:
            # Cannot draw, no face was detected
            pass
        return
            
    def draw_dead_rectangle(self):
        cv2.rectangle(self.img_draw, (self.limit_x_left, self.limit_y_up),
                      (self.limit_x_right, self.limit_y_down),
                      (0, 0, 255), 2)
        return
    
    def draw_eye_rectangles(self):
        x, y, w, h = self.face
        
        # draw left eye
        if self.prev_eyes[0][0] == -1:
            pass
        else:
            ex,ey,ew,eh = self.prev_eyes[0]
            cv2.rectangle(self.img_draw,(ex+x,ey+y),
                          (x+ex+ew,y+ey+eh),(32,165,218),2) 
        
        # draw right eye
        if self.prev_eyes[1][0]==-1:
            pass
        else:
            ex,ey,ew,eh = self.prev_eyes[1]
            cv2.rectangle(self.img_draw,(ex+x,ey+y),
                          (x+ex+ew,y+ey+eh),(0,255,0),2) 
        return
    
    def set_sens_x(self, val):
        self.sens_x = int(val)
        return
    
    def set_sens_y(self, val):
        self.sens_y = int(val)
        return
    
    def set_dead_x(self, val):
        old_dead = self.dead_x
        self.dead_x = int(val)
        diff = self.dead_x - old_dead
        self.limit_x_left = self.limit_x_left - diff
        self.limit_x_right = self.limit_x_right + diff
        return
    
    def set_dead_y(self, val):
        old_dead = self.dead_y
        self.dead_y = int(val)
        diff = self.dead_y - old_dead
        self.limit_y_up = self.limit_y_up - diff
        self.limit_y_down = self.limit_y_down + diff
        return
    
    def flip_cam(self):
        if self.flipped == 1:
            self.flipped = 0
        else:
            self.flipped =1
            
    def set_move_time(self, val):
        self.move_time = float(val)
        return
    
    def toggle_running(self):
        if self.start == 1:
            self.start = 0
        else:
            self.start = 1
            
    def face_in_dead(self):
        return ((self.center_x <= self.limit_x_right) and 
                (self.center_x >= self.limit_x_left) and
                (self.center_y >= self.limit_y_up) and
                (self.center_y <= self.limit_y_down))