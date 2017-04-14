import csv
import os
import re
import sys

from PyQt5.QtBluetooth import QBluetoothSocket, QBluetoothServiceDiscoveryAgent, QBluetoothUuid, QBluetoothServiceInfo, QBluetoothLocalDevice
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDesktopWidget
from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog, QFileDialog
from PyQt5.QtCore import Qt, QDateTime

from GUI.DistancesCarRemoteControler import Ui_MainWindow
from GUI.CapturesDialog import Ui_CapturesDialog


class CapturesDialog(QDialog, Ui_CapturesDialog):

    DISTANCES_FILENAME = "Distances.txt"

    def __init__(self, parent, directory):
        super(CapturesDialog, self).__init__(parent)
        self.setupUi(self)
        self.distances = []
        self.dir = directory
        with open(os.path.join(directory, self.DISTANCES_FILENAME), newline='') as distancesFile:
            self.distances = [line for line in csv.reader(distancesFile)]
        self.setCapturesCount(len(self.distances))
        self.captureNumberSpinBox.valueChanged.connect(self.setCurrentCapture)
        self.captureNumberSpinBox.setValue(1)
        self.captureNumberSpinBox.setMinimum(1)

    def setCapturesCount(self, count):
        self.captureNumberSpinBox.setMaximum(count)
        self.capturesCountLcdNumber.display(count)

    def setCurrentCapture(self, captureNumber):
        capture_id = self.distances[captureNumber-1][0]
        capture_filename = 'IMG_{}.jpg'.format(capture_id)
        capture = QPixmap(os.path.join(self.dir, capture_filename))
        self.captureViewLabel.setPixmap(capture)
        self.captureDateTimeEdit.setDateTime(QDateTime.fromMSecsSinceEpoch(int(capture_id)))
        self.distancesLineEdit.setText('|'+'|'.join(self.distances[captureNumber-1][1:])+'|')


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
    DISTANCES_CAR_BLUETOOTH_SERVICE_UUID = "ad6e04a5-2ae4-4c80-9140-34016e468ee7"
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
    FLASH_COMMMAND = b'H'

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.bluetoothDevice = QBluetoothLocalDevice(self)
        self.bluetoothSocket = QBluetoothSocket(QBluetoothServiceInfo.RfcommProtocol, self)
        self.bluetoothDiscoveryAgent = QBluetoothServiceDiscoveryAgent(self)
        self.bluetoothDiscoveryAgent.setUuidFilter(QBluetoothUuid(self.DISTANCES_CAR_BLUETOOTH_SERVICE_UUID))
        self.bluetoothDiscoveryAgent.finished.connect(self.bluetoothDiscoveryFinished)

        self.keyboardControlTextBrowser.keyPressEvent = self.keyPressed
        self.keyboardControlTextBrowser.keyReleaseEvent = self.keyReleased

        # Signals
        # Bluetooth connection management
        self.connectionPushButton.clicked.connect(self.connectionButtonClicked)
        self.bluetoothSocket.connected.connect(self.bluetoothConnected)
        self.bluetoothSocket.disconnected.connect(self.bluetoothConnected)
        self.bluetoothSocket.error.connect(self.bluetoothError)
        self.bluetoothSocket.readyRead.connect(self.bluetoothDataAvailable)
        # Navigation
        self.navigationPushButton.clicked.connect(self.navigationButtonClicked)
        self.forwardPushButton.pressed.connect(self.moveForward)
        self.forwardPushButton.released.connect(self.stop)
        self.backwardPushButton.pressed.connect(self.moveBackward)
        self.backwardPushButton.released.connect(self.stop)
        self.rightPushButton.pressed.connect(self.turnRight)
        self.rightPushButton.released.connect(self.stop)
        self.leftPushButton.pressed.connect(self.turnLeft)
        self.leftPushButton.released.connect(self.stop)
        # Power
        self.enginesPowerSlider.valueChanged.connect(self.changePower)
        # Capture
        self.enableCapturePushButton.clicked.connect(self.takePictureAndDistances)
        # Flash
        self.flashPushButton.clicked.connect(self.toggleFlash)

        # Menu actions
        self.showCapturesAction.triggered.connect(self.openCapturesDialog)

        # Window position
        fg = self.frameGeometry()
        fg.moveCenter(QDesktopWidget().availableGeometry().center())
        self.move(fg.topLeft())

    def openCapturesDialog(self):
        directory = QFileDialog.getExistingDirectory(self, "Répertoire de captures", '../')
        if directory:
            dialog = CapturesDialog(self, directory)
            dialog.show()

    def keyPressed(self, QKeyEvent):
        if not QKeyEvent.isAutoRepeat():
            if QKeyEvent.key() == Qt.Key_Up:
                self.moveForward()
            elif QKeyEvent.key() == Qt.Key_Down:
                self.moveBackward()
            elif QKeyEvent.key() == Qt.Key_Right:
                self.turnRight()
            elif QKeyEvent.key() == Qt.Key_Left:
                self.turnLeft()

    def keyReleased(self, QKeyEvent):
        if not QKeyEvent.isAutoRepeat():
            if QKeyEvent.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Right, Qt.Key_Left):
                self.stop()
            elif QKeyEvent.key() == Qt.Key_PageUp:
                self.enginesPowerSlider.setValue(self.enginesPowerSlider.value()+self.enginesPowerSlider.pageStep())
            elif QKeyEvent.key() == Qt.Key_PageDown:
                self.enginesPowerSlider.setValue(self.enginesPowerSlider.value()-self.enginesPowerSlider.pageStep())
            elif QKeyEvent.key() == Qt.Key_C:
                self.enableCapturePushButton.click()
            elif QKeyEvent.key() == Qt.Key_F:
                self.flashPushButton.click()

    def connectionButtonClicked(self):
        if self.bluetoothSocket.state() == QBluetoothSocket.UnconnectedState:
            if self.bluetoothDevice.hostMode() == QBluetoothLocalDevice.HostPoweredOff:
                self.bluetoothDevice.powerOn()  # This may not work, but let's try it anyway !
            self.connectionPushButton.setEnabled(False)
            self.connectionPushButton.setText(self.CONNECTION_BUTTON_SEARCH_TEXT)
            self.bluetoothDiscoveryAgent.start()
        else:
            self.bluetoothSocket.disconnectFromService()

    def bluetoothDiscoveryFinished(self):
        services = self.bluetoothDiscoveryAgent.discoveredServices()
        if len(services) == 0:
            self.connectionPushButton.setText(self.CONNECTION_BUTTON_DISCONNECTED_TEXT)
            self.statusbar.showMessage(self.CONNECTION_NOT_FOUND_STATUS, self.STATUS_MESSAGES_TIMEOUT)
            self.connectionPushButton.setEnabled(True)
        else:
            self.connectionPushButton.setText(self.CONNECTION_BUTTON_CONNECTING_TEXT)
            self.bluetoothSocket.connectToService(services[0])

    def bluetoothConnected(self):
        self.connectionPushButton.setEnabled(True)
        if self.bluetoothSocket.state() == QBluetoothSocket.ConnectedState:
            self.connectionPushButton.setText(self.CONNECTION_BUTTON_CONNECTED_TEXT)
            self.statusbar.showMessage(self.CONNECTION_BUTTON_CONNECTED_TEXT, self.STATUS_MESSAGES_TIMEOUT)
            self.stateGroupBox.setEnabled(True)
            self.navigationGroupBox.setEnabled(True)
            self.controlGroupBox.setEnabled(True)
        else:
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
            self.distancesLineEdit.setText('|0.00|0.00|0.00|0.00|0.00|0.00|0.00|')
            self.directionLineEdit.setText(self.DIRECTION_NONE_TEXT)

    def bluetoothError(self):
        self.statusbar.showMessage(self.bluetoothSocket.errorString(), self.STATUS_MESSAGES_TIMEOUT)
        self.connectionPushButton.setText(self.CONNECTION_BUTTON_DISCONNECTED_TEXT)
        self.connectionPushButton.setEnabled(True)

    def bluetoothDataAvailable(self):
        data = self.bluetoothSocket.readAll()
        try:
            text = bytes(data).decode()
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

    def navigationButtonClicked(self):
        if self.navigationPushButton.isChecked():
            self.startNavigation()
            self.statusbar.showMessage(self.NAVIGATION_STATUS_TEXT, self.STATUS_MESSAGES_TIMEOUT)
            self.navigationPushButton.setText(self.NAVIGATION_STOP_TEXT)
        else:
            self.stop()
            self.navigationPushButton.setText(self.NAVIGATION_START_TEXT)
        self.controlGroupBox.setDisabled(self.navigationPushButton.isChecked())

    def startNavigation(self):
        self.bluetoothSocket.write(self.NAVIGATE_COMMAND)

    def stop(self):
        self.bluetoothSocket.write(self.STOP_COMMAND)

    def moveForward(self):
        self.bluetoothSocket.write(self.FORWARD_COMMAND)

    def moveBackward(self):
        self.bluetoothSocket.write(self.BACKWARD_COMMAND)

    def turnRight(self):
        self.bluetoothSocket.write(self.RIGHT_COMMAND)

    def turnLeft(self):
        self.bluetoothSocket.write(self.LEFT_COMMAND)

    def takePictureAndDistances(self):
        self.bluetoothSocket.write(self.PICTURE_COMMAND)
        self.enableCapturePushButton.setText(self.CAPTURE_STOP_TEXT if self.enableCapturePushButton.isChecked() else self.CAPTURE_START_TEXT)
        if self.enableCapturePushButton.isChecked():
            self.statusbar.showMessage(self.CAPTURE_STATUS_TEXT, self.STATUS_MESSAGES_TIMEOUT)

    def changePower(self, power):
        cmd = self.POWER_COMMAND+str(power).encode()
        self.bluetoothSocket.write(cmd)

    def toggleFlash(self):
        self.bluetoothSocket.write(self.FLASH_COMMMAND)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
