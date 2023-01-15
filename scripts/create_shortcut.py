"""Creates Windows shortcut."""

import os
import sys

from win32com.client import Dispatch

python_dir = os.path.split(sys.executable)[0]
shortcut_path = "Tow.lnk"
pythonw_path = os.path.join(python_dir, "pythonw.exe")
tow_path = os.path.join(python_dir, "Scripts", "tow-script.py")
wdir = r"C:\temp"
icon = os.path.join(
    python_dir, "Lib", "site-packages", "tow", "icons", "tow_icon.ico"
)
target_path = "{} {}".format(pythonw_path, tow_path)
print(target_path)

shell = Dispatch("WScript.shell")
shortcut = shell.CreateShortCut(shortcut_path)
shortcut.Targetpath = pythonw_path
shortcut.Arguments = tow_path
shortcut.WorkingDirectory = wdir
shortcut.IconLocation = icon
shortcut.save()
