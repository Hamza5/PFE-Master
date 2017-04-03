import re
import sys

from PyQt5.QtBluetooth import QBluetoothSocket, QBluetoothServiceDiscoveryAgent, QBluetoothUuid, QBluetoothServiceInfo, QBluetoothLocalDevice
from PyQt5.QtWidgets import QDesktopWidget
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import Qt

from GUI.DistancesCarRemoteControler import Ui_MainWindow


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
    DISTANCES_CAR_BLUETOOTH_SERVICE_UUID = "ad6e04a5-2ae4-4c80-9140-34016e468ee7"
    STATUS_MESSAGES_TIMEOUT = 1500
    DISTANCES_REGEXP = re.compile(r'(?:\|(\d+\.\d+))+\|')
    TEMPERATURE_REGEXP = re.compile(r'T(\d+\.\d+)')
    DATA_REGEXP = re.compile(r'C(\d+)')
    NAVIGATE_COMMAND = b'N'
    STOP_COMMAND = b'S'
    PICTURE_COMMAND = b'C'
    POWER_COMMAND = b'P'
    FORWARD_COMMAND = b'F'
    BACKWARD_COMMAND = b'B'
    LEFT_COMMAND = b'L'
    RIGHT_COMMAND = b'R'

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

        # Window position
        fg = self.frameGeometry()
        fg.moveCenter(QDesktopWidget().availableGeometry().center())
        self.move(fg.topLeft())

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
            self.stateGroupBox.setEnabled(False)
            self.navigationGroupBox.setEnabled(False)
            self.controlGroupBox.setEnabled(False)
            self.enginesPowerSlider.setValue(127)
            self.temperatureLcdNumber.display(0)
            self.dataCountLcdNumber.display(0)
            self.distancesLineEdit.setText('|0.00|0.00|0.00|0.00|0.00|0.00|')

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
