import csv
import os
import re
import sys
import bluetooth as bt
from threading import Thread, Timer

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDesktopWidget
from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog, QFileDialog
from PyQt5.QtCore import Qt, QDateTime, pyqtSignal, pyqtSlot

from GUI.DistancesCarRemoteControler import Ui_MainWindow
from GUI.CapturesDialog import Ui_CapturesDialog

DISTANCES_CAR_BLUETOOTH_SERVICE_UUID = "ad6e04a5-2ae4-4c80-9140-34016e468ee7"


class CapturesDialog(QDialog, Ui_CapturesDialog):

    DISTANCES_FILENAME = "Distances.txt"

    def __init__(self, parent, directory):
        super(CapturesDialog, self).__init__(parent)
        self.setupUi(self)
        self.distances = []
        self.dir = directory
        with open(os.path.join(directory, self.DISTANCES_FILENAME), newline='') as distancesFile:
            self.distances = [line for line in csv.reader(distancesFile)]
        self.set_captures_count(len(self.distances))
        self.captureNumberSpinBox.valueChanged.connect(self.set_current_capture)
        self.captureNumberSpinBox.setValue(1)
        self.captureNumberSpinBox.setMinimum(1)

    def set_captures_count(self, count):
        self.captureNumberSpinBox.setMaximum(count)
        self.capturesCountLcdNumber.display(count)

    def set_current_capture(self, capture_number):
        capture_id = self.distances[capture_number - 1][0]
        capture_filename = 'IMG_{}.jpg'.format(capture_id)
        capture = QPixmap(os.path.join(self.dir, capture_filename))
        self.captureViewLabel.setPixmap(capture)
        self.captureDateTimeEdit.setDateTime(QDateTime.fromMSecsSinceEpoch(int(capture_id)))
        self.distancesLineEdit.setText('|' + '|'.join(self.distances[capture_number - 1][1:]) + '|')


class BluetoothConnectionThread(Thread):

    def __init__(self, parent_window):
        super(BluetoothConnectionThread, self).__init__()
        assert isinstance(parent_window, MainWindow)
        self.window = parent_window

    def run(self):
        try:
            self.window.btChanged.emit(1)
            services = bt.find_service(uuid=DISTANCES_CAR_BLUETOOTH_SERVICE_UUID)
            if len(services) > 0:
                s = services[0]
                self.window.btChanged.emit(2)
                self.window.bluetoothSocket.connect((s['host'], s['port']))
                self.window.btChanged.emit(3)
                self.window.bluetoothReceiver = BluetoothReceivingTimer(self.window, 0.1)
                self.window.bluetoothReceiver.run()
            else:
                self.window.btChanged.emit(0)
        except bt.BluetoothError as e:
            print(e.args, file=sys.stderr)
            self.window.btError.emit(str(e))


class BluetoothReceivingTimer:

    def __init__(self, parent_window, delay):
        assert isinstance(parent_window, MainWindow)
        self.window = parent_window
        self.interval = delay
        self.timer = Timer(self.interval, self.run)

    def run(self):
        try:
            self.window.bluetoothSocket.setblocking(False)
            try:
                data = self.window.bluetoothSocket.recv(1024)
                self.window.btData.emit(data)
            except bt.BluetoothError as e:
                if int(str(e).lstrip('(').split(',')[0]) != 11:  # Raise errors other than that caused by the non received data
                    raise e
            self.timer = Timer(self.interval, self.run)
            self.timer.start()
        except bt.BluetoothError as e:
            print(e, file=sys.stderr)
            self.window.btError.emit(str(e))

    def stop(self):
        self.timer.cancel()
        self.window.bluetoothSocket.close()
        self.window.btChanged.emit(0)


