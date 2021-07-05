import pyautogui
import sys
import win32api
import win32con
import winreg
import os
import difflib
import subprocess

def get_software_list(hive, flag):
    aReg = winreg.ConnectRegistry(None, hive)
    aKey = winreg.OpenKey(aReg, 
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", 0, 
        winreg.KEY_READ | flag)

    count_subkey = winreg.QueryInfoKey(aKey)[0]

    software_list = []

    for i in range(count_subkey):
        software = {}
        try:
            asubkey_name = winreg.EnumKey(aKey, i)
            asubkey = winreg.OpenKey(aKey, asubkey_name)
            software['name'] = winreg.QueryValueEx(asubkey, "DisplayName")[0]
            
            try:
                software['path'] = winreg.QueryValueEx(
                    asubkey, "InstallLocation")[0]
            except:
                software['path'] = ''
            software_list.append(software)
        except EnvironmentError:
            continue

    return software_list

def get_office_programs(path):
    names=[]; paths=[];
    for root,_,files in os.walk(path):
        for file in files:
            # if root==r'C:\Program Files\Microsoft Office\root\Office16':
            #     pass
            if file.lower()=='winword.exe':
                names.append('microsoft word')
                paths.append(root+'\\'+file)
            elif file.lower()=='excel.exe':
                names.append('microsoft excel')
                paths.append(root+'\\'+file)
            elif file.lower()=='lync.exe':
                names.append('Skype')
                paths.append(root+'\\'+file)
            elif file.lower()=='msaccess.exe':
                names.append('microsoft access')
                paths.append(root+'\\'+file)
            elif file.lower()=='onenote.exe':
                names.append('microsoft onenote')
                paths.append(root+'\\'+file)
            elif file.lower()=='powerpnt.exe':
                names.append('microsoft powerpoint')
                paths.append(root+'\\'+file)
    return names,paths

