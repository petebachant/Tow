#!/usr/bin/env bash

echo Building GUI

python -m PyQt4.uic.pyuic.py tow/mainwindow.ui -o tow/mainwindow.py

echo Building resource file

pyrcc4 -py3 tow/icons/tow_resources.qrc -o tow/tow_resources_rc.py

echo Replacing relative import

sed -i 's/import tow_resources_rc/from . import tow_resources_rc/g' tow/mainwindow.py

echo Done
