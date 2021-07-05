import tkinter as tk
from tkinter import scrolledtext as st
from PIL import Image, ImageTk
import threading
import cv2
import copy

class App(threading.Thread):
    def __init__(self, listener, watcher):
        threading.Thread.__init__(self)
        self.watcher=watcher
        self.listener = listener
        self.text_buffer = 1e6
        self.start()
        
    def callback(self):
        self.root.quit()
        
    def after(self):
        # Check listener outputs
        if len(self.listener.cmds_output) > 0:
            data = self.listener.cmds_output[0]
            self.execute(data)
            self.listener.cmds_output.remove(data)
            
        # Display image in Canvas
        img = cv2.cvtColor(self.watcher.img_draw, cv2.COLOR_BGR2RGB)
        self.tkimgs.append(ImageTk.PhotoImage(master=self.frm_nw, 
                                              image=Image.fromarray(img)))
        self.cvs_face.itemconfig(self.cvs_img, 
                                 image=self.tkimgs[-1])
        self.tkimgs.remove(self.tkimgs[0])
        
        # Set scales
        self.sens_x_scale.set(self.watcher.sens_x)
        self.sens_y_scale.set(self.watcher.sens_y)
        self.dead_x_scale.set(self.watcher.dead_x)
        self.dead_y_scale.set(self.watcher.dead_y)
        
        # Check Inv Camera Button
        inv = self.inv_cam_var.get()
        if inv!=self.watcher.flipped:
            self.watcher.flip_cam()
        
        # Check for print statements
        if len(self.listener.print_output)>0:
            outputs = copy.copy(self.listener.print_output)
            self.scroll_text.configure(state='normal')
            for output in outputs:
                self.scroll_text.insert('insert',output + '\n')
                self.listener.print_output.remove(output)
            self.scroll_text.configure(state='disabled')
            self.scroll_text.yview_moveto(1)
        
        # Reschedule after functions
        self.root.after(100, self.after)
        
    def execute(self, data):
        cmd,prefix,modifiers = data
        
        if cmd == 'sensitivity' or cmd == 'dead':
            scale = ''; direction = 'increase'
            for mod in modifiers:
                if mod == 'percent':
                    scale = mod
                elif mod == 'absolute':
                    scale = mod
                elif mod == 'decrease' or mod == 'increase':
                    direction = mod
                else:
                    try:
                        num=int(mod)
                        val=num
                    except(ValueError):
                        pass
                
            if scale == 'percent':
                if cmd == 'sensitivity':
                    change_x = int(self.watcher.sens_x*val*0.01)
                    change_y = int(self.watcher.sens_y*val*0.01)
                else:
                    change_x = int(self.watcher.dead_x*val*0.01)
                    change_y = int(self.watcher.dead_y*val*0.01)
                    
            elif scale == 'absolute':
                change_x = val - self.watcher.sens_x
                change_y = val - self.watcher.sens_y
            else:
                change_x = val
                change_y = val
                
            if direction == 'decrease':
                change_x = change_x * -1
                change_y = change_y * -1
                
            if cmd == 'sensitivity':
                new_x = self.watcher.sens_x + change_x
                new_y = self.watcher.sens_y + change_y
            else:
                new_x = self.watcher.dead_x + change_x
                new_y = self.watcher.dead_y + change_y
            
            if new_x > 100:
                new_x = 100
            elif new_x < 1:
                new_x = 1
                
            if new_y > 100:
                new_y = 100
            elif new_y < 1:
                new_y = 1
                
            if cmd == 'sensitivity':
                if prefix == 'x':
                    self.watcher.sens_x = new_x
                elif prefix == 'y':
                    self.watcher.sens_y = new_y
                else:
                    self.watcher.sens_x = new_x
                    self.watcher.sens_y = new_y
            else:
                if prefix == 'x':
                    self.watcher.dead_x = new_x
                elif prefix == 'y':
                    self.watcher.dead_y = new_y
                else:
                    self.watcher.dead_x = new_x
                    self.watcher.dead_y = new_y
            
        elif cmd == 'start':
            self.start_running()
            
        elif cmd == 'stop':
            self.stop_running()
            
        elif cmd == 'calibrate' or cmd == 'recalibrate':
            self.watcher.calibrate()
            
        elif cmd == 'invert':
            inv = self.inv_cam_var.get()
            self.inv_cam_var.set((inv+1)%2)
        
    def start_running(self):
        self.watcher.start = 1
        self.on_bttn.configure(state = 'disabled')
        self.off_bttn.configure(state = 'normal')
        
    def stop_running(self):
        self.watcher.start = 0
        self.on_bttn.configure(state = 'normal')
        self.off_bttn.configure(state = 'disabled')
        
        
    def run(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.callback)

        # Initialize Frames
        self.frm_nw = tk.Frame(self.root)
        self.frm_sw = tk.Frame(self.root)
        self.frm_ne = tk.Frame(self.root, bd = 5, relief = 'sunken')
        self.frm_se = tk.Frame(self.root)
        self.frm_nw.grid(row=1, column=1)
        self.frm_sw.grid(row=2, column=1)
        self.frm_ne.grid(row=1, column=2)
        self.frm_se.grid(row=2, column=2)
        
        # Setup NW frame
        # Create Canvas to display image
        self.cvs_face = tk.Canvas(self.frm_nw)
        self.cvs_face.pack()
        img = self.watcher.img_draw
        self.tkimgs = [ImageTk.PhotoImage(master=self.frm_nw, 
                                   image=Image.fromarray(img))]
        self.cvs_img = self.cvs_face.create_image(0,0, 
                                                  anchor="nw", 
                                                  image=self.tkimgs[0])
        
        # Setup SW frame
        # 1. Sensitivity settings
        self.sens_x_scale = tk.Scale(self.frm_sw, 
                                     from_ = 1, to = 100, 
                                     orient = 'horizontal',
                                     showvalue = 1,
                                     command = self.watcher.set_sens_x,
                                     length = 300)
        self.sens_y_scale = tk.Scale(self.frm_sw, 
                                     from_=1, to=100, 
                                     orient='horizontal',
                                     showvalue = 1,
                                     command = self.watcher.set_sens_y,
                                     length = 300,)
        self.sens_x_scale.set(self.watcher.sens_x)
        self.sens_y_scale.set(self.watcher.sens_y)
        self.sens_x_label = tk.Label(self.frm_sw, text = 'X-Sensitivity',
                                     anchor = 'se')
        self.sens_y_label = tk.Label(self.frm_sw, text = 'Y-Sensitivity',
                                     anchor = 'se')
        
        # 2. Deadzone settings
        self.dead_x_scale = tk.Scale(self.frm_sw, 
                                     from_ = 1, to = 100, 
                                     orient = 'horizontal',
                                     showvalue = 1,
                                     command = self.watcher.set_dead_x,
                                     length = 300)
        self.dead_y_scale = tk.Scale(self.frm_sw, 
                                     from_=1, to=100, 
                                     orient='horizontal',
                                     showvalue = 1,
                                     command = self.watcher.set_dead_y,
                                     length = 300,)
        self.dead_x_scale.set(self.watcher.dead_x)
        self.dead_y_scale.set(self.watcher.dead_y)
        self.dead_x_label = tk.Label(self.frm_sw, text = 'X-Deadzone',
                                     anchor = 'se')
        self.dead_y_label = tk.Label(self.frm_sw, text = 'Y-Deadzone',
                                     anchor = 'se')
        
        # 3. Title
        self.sw_title = tk.Label(self.frm_sw,
                                 text='Mouse Movement Settings', 
                                 justify = 'center')
        self.sw_title.configure(font=tk.StringVar(self.frm_sw, 
                                                  'TkHeadingFont'))
        
        # 4. Inverted Camera Setting
        self.inv_cam_var = tk.IntVar(self.frm_sw)
        self.inv_cam_var.set(self.watcher.flipped)
        self.inv_cam_check = tk.Checkbutton(self.frm_sw,
                                            variable = self.inv_cam_var,
                                            text = 'Inverted Camera',
                                            justify = 'right')
        
        # 5. Grid SW Frame
        self.sw_title.grid(row=1, column=1, columnspan=2)
        self.sens_x_scale.grid(row = 2, column = 2, rowspan = 2)
        self.sens_y_scale.grid(row = 4, column = 2, rowspan = 2)
        self.dead_x_scale.grid(row = 6, column = 2, rowspan = 2)
        self.dead_y_scale.grid(row = 8, column = 2, rowspan = 2)
        self.sens_x_label.grid(row = 3, column = 1)
        self.sens_y_label.grid(row = 5, column = 1)
        self.dead_x_label.grid(row = 7, column = 1)
        self.dead_y_label.grid(row = 9, column = 1)
        self.inv_cam_check.grid(row=11, column=1, columnspan=2)
        
        # Setup SE frame
        # 1. Recalibrate Button
        self.recal_bttn = tk.Button(self.frm_se,
                                     text='Recalibrate Deadzone',
                                     command = self.watcher.calibrate,
                                     width = 40,
                                     height = 2,
                                     justify = 'center')
        
        # 2. Start/Stop button
        self.on_bttn = tk.Button(self.frm_se,
                                 text='Start',
                                 command = self.start_running,
                                 width = 20,
                                 height = 2,
                                 justify = 'center')
        
        self.off_bttn = tk.Button(self.frm_se,
                                 text='Stop',
                                 command = self.stop_running,
                                 width = 20,
                                 height = 2,
                                 justify = 'center',
                                 state = 'disabled')
        
        # 3. Grid SE Frame
        self.on_bttn.grid(row=1, column=1, rowspan=2, columnspan=1,
                          padx=5, pady=5)
        self.off_bttn.grid(row=1, column=2, rowspan=2, columnspan=1,
                          padx=5, pady=5)
        self.recal_bttn.grid(row=3, column=1, rowspan=2, columnspan=2,
                             padx=5, pady=5)
        
        
        # Setup NE frame
        # 1. Create scrolled text box
        self.scroll_text = st.ScrolledText(self.frm_ne, height = 17)
                                         
        
        # 2. Pack widget
        self.scroll_text.grid(row = 1, column = 1,
                              columnspan = 2, rowspan = 12)
        
        self.scroll_text.insert('insert','Speech Recognition Output:\n')
        self.scroll_text.configure(state='disabled')
        
        
        # Start main loop
        self.root.after(10, self.after)
        self.root.mainloop()