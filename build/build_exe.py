import PyInstaller.__main__
import os
import sys

# Change to client directory
os.chdir('../client')

PyInstaller.__main__.run([
    'clipboard_manager.py',
    '--name=CloudClipboard',
    '--onefile',
    '--windowed',
    '--noconsole',
    '--hidden-import=pystray',
    '--hidden-import=PIL._tkinter_finder',
    '--hidden-import=win32timezone',
    '--add-data=config.py;.',
    '--add-data=auth_window.py;.',
    '--icon=clipboard_icon.ico',  # Optional
])

print("\n" + "="*60)
print("✅ EXE BUILD COMPLETE!")
print("="*60)
print(f"Location: client/dist/CloudClipboard.exe")
print("="*60)
