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
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

class SerialConnectionManager {

    private static final float NEEDED_TURN_DISTANCE = 0.2f;
    private static final float NEEDED_FORWARD_DISTANCE = 0.5f;
    private static final float UNKNOWN_DISTANCE = 9.99f;
    private static final int SERIAL_BAUD_RATE = 9600;
    private static final List<Integer> VENDOR_IDS = Arrays.asList(1027, 9025, 5824, 4292, 1659, 6790);
    private static final Pattern DISTANCES_REGEXP = Pattern.compile("(?:\\|([0-9]+\\.[0-9]+))+\\|");
    private static final Pattern TEMPERATURE_REGEXP = Pattern.compile("T([0-9]+\\.[0-9]+)");
    private static final Pattern SPEED_REGEXP = Pattern.compile("P([0-9]+)");

    private UsbManager usbManager;
    private UsbDeviceConnection arduinoSerialConnection;
    private UsbSerialDevice arduinoSerialPort;
    private MainActivity mainActivity;
    private boolean right;
    AtomicBoolean navigation = new AtomicBoolean(false);

    SerialConnectionManager(MainActivity parent, UsbManager usbDevicesManager) {
        mainActivity = parent;
        usbManager = usbDevicesManager;
        right = false;
    }

    private UsbSerialInterface.UsbReadCallback serialReadCallback = new UsbSerialInterface.UsbReadCallback() {
        @Override
        public void onReceivedData(byte[] bytes) {
            String response = new String(bytes);
            Matcher m;
            m = DISTANCES_REGEXP.matcher(response);
            if (m.find()) {
                String[] distancesStrings = m.group().substring(1, m.group().length()-1).split("\\|");
                float[] distances = new float[distancesStrings.length];
                for (int i = 0; i < distances.length; i++) {
                    distances[i] = Float.parseFloat(distancesStrings[i]);
                    if (distances[i] == 0) distances[i] = UNKNOWN_DISTANCE;
                }
                CapturingTask.Distance distance = new CapturingTask.Distance(distances);
                mainActivity.updateDistance(distance);
                CapturingTask.distancesQueue.add(distance);
                Log.i(SerialConnectionManager.class.getName(), "Distances received in "+(System.currentTimeMillis()-CapturingTask.lastDistancesRequest.get())+"ms");
                mainActivity.bluetoothConnectionManager.sendToComputer(m.group().getBytes());
                if (navigation.get())
                    navigate(distance);
            } else {
                m = TEMPERATURE_REGEXP.matcher(response);
                if (m.find()) {
                    float temp = Float.parseFloat(m.group(1));
                    mainActivity.updateTemperature(temp);
                    mainActivity.bluetoothConnectionManager.sendToComputer(m.group().getBytes());
                } else {
                    m = SPEED_REGEXP.matcher(response);
                    if (m.find()) {
                        mainActivity.bluetoothConnectionManager.sendToComputer(m.group().getBytes());
                    }
                }
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
            mainActivity.bluetoothConnectionManager.sendToComputer("ES".getBytes());
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
                if (arduinoSerialConnection == null) {
                    String errorMessage = mainActivity.getString(R.string.serial_open_error);
                    mainActivity.showMessage(errorMessage);
                    Log.e(SerialConnectionManager.class.getName(), errorMessage);
                    mainActivity.bluetoothConnectionManager.sendToComputer("ES".getBytes());
                    return false;
                }
                arduinoSerialPort = UsbSerialDevice.createUsbSerialDevice(device, arduinoSerialConnection);
                if (arduinoSerialPort == null) {
                    String errorMessage = mainActivity.getString(R.string.serial_driver_not_found);
                    mainActivity.showMessage(errorMessage);
                    Log.e(SerialConnectionManager.class.getName(), errorMessage);
                    mainActivity.bluetoothConnectionManager.sendToComputer("ES".getBytes());
                }
                else {
                    if (arduinoSerialPort.open()) {
                        arduinoSerialPort.setBaudRate(SERIAL_BAUD_RATE);
                        arduinoSerialPort.setDataBits(UsbSerialInterface.DATA_BITS_8);
                        arduinoSerialPort.setParity(UsbSerialInterface.PARITY_NONE);
                        arduinoSerialPort.setStopBits(UsbSerialInterface.STOP_BITS_1);
                        arduinoSerialPort.setFlowControl(UsbSerialInterface.FLOW_CONTROL_OFF);
                        arduinoSerialPort.read(serialReadCallback);
                        return true;
                    } else {
                        String errorMessage = mainActivity.getString(R.string.serial_open_error);
                        mainActivity.showMessage(errorMessage);
                        Log.e(SerialConnectionManager.class.getName(), errorMessage);
                        mainActivity.bluetoothConnectionManager.sendToComputer("ES".getBytes());
                    }
                }
                return false;
            }
            @Override
            protected void onPostExecute(Boolean connectionOpened) {
                if (connectionOpened) {
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
            arduinoSerialConnection.close();
            Log.i(SerialConnectionManager.class.getName(), "Serial closed");
        }
    }

    void setEnginesPower(int power) {
        sendSerialData(("P"+power).getBytes());
    }

    void requestDistances() {
        CapturingTask.lastDistancesRequest.set(System.currentTimeMillis());
        sendSerialData("D".getBytes());
    }

    void requestTemperature() {
        sendSerialData("T".getBytes());
    }

    void moveForward() {
        byte[] direction = "F".getBytes();
        sendSerialData(direction);
        mainActivity.bluetoothConnectionManager.sendToComputer(direction);
    }

    void moveBackward() {
        byte[] direction = "B".getBytes();
        sendSerialData(direction);
        mainActivity.bluetoothConnectionManager.sendToComputer(direction);
    }

    void turnLeft() {
        byte[] direction = "L".getBytes();
        sendSerialData(direction);
        mainActivity.bluetoothConnectionManager.sendToComputer(direction);
    }

    void turnRight() {
        byte[] direction = "R".getBytes();
        sendSerialData(direction);
        mainActivity.bluetoothConnectionManager.sendToComputer(direction);
    }

    void stop() {
        byte[] direction = "S".getBytes();
        sendSerialData(direction);
        mainActivity.bluetoothConnectionManager.sendToComputer(direction);
    }

    private void navigate(CapturingTask.Distance d) {
//        int center = (d.dists.length+1)/2;
//        float centerAverage = (d.dists[center] + d.dists[center-1] + d.dists[center+1]) / 3;
//        if (centerAverage < NEEDED_TURN_DISTANCE) {
//            mainActivity.serialConnectionManager.moveBackward();
//        } else {
//            float deviation = 0;
//            for (int i = 0; i < d.dists.length; i++) {
//                deviation += (i+1) * d.dists[i];
//            }
//            deviation /= d.dists.length;
//            if (deviation < d.dists.length/3f)
//                turnRight();
//            else if (deviation > d.dists.length*2/3f)
//                turnLeft();
//            else
//                moveForward();
//        }
        float min = minimumDistances(d.dists);
        if (min != 0) {
            if (min < NEEDED_TURN_DISTANCE) {
                moveBackward();
                right = Math.random() > 0.5;
            }
            else if (min < NEEDED_FORWARD_DISTANCE) {
                if (right) turnRight();
                else turnLeft();
            }
            else moveForward();
        }
    }

    private float trueDistancesAverage(float[] data) {
        int valid = 0;
        float sum = 0;
        for (float f : data)
            if (f != UNKNOWN_DISTANCE) {
                sum += f;
                valid++;
            }
        if (valid != 0)
            return sum / valid;
        else
            return 0;
    }

    private float minimumDistances(float[] data) {
        float min = data[0];
        for (int i=1; i<data.length; i++)
            if (data[i] < min) min = data[i];
        return min;
    }

    void setNavigation(boolean enabled) {
        navigation.set(enabled);
        if (!navigation.get()) stop();
    }

}
