# -*- coding: utf-8 -*-
"""
Created on Thu Mar  4 12:57:04 2021

@author: Brandon Caron
"""

a = App(None,watcher)
img = a.watcher.img_draw
tkimg = [ImageTk.PhotoImage(master=a.frm_nw, image=Image.fromarray(img))]
a.cvs_img = a.cvs_face.create_image(0,0, anchor="nw", image=tkimg[0])