call buildgui

cd ../pyinstaller-2.0

python pyinstaller.py -y --icon=../Tow/icons/tow_icon_b.ico --noconsole ../PyQt-testing/Tow/tow.py

cd Tow/dist/Tow

Tow