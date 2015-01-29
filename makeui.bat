echo Building GUI

call pyuic4 tow/mainwindow.ui > tow/mainwindow.py

echo Building resource file

call pyrcc4 -py3 tow/icons/tow_resources.qrc -o tow/tow_resources_rc.py

echo Done