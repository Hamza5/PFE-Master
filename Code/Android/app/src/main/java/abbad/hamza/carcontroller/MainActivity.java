package abbad.hamza.carcontroller;

import android.app.Activity;
import android.app.PendingIntent;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothServerSocket;
import android.bluetooth.BluetoothSocket;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.hardware.usb.UsbDevice;
import android.hardware.usb.UsbDeviceConnection;
import android.hardware.usb.UsbManager;
import android.os.AsyncTask;
import android.os.Bundle;
import android.view.View;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import com.felhr.usbserial.UsbSerialDevice;
import com.felhr.usbserial.UsbSerialInterface;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Locale;
import java.util.UUID;

public class MainActivity extends Activity {

    private static final String USB_PERMISSION = "abbad.hamza.permission.USB_PERMISSION";
    private static final String USB_DEVICE = "abbad.hamza.action.USB_DEVICE";
    private static final UUID DISTANCES_CAR_SERVICE_UUID = UUID.fromString("ad6e04a5-2ae4-4c80-9140-34016e468ee7");
    private static final int BLUETOOTH_DISCOVERABILITY_DURATION = 60;
    private static final int BLUETOOTH_BUFFER_SIZE = 1024;
    private static final int SERIAL_BAUD_RATE = 9600;

    private TextView logView;
    private EditText commandInput;
//    private Camera camera;
//    private SurfaceHolder cameraSurfaceHolder;
    private UsbManager usbManager;
    private UsbSerialDevice arduinoSerialPort;
    private BluetoothAdapter bluetoothAdapter;
    private BluetoothTransmissionThread bluetoothTransmissionThread;
    private boolean bluetoothServerStarted;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
//        cameraSurfaceHolder = ((SurfaceView) findViewById(R.id.surfaceView)).getHolder();
        logView = (TextView) findViewById(R.id.logTextView);
        commandInput = (EditText) findViewById(R.id.messageEditText);
        usbManager = (UsbManager) getSystemService(USB_SERVICE);
        bluetoothServerStarted = false;
        bluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
        if (bluetoothAdapter == null) {
            showMessage(getString(R.string.bluetooth_adapter_error));
            finish();
        }

        // USB serial connection
        IntentFilter usbDeviceIntents = new IntentFilter();
        usbDeviceIntents.addAction(USB_PERMISSION);
        usbDeviceIntents.addAction(UsbManager.ACTION_USB_DEVICE_ATTACHED);
        usbDeviceIntents.addAction(UsbManager.ACTION_USB_DEVICE_DETACHED);
        registerReceiver(usbEventsReceiver, usbDeviceIntents);

