package abbad.hamza.distancescar;

import android.hardware.usb.UsbDevice;
import android.hardware.usb.UsbDeviceConnection;
import android.hardware.usb.UsbManager;
import android.os.AsyncTask;
import android.util.Log;

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
                float[] distances = new float[]{Float.parseFloat(m.group(1)), Float.parseFloat(m.group(2)), Float.parseFloat(m.group(3))};
                float min = Math.min(Math.min(distances[0], distances[1]), distances[2]);
                mainActivity.updateDistance(min);
                CapturingTask.Distance distance = new CapturingTask.Distance(distances);
                CapturingTask.distancesQueue.add(distance);
            }
            m = TEMPERATURE_REGEXP.matcher(response);
            if (m.find()) {
                mainActivity.updateTemperature(Float.parseFloat(m.group(1)));
            }
            Log.i(SerialConnectionManager.class.getName(), response);
        }
    };

    void sendSerialData(byte[] data) {
        if (arduinoSerialPort != null) {
            arduinoSerialPort.write(data);
        }
        else {
            String errorMessage = mainActivity.getString(R.string.serial_no_port);
            mainActivity.showMessage(errorMessage);
            Log.e(getClass().getName(), errorMessage);
        }
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
                if (arduinoSerialConnection == null) mainActivity.showMessage(mainActivity.getString(R.string.serial_open_error));
                arduinoSerialPort = UsbSerialDevice.createUsbSerialDevice(device, arduinoSerialConnection);
                if (arduinoSerialPort == null) mainActivity.showMessage(mainActivity.getString(R.string.serial_driver_not_found));
                else {
                    if (arduinoSerialPort.open()) {
                        arduinoSerialPort.setBaudRate(SERIAL_BAUD_RATE);
                        arduinoSerialPort.setDataBits(UsbSerialInterface.DATA_BITS_8);
                        arduinoSerialPort.setParity(UsbSerialInterface.PARITY_NONE);
                        arduinoSerialPort.setStopBits(UsbSerialInterface.STOP_BITS_1);
                        arduinoSerialPort.setFlowControl(UsbSerialInterface.FLOW_CONTROL_OFF);
                        arduinoSerialPort.read(serialReadCallback);
                        return true;
                    } else mainActivity.showMessage(mainActivity.getString(R.string.serial_open_error));
                }
                return false;
            }
            @Override
            protected void onPostExecute(Boolean connectionOpened) {
                if (!connectionOpened) mainActivity.showMessage(mainActivity.getString(R.string.serial_open_error));
                else {
                    Log.i(SerialConnectionManager.class.getName(), "Serial opened");
                    mainActivity.serialConnectionOpened();
                }
            }
        };
        deviceInitialisation.execute(device);
    }

    void closeConnection() {
        if (arduinoSerialPort != null) {
            arduinoSerialPort.close();
            arduinoSerialPort = null;
            Log.i(SerialConnectionManager.class.getName(), "Serial closed");
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

    void moveForward() {
        sendSerialData("F".getBytes());
    }

    void moveBackward() {
        sendSerialData("B".getBytes());
    }

    void turnLeft() {
        sendSerialData("L".getBytes());
    }

    void turnRight() {
        sendSerialData("R".getBytes());
    }

    void stop() {
        sendSerialData("S".getBytes());
    }

}
