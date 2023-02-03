"""Tow application."""

import json
import os
import sys

from acspy import acsc
from PyQt5 import QtGui, QtNetwork
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .__init__ import __version__
from .mainwindow import *


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Set up some parameters
        self.axis = 5
        self.homecounter = 0
        self.jogmode = False
        self.leftlimit = 24.9
        self.platform = 9.0
        self.override = False
        self.axis_enabled = False

        # Set maximum velocities to 2 m/s
        self.ui.velSpinBox.setMaximum(2.0)
        self.ui.velSpinBox_baf1.setMaximum(2.0)
        self.ui.velSpinBox_baf2.setMaximum(2.0)

        # Set initial states of all buttons
        self.ui.rbAbsolute.setEnabled(False)
        self.ui.rbAbsolute_baf.setEnabled(False)
        self.ui.enableAxis.setEnabled(False)
        self.ui.actionRunHoming.setEnabled(False)
        self.ui.dock_jog.setEnabled(False)
        self.ui.groupBox_shortcuts.setEnabled(False)
        self.ui.tabWidgetMode.setEnabled(False)
        self.ui.toolBar_Jog.setEnabled(False)
        self.ui.enableAxis.setIcon(QIcon())
        self.ui.posSpinBox.setMinimum(-self.leftlimit)
        self.ui.posSpinBox.setMaximum(self.leftlimit)
        self.ui.posSpinBox_baf1.setMinimum(-self.leftlimit)
        self.ui.posSpinBox_baf1.setMaximum(self.leftlimit)
        self.ui.posSpinBox_baf2.setMinimum(-self.leftlimit)
        self.ui.posSpinBox_baf2.setMaximum(self.leftlimit)
        self.ui.posSpinBox_baf2.setDisabled(True)

        # Add some labels to the status bar
        self.hlabel = QLabel()
        self.hlabel.setText("Not homed ")
        self.ui.statusBar.addWidget(self.hlabel)
        self.poslabel = QLabel()
        self.poslabel.setText("Pos. (m): ")
        self.ui.statusBar.addWidget(self.poslabel)
        self.vellabel = QLabel()
        self.vellabel.setText("Vel. (m/s): ")
        self.ui.statusBar.addWidget(self.vellabel)

        # Add a button to the toolbar
        self.ui.toolBar_Jog.addWidget(self.ui.pbJogPlus)
        self.ui.toolBar_Jog.addWidget(self.ui.pbJogMinus)
        self.ui.pbJogMinus.setFixedHeight(27)
        self.ui.pbJogPlus.setFixedHeight(27)
        self.ui.pbJogMinus.setFixedWidth(32)
        self.ui.pbJogPlus.setFixedWidth(32)
        self.ui.dock_jog.close()

        # Set up timers
        self.timer_slow = QTimer()
        self.timer_slow.timeout.connect(self.on_timer_slow)
        self.timer_fast = QTimer()
        self.timer_fast.timeout.connect(self.on_timer_fast)

        # Connect to the controller
        self.simulator = False
        self.retry = True
        if self.simulator:
            self.hcomm = acsc.openCommDirect()
        else:
            self.hcomm = acsc.openCommEthernetTCP("10.0.0.100", 701)

        # If connection fails, bring up error message box
        while self.hcomm == acsc.INVALID and self.retry:
            msgtxt = "Unable to connect to controller.\n\n"
            msgtxt += "Check that controller is powered-on and "
            msgtxt += "SPiiPlus User Mode Driver is running."
            c_err_box = QMessageBox()
            c_err_box.setIcon(QMessageBox.Critical)
            c_err_box.setWindowIcon(QIcon(":/icons/tow_icon.svg"))
            c_err_box.setWindowTitle("Connection Error")
            c_err_box.setText(msgtxt)
            c_err_box.setStandardButtons(QMessageBox.Retry | QMessageBox.Abort)
            c_err_box.setDefaultButton(QMessageBox.Retry)
            c_err_box.addButton("Use &Simulator", QMessageBox.AcceptRole)

            ret = c_err_box.exec_()

            if ret == QMessageBox.Retry:
                if self.simulator:
                    self.hcomm = acsc.openCommDirect()
                else:
                    self.hcomm = acsc.openCommEthernetTCP("10.0.0.100", 701)
            elif ret == QMessageBox.Abort:
                self.connectfail = True
                self.retry = False
                self.timer_fast.start(10)
            elif ret == QMessageBox.AcceptRole:
                self.simulator = True
                self.hcomm = acsc.openCommDirect()

        if self.hcomm != acsc.INVALID:
            self.timer_slow.start(150)
            self.timer_fast.start(50)
            self.ui.enableAxis.setEnabled(True)
            self.ui.actionRunHoming.setEnabled(True)

        # Register the emergency stop button
        acsc.registerEmergencyStop()

        # Make sure jog program is not running
        acsc.stopBuffer(self.hcomm, 5)

        # Create the jog group action group
        self.offset_group = QActionGroup(self)
        self.ui.traverseOff.setActionGroup(self.offset_group)
        self.ui.traverse1m.setActionGroup(self.offset_group)
        self.ui.traverse2m.setActionGroup(self.offset_group)
        self.ui.traverse3m.setActionGroup(self.offset_group)
        self.ui.traverse4m.setActionGroup(self.offset_group)
        self.traverse_offset_actions = {
            "off": self.ui.traverseOff,
            "1m": self.ui.traverse1m,
            "2m": self.ui.traverse2m,
            "3m": self.ui.traverse3m,
            "4m": self.ui.traverse4m,
        }

        # Create TCP server for remote control
        remoteserver = QtNetwork.QTcpServer()
        print(str(remoteserver.serverAddress().toString()))

        # Connect signals and slots
        self.connectslots()

        # Load settings
        self.load_settings()

    def load_settings(self):
        """
        Loads settings in JSON format from `~/.towconfig`.
        """
        userdir = os.path.expanduser("~")
        self.settings_fpath = os.path.join(userdir, ".towconfig")
        try:
            with open(self.settings_fpath) as f:
                self.settings = json.load(f)
        except IOError:
            self.settings = {}
        if "Last window location" in self.settings:
            self.move(
                QPoint(
                    self.settings["Last window location"][0],
                    self.settings["Last window location"][1],
                )
            )
        if "Mode index" in self.settings:
            self.ui.tabWidgetMode.setCurrentIndex(self.settings["Mode index"])
        if "Traverse offset" in self.settings:
            offset = self.settings["Traverse offset"]
            self.traverse_offset_actions[offset].trigger()
        if "Point-to-point" in self.settings:
            s = self.settings["Point-to-point"]
            if "absolute" in s:
                if self.ui.rbAbsolute.isEnabled():
                    self.ui.rbAbsolute.setChecked(s["absolute"])
            if "pos" in s:
                self.ui.posSpinBox.setValue(s["pos"])
            if "vel" in s:
                self.ui.velSpinBox.setValue(s["vel"])
            if "acc" in s:
                self.ui.accSpinBox.setValue(s["acc"])
        if "Back-and-forth" in self.settings:
            s = self.settings["Back-and-forth"]
            if "absolute" in s:
                if self.ui.rbAbsolute_baf.isEnabled():
                    self.ui.rbAbsolute_baf.setChecked(s["absolute"])
            if "p1" in s:
                self.ui.posSpinBox_baf1.setValue(s["p1"])
            if "p2" in s:
                self.ui.posSpinBox_baf2.setValue(s["p2"])
            if "v1" in s:
                self.ui.velSpinBox_baf1.setValue(s["v1"])
            if "v2" in s:
                self.ui.velSpinBox_baf2.setValue(s["v2"])
            if "a1" in s:
                self.ui.accSpinBox_baf1.setValue(s["a1"])
            if "a2" in s:
                self.ui.accSpinBox_baf2.setValue(s["a2"])
            if "loop" in s:
                self.ui.checkBox_loop.setChecked(s["loop"])

    def connectslots(self):
        # Connect signals to their appropriate slots
        self.ui.pbGo.clicked.connect(self.on_go)
        self.ui.enableAxis.triggered.connect(self.on_enableAxis_click)
        self.ui.pbJogMinus.pressed.connect(self.on_pbJogMinus_press)
        self.ui.pbJogMinus.released.connect(self.on_pbJogMinus_release)
        self.ui.pbJogPlus.pressed.connect(self.on_pbJogPlus_press)
        self.ui.pbJogPlus.released.connect(self.on_pbJogPlus_release)
        self.ui.actionRunHoming.triggered.connect(self.on_runHoming)
        self.ui.actionHalt.triggered.connect(self.on_halt)
        self.ui.pbHalt.clicked.connect(self.on_halt)
        self.ui.actionAbout.triggered.connect(self.on_actionAbout)
        self.ui.pbJogPendant.clicked.connect(self.on_JogPendant)
        self.ui.actionJogPendant.triggered.connect(self.on_JogPendant)
        self.offset_group.triggered.connect(self.on_traverseChange)
        self.ui.actionOverride.triggered.connect(self.on_override)
        self.ui.actionWiki.triggered.connect(self.on_wiki)
        self.ui.pbGoLeftLimit.clicked.connect(self.on_goLeftLimit)
        self.ui.pbGoRightLimit.clicked.connect(self.on_goRightLimit)
        self.ui.pbGoPlatform.clicked.connect(self.on_goPlatform)
        self.ui.rbAbsolute.clicked.connect(self.on_abs)
        self.ui.rbAbsolute_baf.clicked.connect(self.on_abs)
        self.ui.rbRelative.clicked.connect(self.on_rel)
        self.ui.rbRelative_baf.clicked.connect(self.on_rel)
        self.ui.pbHalt_baf.clicked.connect(self.on_halt)
        self.ui.pbGo_baf.clicked.connect(self.on_go_baf)

    def on_timer_slow(self):
        self.axis_enabled = acsc.getMotorEnabled(self.hcomm, self.axis)

        if self.axis_enabled:
            self.ui.enableAxis.setChecked(True)
            self.ui.enableAxis.setText("Disable")
            self.ui.enableAxis.setIcon(QIcon(":icons/cancelx.png"))
        else:
            self.ui.enableAxis.setChecked(False)
            self.ui.enableAxis.setText("Enable")
            self.ui.enableAxis.setIcon(QIcon(":icons/checkmark.png"))
            self.jogmode = False
            acsc.stopBuffer(self.hcomm, 5)

        if self.simulator == False:
            self.homecounter = acsc.readInteger(
                self.hcomm, None, "homeCounter_tow"
            )

    def on_timer_fast(self):
        if self.hcomm == acsc.INVALID:
            self.close()
        self.ui.tabWidgetMode.setEnabled(self.axis_enabled)
        self.ui.dock_jog.setEnabled(self.axis_enabled)
        self.ui.pbJogPendant.setEnabled(self.axis_enabled)
        self.ui.toolBar_Jog.setEnabled(self.axis_enabled)

        if self.homecounter > 0 or self.override == True:
            self.ui.rbAbsolute.setEnabled(True)
            self.ui.rbAbsolute_baf.setEnabled(True)
            if self.homecounter > 0:
                self.ui.groupBox_shortcuts.setEnabled(True)
                self.hlabel.setText("Homed ")

        if self.jogmode == True:
            self.ui.pbJogPendant.setChecked(True)
            self.ui.actionJogPendant.setChecked(True)
        else:
            self.ui.pbJogPendant.setChecked(False)
            self.ui.actionJogPendant.setChecked(False)

        # Get and display reference position and velocity
        self.rpos = acsc.getRPosition(self.hcomm, self.axis)
        self.rvel = acsc.getRVelocity(self.hcomm, self.axis)
        self.poslabel.setText("Pos. (m): %.3f " % self.rpos)
        self.vellabel.setText("Vel. (m/s): %.2f " % self.rvel)

    def on_enableAxis_click(self):
        if not self.axis_enabled:
            self.axis_enabled = True
            acsc.enable(self.hcomm, self.axis, acsc.SYNCHRONOUS)
            self.ui.enableAxis.setText("Disable")
        else:
            self.axis_enabled = False
            acsc.disable(self.hcomm, self.axis, acsc.SYNCHRONOUS)
            self.ui.enableAxis.setText("Enable")

    def on_runHoming(self):
        if self.simulator:
            self.homecounter += 1
        else:
            acsc.runBuffer(self.hcomm, 2, None)
        self.ui.rbAbsolute.setChecked(True)
        self.ui.rbAbsolute_baf.setChecked(True)
        self.on_abs()
        self.ui.actionOverride.setEnabled(False)
        self.override = False

    def on_go(self):
        target = self.ui.posSpinBox.value()
        vel = self.ui.velSpinBox.value()
        acc = self.ui.accSpinBox.value()
        acsc.setVelocity(self.hcomm, self.axis, vel)
        acsc.setAcceleration(self.hcomm, self.axis, acc)
        acsc.setDeceleration(self.hcomm, self.axis, acc)
        acsc.setJerk(self.hcomm, self.axis, acc * 10)
        if self.ui.rbRelative.isChecked() == True:
            flags = acsc.AMF_RELATIVE
        else:
            flags = None
        acsc.toPoint(self.hcomm, flags, self.axis, target)

    def on_go_baf(self):
        """Do a back-and-forth move."""
        p1 = self.ui.posSpinBox_baf1.value()
        v1 = self.ui.velSpinBox_baf1.value()
        v2 = self.ui.velSpinBox_baf2.value()
        a1 = self.ui.accSpinBox_baf1.value()
        a2 = self.ui.accSpinBox_baf2.value()
        if self.ui.rbRelative_baf.isChecked():
            relflag = "r"
            p2 = -p1
        else:
            relflag = ""
            p2 = self.ui.posSpinBox_baf2.value()
        txt = "GLOBAL INT move\n"
        txt += "JERK({}) = 1\n".format(self.axis)
        txt += "move = 1\n"
        txt += "WHILE move\n"
        txt += "    ACC({}) = {}\n".format(self.axis, a1)
        txt += "    DEC({}) = {}\n".format(self.axis, a1)
        txt += "    VEL({}) = {}\n".format(self.axis, v1)
        txt += "    ptp/e{} {}, {}\n".format(relflag, self.axis, p1)
        txt += "    ACC({}) = {}\n".format(self.axis, a2)
        txt += "    DEC({}) = {}\n".format(self.axis, a2)
        txt += "    VEL({}) = {}\n".format(self.axis, v2)
        txt += "    ptp/e{} {}, {}\n".format(relflag, self.axis, p2)
        if not self.ui.checkBox_loop.isChecked():
            txt += "    move = 0\n"
        txt += "END\n"
        txt += "STOP\n"
        acsc.loadBuffer(self.hcomm, 19, txt, 512)
        acsc.runBuffer(self.hcomm, 19)

    def on_pbJogMinus_press(self):
        acsc.setAcceleration(self.hcomm, self.axis, 0.2, acsc.SYNCHRONOUS)
        acsc.setDeceleration(self.hcomm, self.axis, 0.2, acsc.SYNCHRONOUS)
        acsc.setJerk(self.hcomm, self.axis, 2, acsc.SYNCHRONOUS)
        acsc.jog(self.hcomm, acsc.AMF_VELOCITY, self.axis, -0.2)

    def on_pbJogMinus_release(self):
        acsc.halt(self.hcomm, self.axis)

    def on_pbJogPlus_press(self):
        acsc.setAcceleration(self.hcomm, self.axis, 0.2, acsc.SYNCHRONOUS)
        acsc.setDeceleration(self.hcomm, self.axis, 0.2, acsc.SYNCHRONOUS)
        acsc.setJerk(self.hcomm, self.axis, 2, acsc.SYNCHRONOUS)
        acsc.jog(self.hcomm, acsc.AMF_VELOCITY, self.axis, 0.2)

    def on_pbJogPlus_release(self):
        acsc.halt(self.hcomm, self.axis)

    def on_JogPendant(self):
        if self.jogmode == False:
            self.jogmode = True
            acsc.runBuffer(self.hcomm, 5, None)
        elif self.jogmode == True:
            acsc.stopBuffer(self.hcomm, 5)
            self.jogmode = False

    def on_halt(self):
        acsc.writeInteger(self.hcomm, "move", 0)
        acsc.stopBuffer(self.hcomm, 19)
        acsc.halt(self.hcomm, self.axis)

    def on_actionAbout(self):
        about_text = "<b>Tow {}</b><br>".format(__version__)
        about_text += "A simple towing app for the UNH tow tank<br><br>"
        about_text += "By Pete Bachant<br>"
        about_text += "petebachant@gmail.com"
        QMessageBox.about(self, "About Tow", about_text)

    def on_traverseChange(self):
        if self.ui.traverseOff.isChecked():
            self.leftlimit = 26.2
            self.platform = 10.2
        elif self.ui.traverse1m.isChecked():
            self.leftlimit = 24.9
            self.platform = 9.0
        elif self.ui.traverse2m.isChecked():
            self.leftlimit = 23.9
            self.platform = 8.0
        elif self.ui.traverse3m.isChecked():
            self.leftlimit = 22.9
            self.platform = 7.0
        elif self.ui.traverse4m.isChecked():
            self.leftlimit = 21.9
            self.platform = 6.0
        elif self.ui.traverseCustom.isChecked():
            print("Nope, not yet")
        if self.ui.rbRelative.isChecked():
            self.ui.posSpinBox.setMinimum(-self.leftlimit)
        self.ui.posSpinBox.setMaximum(self.leftlimit)
        if self.ui.rbRelative_baf.isChecked():
            self.ui.posSpinBox_baf1.setMinimum(-self.leftlimit)
        self.ui.posSpinBox_baf1.setMaximum(self.leftlimit)

    def on_goLeftLimit(self):
        vel = self.ui.velSpinBox.value()
        acc = self.ui.accSpinBox.value()
        acsc.setVelocity(self.hcomm, self.axis, vel)
        acsc.setAcceleration(self.hcomm, self.axis, acc)
        acsc.setDeceleration(self.hcomm, self.axis, acc)
        acsc.setJerk(self.hcomm, self.axis, acc * 10)
        acsc.toPoint(self.hcomm, None, self.axis, self.leftlimit)

    def on_goRightLimit(self):
        vel = self.ui.velSpinBox.value()
        acc = self.ui.accSpinBox.value()
        acsc.setVelocity(self.hcomm, self.axis, vel)
        acsc.setAcceleration(self.hcomm, self.axis, acc)
        acsc.setDeceleration(self.hcomm, self.axis, acc)
        acsc.setJerk(self.hcomm, self.axis, acc * 10)
        acsc.toPoint(self.hcomm, None, self.axis, 0.0)

    def on_goPlatform(self):
        vel = self.ui.velSpinBox.value()
        acc = self.ui.accSpinBox.value()
        acsc.setVelocity(self.hcomm, self.axis, vel)
        acsc.setAcceleration(self.hcomm, self.axis, acc)
        acsc.setDeceleration(self.hcomm, self.axis, acc)
        acsc.setJerk(self.hcomm, self.axis, acc * 10)
        acsc.toPoint(self.hcomm, None, self.axis, self.platform)

    def on_override(self):
        self.override = True
        self.ui.rbAbsolute.setChecked(True)
        self.ui.rbAbsolute_baf.setChecked(True)
        self.on_abs()

    def on_abs(self):
        if not self.override:
            self.ui.posSpinBox.setMinimum(0.0)
            self.ui.posSpinBox_baf1.setMinimum(0.0)
            self.ui.posSpinBox_baf2.setMinimum(0.0)
        self.ui.posSpinBox_baf2.setEnabled(True)

    def on_rel(self):
        self.ui.posSpinBox.setMinimum(-self.leftlimit)
        self.ui.posSpinBox_baf1.setMinimum(-self.leftlimit)
        self.ui.posSpinBox_baf2.setDisabled(True)

    def on_wiki(self):
        url = QUrl("https://github.com/unh-oe/wave-tow-tank/wiki")
        QDesktopServices.openUrl(url)

    def closeEvent(self, event):
        acsc.stopBuffer(self.hcomm, 5)
        acsc.closeComm(self.hcomm)
        acsc.unregisterEmergencyStop()
        self.settings["Last window location"] = [
            self.pos().x(),
            self.pos().y(),
        ]
        self.settings["Mode index"] = self.ui.tabWidgetMode.currentIndex()
        for key, val in self.traverse_offset_actions.items():
            if val.isChecked():
                offset = key
        self.settings["Traverse offset"] = offset
        self.settings["Point-to-point"] = {
            "absolute": self.ui.rbAbsolute.isChecked(),
            "pos": self.ui.posSpinBox.value(),
            "vel": self.ui.velSpinBox.value(),
            "acc": self.ui.accSpinBox.value(),
        }
        self.settings["Back-and-forth"] = {
            "absolute": self.ui.rbAbsolute_baf.isChecked(),
            "p1": self.ui.posSpinBox_baf1.value(),
            "p2": self.ui.posSpinBox_baf2.value(),
            "v1": self.ui.velSpinBox_baf1.value(),
            "v2": self.ui.velSpinBox_baf2.value(),
            "a1": self.ui.accSpinBox_baf1.value(),
            "a2": self.ui.accSpinBox_baf2.value(),
            "loop": self.ui.checkBox_loop.isChecked(),
        }
        with open(self.settings_fpath, "w") as f:
            json.dump(self.settings, f, indent=4)


def main():
    app = QApplication(sys.argv)
    height = QDesktopWidget().screenGeometry().height()
    width = QDesktopWidget().screenGeometry().width()
    w = MainWindow()
    w.show()
    w.setFixedSize(w.size())
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