class MainWindow(QMainWindow, Ui_MainWindow):

    CONNECTION_BUTTON_DISCONNECTED_TEXT = "Déconnecté"
    CONNECTION_BUTTON_CONNECTED_TEXT = "Connecté"
    CONNECTION_BUTTON_SEARCH_TEXT = "Recherche..."
    CONNECTION_BUTTON_CONNECTING_TEXT = "Connexion..."
    CONNECTION_NOT_FOUND_STATUS = "Robot non trouvé !"
    NAVIGATION_STATUS_TEXT = "Navigation..."
    NAVIGATION_START_TEXT = "Démarrer la navigation"
    NAVIGATION_STOP_TEXT = "Arrêter la navigation"
    CAPTURE_STATUS_TEXT = "Capture..."
    CAPTURE_START_TEXT = "Activer la capture"
    CAPTURE_STOP_TEXT = "Désactiver la capture"
    DIRECTION_NONE_TEXT = "Aucune"
    DIRECTION_FORWARD_TEXT = "Avant"
    DIRECTION_BACKWARD_TEXT = "Arrière"
    DIRECTION_RIGHT_TEXT = "Droite"
    DIRECTION_LEFT_TEXT = "Gauche"
    STATUS_MESSAGES_TIMEOUT = 1500
    DISTANCES_REGEXP = re.compile(r'(?:\|(\d+\.\d+))+\|')
    TEMPERATURE_REGEXP = re.compile(r'T(\d+\.\d+)')
    DATA_REGEXP = re.compile(r'C(\d+)')
    SPEED_REGEXP = re.compile(r'P(\d+)')
    NAVIGATE_COMMAND = b'N'
    STOP_COMMAND = b'S'
    PICTURE_COMMAND = b'C'
    POWER_COMMAND = b'P'
    FORWARD_COMMAND = b'F'
    BACKWARD_COMMAND = b'B'
    LEFT_COMMAND = b'L'
    RIGHT_COMMAND = b'R'
    FLASH_COMMAND = b'H'

    btChanged = pyqtSignal(int)
    btError = pyqtSignal(str)
    btData = pyqtSignal(bytes)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.bluetoothSocket = bt.BluetoothSocket(bt.RFCOMM)
        self.bluetoothConnectionThread = BluetoothConnectionThread(self)
        self.bluetoothReceiver = BluetoothReceivingTimer(self, 0.1)

        self.connected = False

        self.keyboardControlTextBrowser.keyPressEvent = self.key_pressed
        self.keyboardControlTextBrowser.keyReleaseEvent = self.key_released

        # Signals
        # Bluetooth connection management
        self.btChanged.connect(self.bluetooth_connection_state_changed)
        self.btError.connect(self.bluetooth_error)
        self.btData.connect(self.bluetooth_data_available)
        self.connectionPushButton.clicked.connect(self.connection_button_clicked)
        # Navigation
        self.navigationPushButton.clicked.connect(self.navigation_button_clicked)
        self.forwardPushButton.pressed.connect(self.move_forward)
        self.forwardPushButton.released.connect(self.stop)
        self.backwardPushButton.pressed.connect(self.move_backward)
        self.backwardPushButton.released.connect(self.stop)
        self.rightPushButton.pressed.connect(self.turn_right)
        self.rightPushButton.released.connect(self.stop)
        self.leftPushButton.pressed.connect(self.turn_left)
        self.leftPushButton.released.connect(self.stop)
        # Power
        self.enginesPowerSlider.valueChanged.connect(self.change_power)
        # Capture
        self.enableCapturePushButton.clicked.connect(self.take_picture_and_distances)
        # Flash
        self.flashPushButton.clicked.connect(self.toggle_flash)

        # Menu actions
        self.showCapturesAction.triggered.connect(self.open_captures_dialog)

        # Window position
        fg = self.frameGeometry()
        fg.moveCenter(QDesktopWidget().availableGeometry().center())
        self.move(fg.topLeft())

    def open_captures_dialog(self):
        directory = QFileDialog.getExistingDirectory(self, "Répertoire de captures", '../')
        if directory:
            dialog = CapturesDialog(self, directory)
            dialog.show()

    def key_pressed(self, key_event):
        if not key_event.isAutoRepeat():
            if key_event.key() == Qt.Key_Up:
                self.move_forward()
            elif key_event.key() == Qt.Key_Down:
                self.move_backward()
            elif key_event.key() == Qt.Key_Right:
                self.turn_right()
            elif key_event.key() == Qt.Key_Left:
                self.turn_left()

    def key_released(self, key_event):
        if not key_event.isAutoRepeat():
            if key_event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Right, Qt.Key_Left):
                self.stop()
            elif key_event.key() == Qt.Key_PageUp:
                self.enginesPowerSlider.setValue(self.enginesPowerSlider.value()+self.enginesPowerSlider.pageStep())
            elif key_event.key() == Qt.Key_PageDown:
                self.enginesPowerSlider.setValue(self.enginesPowerSlider.value()-self.enginesPowerSlider.pageStep())
            elif key_event.key() == Qt.Key_C:
                self.enableCapturePushButton.click()
            elif key_event.key() == Qt.Key_F:
                self.flashPushButton.click()

    def closeEvent(self, close_event):
        self.bluetoothReceiver.stop()

    def connection_button_clicked(self):
        if not self.connected:
            self.bluetoothConnectionThread = BluetoothConnectionThread(self)
            self.bluetoothConnectionThread.start()
        else:
            self.bluetoothReceiver.stop()

    @pyqtSlot(int)
    def bluetooth_connection_state_changed(self, state):
        if state == 3:
            self.connected = True
        elif state == 0:
            self.connected = False
        if state == 3:
            self.connectionPushButton.setText(self.CONNECTION_BUTTON_CONNECTED_TEXT)
            self.statusbar.showMessage(self.CONNECTION_BUTTON_CONNECTED_TEXT, self.STATUS_MESSAGES_TIMEOUT)
            self.stateGroupBox.setEnabled(True)
            self.navigationGroupBox.setEnabled(True)
            self.controlGroupBox.setEnabled(True)
            self.connectionPushButton.setEnabled(True)
        elif state == 0:
            self.connectionPushButton.setText(self.CONNECTION_BUTTON_DISCONNECTED_TEXT)
            self.statusbar.showMessage(self.CONNECTION_BUTTON_DISCONNECTED_TEXT, self.STATUS_MESSAGES_TIMEOUT)
            self.navigationPushButton.setChecked(False)
            self.enableCapturePushButton.setChecked(False)
            self.flashPushButton.setChecked(False)
            self.stateGroupBox.setEnabled(False)
            self.navigationGroupBox.setEnabled(False)
            self.controlGroupBox.setEnabled(False)
            self.enginesPowerSlider.setValue(127)
            self.temperatureLcdNumber.display(0)
            self.dataCountLcdNumber.display(0)
            self.distancesLineEdit.setText('|0.00|0.00|0.00|')
            self.directionLineEdit.setText(self.DIRECTION_NONE_TEXT)
            self.connectionPushButton.setEnabled(True)
        elif state == 1:
            self.connectionPushButton.setText(self.CONNECTION_BUTTON_SEARCH_TEXT)
            self.connectionPushButton.setEnabled(False)
        elif state == 2:
            self.connectionPushButton.setText(self.CONNECTION_BUTTON_CONNECTING_TEXT)
            self.connectionPushButton.setEnabled(False)

    @pyqtSlot(str)
    def bluetooth_error(self, text):
        self.statusbar.showMessage(text, self.STATUS_MESSAGES_TIMEOUT)
        self.btChanged.emit(0)

    @pyqtSlot(bytes)
    def bluetooth_data_available(self, data):
        try:
            text = data.decode()
            if text.startswith('E'):  # Error reported by the smartphone
                self.dataCountLcdNumber.setStyleSheet("*:enabled {color : white; background-color:red;}")
                self.statusbar.setStyleSheet("*:enabled {color : white; background-color:red;}")
                if text == 'EC':
                    self.statusbar.showMessage('Erreur de capture !')
                elif text == 'EM':
                    self.statusbar.showMessage('Erreur de la camera !')
                elif text == 'ES':
                    self.statusbar.showMessage('Erreur de la connexion en série !')
                return
            else:
                self.dataCountLcdNumber.setStyleSheet("")
                self.statusbar.setStyleSheet("")
                self.statusbar.showMessage("")
            match = self.DISTANCES_REGEXP.match(text)
            if match:
                self.distancesLineEdit.setText(match.group())
            else:
                match = self.TEMPERATURE_REGEXP.match(text)
                if match:
                    self.temperatureLcdNumber.display(float(match.group(1)))
                else:
                    match = self.DATA_REGEXP.match(text)
                    if match:
                        self.dataCountLcdNumber.display(int(match.group(1)))
                    else:
                        match = self.SPEED_REGEXP.match(text)
                        if match:
                            self.enginesPowerSlider.setValue(int(match.group(1)))
                        else:
                            STOP = self.STOP_COMMAND.decode()
                            FORWARD = self.FORWARD_COMMAND.decode()
                            BACKWARD = self.BACKWARD_COMMAND.decode()
                            RIGHT = self.RIGHT_COMMAND.decode()
                            LEFT = self.LEFT_COMMAND.decode()
                            if text == STOP:
                                self.directionLineEdit.setText(self.DIRECTION_NONE_TEXT)
                            elif text == FORWARD:
                                self.directionLineEdit.setText(self.DIRECTION_FORWARD_TEXT)
                            elif text == BACKWARD:
                                self.directionLineEdit.setText(self.DIRECTION_BACKWARD_TEXT)
                            elif text == RIGHT:
                                self.directionLineEdit.setText(self.DIRECTION_RIGHT_TEXT)
                            elif text == LEFT:
                                self.directionLineEdit.setText(self.DIRECTION_LEFT_TEXT)
        except UnicodeError as ex:
            print(ex, file=sys.stderr)  # Some garbage

    def navigation_button_clicked(self):
        if self.navigationPushButton.isChecked():
            self.start_navigation()
            self.statusbar.showMessage(self.NAVIGATION_STATUS_TEXT, self.STATUS_MESSAGES_TIMEOUT)
            self.navigationPushButton.setText(self.NAVIGATION_STOP_TEXT)
        else:
            self.stop()
            self.navigationPushButton.setText(self.NAVIGATION_START_TEXT)
        self.controlGroupBox.setDisabled(self.navigationPushButton.isChecked())

    def start_navigation(self):
        self.bluetoothSocket.send(self.NAVIGATE_COMMAND)

    def stop(self):
        self.bluetoothSocket.send(self.STOP_COMMAND)

    def move_forward(self):
        self.bluetoothSocket.send(self.FORWARD_COMMAND)

    def move_backward(self):
        self.bluetoothSocket.send(self.BACKWARD_COMMAND)

    def turn_right(self):
        self.bluetoothSocket.send(self.RIGHT_COMMAND)

    def turn_left(self):
        self.bluetoothSocket.send(self.LEFT_COMMAND)

    def take_picture_and_distances(self):
        self.bluetoothSocket.send(self.PICTURE_COMMAND)
        self.enableCapturePushButton.setText(self.CAPTURE_STOP_TEXT if self.enableCapturePushButton.isChecked() else self.CAPTURE_START_TEXT)
        if self.enableCapturePushButton.isChecked():
            self.statusbar.showMessage(self.CAPTURE_STATUS_TEXT, self.STATUS_MESSAGES_TIMEOUT)

    def change_power(self, power):
        cmd = self.POWER_COMMAND+str(power).encode()
        self.bluetoothSocket.send(cmd)

    def toggle_flash(self):
        self.bluetoothSocket.send(self.FLASH_COMMAND)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
