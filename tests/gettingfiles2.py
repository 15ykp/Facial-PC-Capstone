# -*- coding: utf-8 -*-
"""
Created on Thu Jan  7 13:44:35 2021

@author: Brandon Caron
"""

import winreg
import os
import difflib

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

SOFTWARE_LIST = (get_software_list(
                    winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_32KEY) + 
                get_software_list(
                    winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_64KEY) + 
                get_software_list(winreg.HKEY_CURRENT_USER, 0))
    
SOFTWARE_DICT={'microsoft edge' : 'MicrosoftEdge.exe',
               'notepad' : 'notepad.exe'}

for software in SOFTWARE_LIST:
        path = software['path']
        
        if path!='' and os.path.exists(path) and (
                'microsoft office' in path.lower()):
            names, paths = get_office_programs(path)
            i=0
            for name in names:
                SOFTWARE_DICT[name]=paths[i]
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
            matches = difflib.get_close_matches(name.lower()+'.exe', poss_l)
            if matches!=[]:
                i = poss_l.index(matches[0])
                match=poss[i]
                path=poss_paths[i]
                if path[-1]=='\\':
                    SOFTWARE_DICT[name.lower()]=path + match
                else:
                    SOFTWARE_DICT[name.lower()]=path + '\\' + match
            else:
                print('couldnt find match for ',name)
                
del(path, names, paths, i, name, root, files, file, poss, poss_l, poss_paths,
    matches, match, software)