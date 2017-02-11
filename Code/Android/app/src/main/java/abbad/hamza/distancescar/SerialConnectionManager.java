package abbad.hamza.distancescar;

import android.hardware.usb.UsbDevice;
import android.hardware.usb.UsbDeviceConnection;
import android.hardware.usb.UsbManager;
import android.os.AsyncTask;

import com.felhr.usbserial.UsbSerialDevice;
import com.felhr.usbserial.UsbSerialInterface;

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

class SerialConnectionManager {

    private static final int SERIAL_BAUD_RATE = 9600;
    private static final List<Integer> VENDOR_IDS = Arrays.asList(1027, 9025, 5824, 4292, 1659, 6790);
    private static final Pattern DISTANCES_REGEXP = Pattern.compile("\\|([0-9]+\\.[0-9]+)\\|([0-9]+\\.[0-9]+)\\|([0-9]+\\.[0-9]+)\\|");
    private static final Pattern TEMPERATURE_REGEXP = Pattern.compile("T([0-9]+\\.[0-9]+)");

    private UsbManager usbManager;
    private UsbDeviceConnection arduinoSerialConnection;
    private UsbSerialDevice arduinoSerialPort;
    private MainActivity mainActivity;

    SerialConnectionManager(MainActivity parent, UsbManager usbDevicesManager) {
        mainActivity = parent;
        usbManager = usbDevicesManager;
    }

    private UsbSerialInterface.UsbReadCallback serialReadCallback = new UsbSerialInterface.UsbReadCallback() {
        @Override
        public void onReceivedData(byte[] bytes) {
            String response = new String(bytes);
            Matcher m;
            m = DISTANCES_REGEXP.matcher(response);
            if (m.find()) {
                mainActivity.updateDistance(new float[]{Float.parseFloat(m.group(1)), Float.parseFloat(m.group(2)), Float.parseFloat(m.group(3))});
            }
            m = TEMPERATURE_REGEXP.matcher(response);
            if (m.find()) {
                mainActivity.updateTemperature(Float.parseFloat(m.group(1)));
            }
            mainActivity.bluetoothConnectionManager.sendToComputer(bytes);
        }
    };

    void sendSerialData(byte[] data) {
        if (arduinoSerialPort != null)
            arduinoSerialPort.write(data);
        else mainActivity.showMessage(mainActivity.getString(R.string.serial_no_port));
    }

    UsbDevice getConnectedUSBDevice() {
        HashMap<String, UsbDevice> usbDevices = usbManager.getDeviceList();
        for (UsbDevice device : usbDevices.values())
            if (VENDOR_IDS.contains(device.getVendorId()))
                return device;
        return null;
    }

    void openSerialConnection(UsbDevice device) {
        AsyncTask<UsbDevice, Void, Boolean> deviceInitialisation = new AsyncTask<UsbDevice, Void, Boolean>() {
            @Override
            protected Boolean doInBackground(UsbDevice... devices) {
                UsbDevice device = devices[0];
                arduinoSerialConnection = usbManager.openDevice(device);
                if (arduinoSerialConnection == null) mainActivity.showMessage("USB connection failed");
                arduinoSerialPort = UsbSerialDevice.createUsbSerialDevice(device, arduinoSerialConnection);
                if (arduinoSerialPort == null) mainActivity.showMessage(mainActivity.getString(R.string.serial_driver_not_found));
                else{
                    if (arduinoSerialPort.open()) {
                        arduinoSerialPort.setBaudRate(SERIAL_BAUD_RATE);
                        arduinoSerialPort.setDataBits(UsbSerialInterface.DATA_BITS_8);
                        arduinoSerialPort.setParity(UsbSerialInterface.PARITY_NONE);
                        arduinoSerialPort.setStopBits(UsbSerialInterface.STOP_BITS_1);
                        arduinoSerialPort.setFlowControl(UsbSerialInterface.FLOW_CONTROL_OFF);
                        arduinoSerialPort.read(serialReadCallback);
                        return true;
                    } else mainActivity.showMessage("USB serial port opening failed");
                }
                return false;
            }
            @Override
            protected void onPostExecute(Boolean connectionOpened) {
                if (!connectionOpened) mainActivity.showMessage(mainActivity.getString(R.string.serial_open_error));
                else mainActivity.serialConnectionOpened();
            }
        };
        deviceInitialisation.execute(device);
    }

    void closeConnection() {
        if (arduinoSerialPort != null) {
            arduinoSerialPort.close();
            arduinoSerialPort = null;
            arduinoSerialConnection.close();
        }
    }

    void setEnginesPower(int power) {
        sendSerialData(("P"+power).getBytes());
    }

    void requestDistances() {
        sendSerialData("D".getBytes());
    }

    void requestTemperature() {
        sendSerialData("T".getBytes());
    }

    void moveForward(int milliseconds) {
        sendSerialData(("F"+milliseconds).getBytes());
    }

    void moveBackward(int milliseconds) {
        sendSerialData(("B"+milliseconds).getBytes());
    }

    void turnLeft(int milliseconds) {
        sendSerialData(("L"+milliseconds).getBytes());
    }

    void turnRight(int milliseconds) {
        sendSerialData(("R"+milliseconds).getBytes());
    }

}
