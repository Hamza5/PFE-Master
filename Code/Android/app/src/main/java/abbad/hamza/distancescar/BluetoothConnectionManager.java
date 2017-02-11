package abbad.hamza.distancescar;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothServerSocket;
import android.bluetooth.BluetoothSocket;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.Arrays;
import java.util.UUID;

class BluetoothConnectionManager {

    private static final UUID DISTANCES_CAR_SERVICE_UUID = UUID.fromString("ad6e04a5-2ae4-4c80-9140-34016e468ee7");
    private static final int BLUETOOTH_BUFFER_SIZE = 1024;

    private BluetoothSocket computerSocket;
    private InputStream bluetoothInput;
    private OutputStream bluetoothOutput;
    private MainActivity mainActivity;
    private BluetoothAdapter bluetoothAdapter;
    private BluetoothReceivingThread receivingThread;
    private BluetoothServerInitialisationThread initialisationThread;

    BluetoothConnectionManager(MainActivity parent, BluetoothAdapter adapter) {
        mainActivity = parent;
        bluetoothAdapter = adapter;
        initialisationThread = new BluetoothServerInitialisationThread();
        receivingThread = new BluetoothReceivingThread();
    }

    private class BluetoothServerInitialisationThread extends Thread {

        @Override
        public void run() {
            try {
                BluetoothServerSocket smartphoneSocket = bluetoothAdapter.listenUsingRfcommWithServiceRecord(mainActivity.getString(R.string.bluetooth_socket_name), DISTANCES_CAR_SERVICE_UUID);
                computerSocket = smartphoneSocket.accept();
                smartphoneSocket.close();
                receivingThread = new BluetoothReceivingThread();
                receivingThread.start();
            } catch (IOException ignored) {
                // Happens when the server is closed with no client connected
            }
        }

    }

    private class BluetoothReceivingThread extends Thread {

        @Override
        public void run() {
            try {
                byte[] buffer = new byte[BLUETOOTH_BUFFER_SIZE];
                int bytesCount;
                try {
                    bluetoothInput = computerSocket.getInputStream();
                    bluetoothOutput = computerSocket.getOutputStream();
                    mainActivity.setBluetoothConnectionStatus(true);
                    while (!isInterrupted()) {
                        bytesCount = bluetoothInput.read(buffer);
                        if (bytesCount > 0) {
                            byte[] info = Arrays.copyOfRange(buffer, 0, bytesCount);
                            mainActivity.serialConnectionManager.sendSerialData(info);
                        }
                    }
                } catch (IOException ignored) { }
                bluetoothInput.close();
                bluetoothInput = null;
                bluetoothOutput.close();
                bluetoothOutput = null;
                computerSocket.close();
                computerSocket = null;
                mainActivity.setBluetoothConnectionStatus(false);
                if (!isInterrupted()) {
                    initialisationThread = new BluetoothServerInitialisationThread();
                    initialisationThread.start();
                }
            } catch (IOException ex) {
                mainActivity.showMessage(mainActivity.getString(R.string.bluetooth_stream_error));
            }
        }

    }

    void sendToComputer(byte[] data) {
        if (bluetoothOutput != null)
            try {
                bluetoothOutput.write(data);
            } catch (IOException ex) {
                mainActivity.showMessage(mainActivity.getString(R.string.bluetooth_stream_error));
            }
    }

    void startServer() {
        initialisationThread = new BluetoothServerInitialisationThread();
        initialisationThread.start();
    }

    void stopServer() {
        initialisationThread.interrupt();
    }

    void stopReceiving() {
        receivingThread.interrupt();
    }

    boolean isWaiting() {
        return initialisationThread.isAlive();
    }

    boolean isReceiving() {
        return receivingThread.isAlive();
    }

    boolean isRunning() {
        return isWaiting() || isReceiving();
    }

}
