import os
import winshell
from win32com.client import Dispatch

def create_startup_shortcut():
    startup_folder = winshell.startup()
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "DeskUpper.exe")
    
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(os.path.join(startup_folder, "DeskUpper.lnk"))
    shortcut.Targetpath = path
    shortcut.WorkingDirectory = os.path.dirname(path)
    shortcut.save()

if __name__ == "__main__":
    create_startup_shortcut() 