        // Bluetooth connection
        IntentFilter bluetoothIntents = new IntentFilter();
        bluetoothIntents.addAction(BluetoothAdapter.ACTION_STATE_CHANGED);
        bluetoothIntents.addAction(BluetoothAdapter.ACTION_SCAN_MODE_CHANGED);
        bluetoothIntents.addAction(BluetoothAdapter.ACTION_CONNECTION_STATE_CHANGED);
        registerReceiver(bluetoothEventsReceiver, bluetoothIntents);
    }

    @Override
    protected void onStart() {
        super.onStart();

        HashMap<String, UsbDevice> usbDevices = usbManager.getDeviceList();
        showMessage("Connected USB devices = "+usbDevices.size());
        for (UsbDevice device : usbDevices.values())
                showMessage(String.valueOf(device.getDeviceId()) + " " + String.valueOf(device.getVendorId()));
//        if (!usbDevices.isEmpty()) requestUSBPermission(usbDevices.values().iterator().next());
//        if (bluetoothAdapter.getScanMode() != BluetoothAdapter.SCAN_MODE_CONNECTABLE_DISCOVERABLE)
//            requestEnableBluetoothDiscoverability();
//        else
//            startBluetoothServer();
    }

    @Override
    protected void onResume() {
        super.onResume();
//        AsyncTask<Void, Void, Camera> cameraTask = new AsyncTask<Void, Void, Camera>() {
//            @Override
//            protected Camera doInBackground(Void... voids) {
//                try {
//                    camera = Camera.open(0);
//                    return camera;
//                } catch (RuntimeException ex){
//                    Log.e(TAG, getString(R.string.camera_open_error), ex);
//                    return null;
//                }
//
//            }
//            @Override
//            protected void onPostExecute(Camera camera) {
//                try {
//                    if (camera != null) {
//                        camera.setPreviewDisplay(cameraSurfaceHolder);
//                        camera.startPreview();
//                    }
//                } catch (IOException e) {
//                    Log.e(TAG, getString(R.string.camera_preview_error), e);
//                }
//            }
//        };
//        cameraTask.execute();
    }

    @Override
    protected void onPause() {
        super.onPause();
//        if (camera != null) {
//            camera.stopPreview();
//            camera.release();
//            camera = null;
//        }
    }

    @Override
    protected void onStop() {
        super.onStop();
        closeBluetoothConnection();
        closeSerialConnection();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        unregisterReceiver(bluetoothEventsReceiver);
        unregisterReceiver(usbEventsReceiver);
    }

    private void requestUSBPermission(UsbDevice device) {
        Intent permissionIntent = new Intent(USB_PERMISSION);
        permissionIntent.putExtra(USB_DEVICE, device);
        PendingIntent pi = PendingIntent.getBroadcast(this, 0, permissionIntent, 0);
        usbManager.requestPermission(device, pi);
    }

    private void openSerialConnection(final UsbDevice device) {
        AsyncTask<Void, Void, Boolean> deviceInitialisation = new AsyncTask<Void, Void, Boolean>() {
            @Override
            protected Boolean doInBackground(Void... params) {
                UsbDeviceConnection arduinoSerialConnection = usbManager.openDevice(device);
                arduinoSerialPort = UsbSerialDevice.createUsbSerialDevice(device, arduinoSerialConnection);
                if (arduinoSerialPort != null && arduinoSerialPort.open()) {
                    arduinoSerialPort.setBaudRate(SERIAL_BAUD_RATE);
                    arduinoSerialPort.setDataBits(UsbSerialInterface.DATA_BITS_8);
                    arduinoSerialPort.setParity(UsbSerialInterface.PARITY_NONE);
                    arduinoSerialPort.setStopBits(UsbSerialInterface.STOP_BITS_1);
                    arduinoSerialPort.setFlowControl(UsbSerialInterface.FLOW_CONTROL_OFF);
                    arduinoSerialPort.read(serialReadCallback);
                    return true;
                }
                return false;
            }
            @Override
            protected void onPostExecute(Boolean connectionOpened) {
                if (connectionOpened) appendLog(getString(R.string.serial_connection_opened));
                else
                    showMessage(getString(R.string.serial_open_error));
            }
        };
        deviceInitialisation.execute();
    }

    private void closeSerialConnection() {
        if (arduinoSerialPort != null) {
            arduinoSerialPort.close();
            arduinoSerialPort = null;
            appendLog(getString(R.string.serial_connection_closed));
        }
    }

    private void sendSerialData(byte[] data) {
        if (arduinoSerialPort != null)
            arduinoSerialPort.write(data);
        else showMessage(getString(R.string.no_serial_port));
    }

    private BroadcastReceiver usbEventsReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            if (intent.getAction().equals(USB_PERMISSION)){
                boolean permissionGranted = intent.getExtras().getBoolean(UsbManager.EXTRA_PERMISSION_GRANTED);
                if (permissionGranted) {
                    UsbDevice arduinoDevice = (UsbDevice) intent.getExtras().get(USB_DEVICE);
                    openSerialConnection(arduinoDevice);
                } else appendLog(getString(R.string.serial_permission_rejected));
            }
            else if (intent.getAction().equals(UsbManager.ACTION_USB_DEVICE_ATTACHED)) {
                UsbDevice device = intent.getParcelableExtra(UsbManager.EXTRA_DEVICE);
                appendLog(String.format(Locale.ENGLISH, getString(R.string.serial_device_connected), device.getVendorId()));
                requestUSBPermission(device);
            }
            else if (intent.getAction().equals(UsbManager.ACTION_USB_DEVICE_DETACHED))
                closeSerialConnection();
        }
    };

    private UsbSerialInterface.UsbReadCallback serialReadCallback = new UsbSerialInterface.UsbReadCallback() {
        @Override
        public void onReceivedData(byte[] bytes) {
            if (bluetoothTransmissionThread != null)
                bluetoothTransmissionThread.send(bytes);
        }
    };

    private void requestEnableBluetoothDiscoverability() {
        Intent discoverabilityIntent = new Intent(BluetoothAdapter.ACTION_REQUEST_DISCOVERABLE);
        discoverabilityIntent.putExtra(BluetoothAdapter.EXTRA_DISCOVERABLE_DURATION, BLUETOOTH_DISCOVERABILITY_DURATION);
        startActivity(discoverabilityIntent);
    }

    private void startBluetoothServer() {
        AsyncTask<BluetoothAdapter, Void, BluetoothSocket> bluetoothSmartphoneSocketTask = new AsyncTask<BluetoothAdapter, Void, BluetoothSocket>() {
            BluetoothServerSocket smartphoneSocket;
            @Override
            protected BluetoothSocket doInBackground(BluetoothAdapter... bluetoothAdapters) {
                try {
                    appendLog(getString(R.string.bluetooth_server_starting));
                    smartphoneSocket = bluetoothAdapters[0].listenUsingRfcommWithServiceRecord(getString(R.string.bluetooth_socket_name), DISTANCES_CAR_SERVICE_UUID);
                    bluetoothServerStarted = true;
                    appendLog(getString(R.string.bluetooth_server_waiting));
                    BluetoothSocket computerSocket = smartphoneSocket.accept();
                    appendLog(getString(R.string.bluetooth_client_connected));
                    smartphoneSocket.close();
                    return computerSocket;
                } catch (IOException ex) {
                    return null;
                }
            }

            @Override
            protected void onCancelled() {
                if (smartphoneSocket != null)
                    try {
                        smartphoneSocket.close();
                        bluetoothServerStarted = false;
                    } catch (IOException ignored) { }
            }

            @Override
            protected void onPostExecute(BluetoothSocket computerSocket) {
                if (computerSocket != null) {
                    bluetoothTransmissionThread = new BluetoothTransmissionThread(computerSocket);
                    bluetoothTransmissionThread.start();
                } else showMessage(getString(R.string.bluetooth_connection_error));
            }
        };
        bluetoothSmartphoneSocketTask.execute(bluetoothAdapter);
    }

    class BluetoothTransmissionThread extends Thread {
        private InputStream bluetoothInput;
        private OutputStream bluetoothOutput;
        private BluetoothSocket computerSocket;

        BluetoothTransmissionThread(BluetoothSocket bluetoothComputerSocket) {
            computerSocket = bluetoothComputerSocket;
        }

        @Override
        public void run() {
            try {
                bluetoothInput = computerSocket.getInputStream();
                bluetoothOutput = computerSocket.getOutputStream();
                byte[] buffer = new byte[BLUETOOTH_BUFFER_SIZE];
                int bytesCount;
                try {
                    while (!interrupted()) {
                        bytesCount = bluetoothInput.read(buffer);
                        if (bytesCount > 0) {
                            byte[] info = Arrays.copyOfRange(buffer, 0, bytesCount);
                            appendLog(String.format(getString(R.string.bluetooth_client_message), new String(info)));
                            sendSerialData(info);
                        }
                    }
                } catch (IOException ignored) { }
                bluetoothInput.close();
                bluetoothOutput.close();
                computerSocket.close();
                bluetoothInput = null;
                bluetoothOutput = null;
                bluetoothServerStarted = false;
                appendLog(getString(R.string.bluetooth_client_disconnected));
                startBluetoothServer();
            } catch (IOException ex) {
                showMessage(getString(R.string.bluetooth_stream_error));
            }
        }

        void send(byte[] data) {
            if (bluetoothOutput != null)
                try {
                    bluetoothOutput.write(data);
                    appendLog(String.format(getString(R.string.serial_device_message), new String(data)));
                } catch (IOException ex) {
                    showMessage(getString(R.string.bluetooth_client_disconnected));
                }
        }
    }

    private void closeBluetoothConnection() {
        if (bluetoothTransmissionThread != null) {
            bluetoothTransmissionThread.interrupt();
            bluetoothTransmissionThread = null;
        }
    }

    private BroadcastReceiver bluetoothEventsReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            Bundle extras = intent.getExtras();
            switch (intent.getAction()) {
                case BluetoothAdapter.ACTION_STATE_CHANGED:
                    switch (extras.getInt(BluetoothAdapter.EXTRA_STATE)) {
                        case BluetoothAdapter.STATE_ON:
                            if (bluetoothAdapter.getScanMode() != BluetoothAdapter.SCAN_MODE_CONNECTABLE_DISCOVERABLE)
                                requestEnableBluetoothDiscoverability();
                            else if (!bluetoothServerStarted)
                                startBluetoothServer();
                            break;
                        case BluetoothAdapter.STATE_TURNING_OFF:
                            closeBluetoothConnection();
                            break;
                    }
                    break;
                case BluetoothAdapter.ACTION_SCAN_MODE_CHANGED:
                    if (extras.getInt(BluetoothAdapter.EXTRA_SCAN_MODE) == BluetoothAdapter.SCAN_MODE_CONNECTABLE_DISCOVERABLE) {
                        if (!bluetoothServerStarted) startBluetoothServer();
                    }
                    break;
                case BluetoothAdapter.ACTION_CONNECTION_STATE_CHANGED:
                    if (extras.getInt(BluetoothAdapter.EXTRA_CONNECTION_STATE) == BluetoothAdapter.STATE_DISCONNECTING) {
                        closeBluetoothConnection();
                    }
                    break;
            }

        }
    };

    private void appendLog(final String text) {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                logView.append(text+'\n');
            }
        });
    }

    private void showMessage(final String message) {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                Toast.makeText(MainActivity.this, message, Toast.LENGTH_SHORT).show();
            }
        });
    }

    public void sendMessageButtonClicked(View view) {
        sendSerialData(commandInput.getText().toString().getBytes());
        commandInput.setText("");
    }

    public void resetBluetoothButtonClicked(View view) {
        if (bluetoothServerStarted) closeBluetoothConnection();
        if (bluetoothAdapter.getScanMode() != BluetoothAdapter.SCAN_MODE_CONNECTABLE_DISCOVERABLE)
            requestEnableBluetoothDiscoverability();
        else startBluetoothServer();
    }

}
