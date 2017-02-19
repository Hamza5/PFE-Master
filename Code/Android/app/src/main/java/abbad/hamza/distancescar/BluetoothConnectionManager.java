package abbad.hamza.distancescar;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothServerSocket;
import android.bluetooth.BluetoothSocket;
import android.util.Log;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.Arrays;
import java.util.UUID;

class BluetoothConnectionManager {

    private static final UUID DISTANCES_CAR_SERVICE_UUID = UUID.fromString("ad6e04a5-2ae4-4c80-9140-34016e468ee7");
    private static final int BLUETOOTH_BUFFER_SIZE = 1024;
    private static final String FORWARD_COMMAND = "F";
    private static final String BACKWARD_COMMAND = "B";
    private static final String LEFT_COMMAND = "L";
    private static final String RIGHT_COMMAND = "R";
    private static final String POWER_COMMAND = "P";
    private static final String PICTURE_COMMAND = "C";
    private static final String MOVING_COMMAND = "M";
    private static final String NAVIGATE_COMMAND = "N";
    private static final String STOP_COMMAND = "S";

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
                Log.i(BluetoothConnectionManager.class.getName(), "Waiting for a client to connect");
                computerSocket = smartphoneSocket.accept();
                smartphoneSocket.close();
                Log.i(BluetoothConnectionManager.class.getName(), "Client connected");
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
                            final String command = new String(Arrays.copyOfRange(buffer, 0, bytesCount));
                            switch (command) {
                                case FORWARD_COMMAND:
                                    mainActivity.serialConnectionManager.moveForward();
                                    break;
                                case BACKWARD_COMMAND:
                                    mainActivity.serialConnectionManager.moveBackward();
                                case LEFT_COMMAND:
                                    mainActivity.serialConnectionManager.turnLeft();
                                    break;
                                case RIGHT_COMMAND:
                                    mainActivity.serialConnectionManager.turnRight();
                                    break;
                                case PICTURE_COMMAND:
                                    mainActivity.captureManager.takePicture();
                                    break;
                                case NAVIGATE_COMMAND:
                                    mainActivity.serialConnectionManager.startNavigation();
                                    mainActivity.taskHandler.postDelayed(new CapturingTask(mainActivity, mainActivity.taskHandler), CapturingTask.TASK_REPEATING_FREQUENCY);
                                    break;
                                case STOP_COMMAND:
                                    mainActivity.taskHandler.removeCallbacksAndMessages(null);
                                    mainActivity.serialConnectionManager.stop();
                                    break;
                                default:
                                if (command.startsWith(POWER_COMMAND)) {
                                    final int power = Integer.parseInt(command.substring(POWER_COMMAND.length()));
                                    mainActivity.runOnUiThread(new Runnable() {
                                        @Override
                                        public void run() {
                                            mainActivity.powerSeekBar.setProgress(power);
                                        }
                                    });
                                } else if (command.startsWith(MOVING_COMMAND)) {
                                    final int move_delay = Integer.parseInt(command.substring(MOVING_COMMAND.length()));
                                    mainActivity.runOnUiThread(new Runnable() {
                                        @Override
                                        public void run() {
                                            mainActivity.delayEditText.setText(String.valueOf(move_delay));
                                        }
                                    });
                                } else
                                    mainActivity.serialConnectionManager.sendSerialData(command.getBytes());
                            }
                        }
                    }
                } catch (IOException ignored) { }
                bluetoothInput.close();
                bluetoothInput = null;
                bluetoothOutput.close();
                bluetoothOutput = null;
                computerSocket.close();
                computerSocket = null;
                Log.i(BluetoothConnectionManager.class.getName(), "Client disconnected");
                mainActivity.setBluetoothConnectionStatus(false);
            } catch (IOException ex) {
                String errorMessage = mainActivity.getString(R.string.bluetooth_stream_error);
                mainActivity.showMessage(errorMessage);
                Log.e(BluetoothConnectionManager.class.getName(), errorMessage);
            }
        }

    }

    void sendToComputer(byte[] data) {
        if (bluetoothOutput != null)
            try {
                bluetoothOutput.write(data);
            } catch (IOException ex) {
                String errorMessage = mainActivity.getString(R.string.bluetooth_stream_error);
                mainActivity.showMessage(errorMessage);
                Log.e(getClass().getName(), errorMessage);
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