class Handler():
    
    def __init__(self):
        self.COMMANDS = ['click', 'open', 'close', 'type', 'move', 'press', 
                         'release', 'hold', 'sensitivity', 'start', 'stop',
                         'calibrate', 'dead', 'recalibrate', 'invert']
        
        self.SOFTWARE_LIST = (get_software_list(
                            winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_32KEY)
                        + get_software_list(
                            winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_64KEY)
                        + get_software_list(winreg.HKEY_CURRENT_USER, 0))
        
        self.SOFTWARE_DICT={'microsoft edge' : 'MicrosoftEdge.exe',
                       'notepad' : 'notepad.exe'}
        
        self.open_applications={}
        
        for software in self.SOFTWARE_LIST:
            path = software['path']
            
            if path!='' and os.path.exists(path) and (
                    'microsoft office' in path.lower()):
                path=os.path.join(r'C:\Program Files\Microsoft Office','root')
                names, paths = get_office_programs(path)
                i=0
                for name in names:
                    self.SOFTWARE_DICT[name]=paths[i]
                    i+=1
                    
            elif path!='' and os.path.exists(path):
                name = software['name']
                poss = []; poss_l=[]; poss_paths=[]
                for root,_,files in os.walk(path):
                    if files!=[]:
                        for file in files:
                            if file[-3::]=='exe':
                                poss.append(file)
                                poss_l.append(file.lower())
                                poss_paths.append(root)
                matches = difflib.get_close_matches(name.lower()+'.exe', 
                                                    poss_l)
                if matches!=[]:
                    i = poss_l.index(matches[0])
                    match=poss[i]
                    path=poss_paths[i]
                    if path[-1]=='\\':
                        self.SOFTWARE_DICT[name.lower()]=path + match
                    else:
                        self.SOFTWARE_DICT[name.lower()]=path + '\\' + match
        
        self.KEY_LIST = pyautogui.KEYBOARD_KEYS
    
    def execute(self, cmd, prefix, modifiers):
        
        if cmd == 'click':
            presses = 1
            for mod in modifiers:
                try:
                    num=int(mod)
                    presses=num
                except(ValueError):
                    pass
                
            if not bool(prefix): prefix='left'
            if 'hold' in modifiers:
                self.mouseDown(button=prefix)
            else:
                self.click(button=prefix, clicks=presses)
        
        elif cmd == 'open':
            # Open command decoder
            apps = list(self.SOFTWARE_DICT.keys())
            request = modifiers[0].lower()
            matches = difflib.get_close_matches(request, apps)
            if matches!=[]:
                self.open_application(self.SOFTWARE_DICT[matches[0]],
                                      matches[0])
            else:
                print('No application found')
                print(request)
                print(apps)
                
        elif cmd == 'close':
            # Close command decoder
            running_apps = list(self.open_applications)
            request = modifiers[0].lower()
            matches = difflib.get_close_matches(request, running_apps)
            if matches !=[]:
                self.close_application(matches[0])
            else:
                print('No running application found')
                print(request)
                print(running_apps)
            
        elif cmd == 'type':
            self.type_string(modifiers[0])
            
        elif cmd == 'move':
            # move command decoder
            pass
        elif cmd == 'press':
            keys=[]; presses=1;
            for mod in modifiers:
                if mod in self.KEY_LIST: 
                    keys.append(mod)
                else:
                    try:
                        num=int(mod)
                        presses=num
                    except(ValueError):
                        pass
                    
            if len(keys)>1:
                self.press_keys(keys, presses)
            elif len(keys)==1:
                self.press_key(keys[0], presses)
            else:
                print('No keys given as modifier.')
            
        elif cmd == 'hold':
            for mod in modifiers:
                if mod in self.KEY_LIST: 
                    self.keyDown(mod)
                    print('key down')
                    
        elif cmd == 'release':
            print(self.get_left_mouse_state())
            if 'click' in modifiers:
                if prefix==None: prefix='left'
                self.mouseUp(button=prefix)
            else:
                for mod in modifiers:
                    if mod in self.KEY_LIST: self.keyUp(mod)
        return
        
    
    def get_left_mouse_state(self):
        if sys.platform=='win32':
            return win32api.GetKeyState(win32con.VK_LBUTTON)
        
    def get_right_mouse_state(self):
        if sys.platform=='win32':
            return win32api.GetKeyState(win32con.VK_RBUTTON)
    
    def click(self, x=None, y=None, button='left', clicks=1):
        pyautogui.click(x,y,button=button, clicks=clicks)
        return
        
    def drag(self, x_dist, y_dist, duration=0.1):
        pyautogui.drag(x_dist, y_dist, duration=duration)
        return
    
    def move(self, x,y,duration=0.1):
        pyautogui.move(x,y,duration)
        return
    
    def moveTo(self, x,y,duration=0.1):
        if pyautogui.onScreen(x,y):
            pyautogui.moveTo(x,y,duration)
        return
    
    def mouseDown(self, x=None, y=None, button='left'):
        pyautogui.mouseDown(x, y, button=button)
        return
    
    def mouseUp(self, x=None, y=None, button='left'):
        pyautogui.mouseUp(x, y, button=button)
        return
    
    def scroll(self, dist, x=None, y=None):
        pyautogui.scroll(dist, x, y)
        return
    
    def type_string(self, string, interval=0):
        pyautogui.write(string, interval)
        return
    
    def press_key(self, key, presses=1):
        pyautogui.press(key, presses)
    
    def press_keys(self, keys, presses=1):
        for i in range(presses):
            for key in keys:
                pyautogui.keyDown(key)
            for key in keys:
                pyautogui.keyUp(key)
        return
    
    def keyDown(self, key):
        pyautogui.keyDown(key)
        return
    
    def keyUp(self, key):
        pyautogui.keyUp(key)
        return
    
    def open_application(self, path, name='unknown'):
        app = subprocess.Popen(path)
        self.open_applications[name]=app
        return
    
    def close_application(self, name):
        app = self.open_applications[name]
        app.kill()
        del self.open_applications[name]
        return
        