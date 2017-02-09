package abbad.hamza.distancescar;

import android.app.Activity;
import android.app.PendingIntent;
import android.bluetooth.BluetoothAdapter;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.hardware.usb.UsbDevice;
import android.hardware.usb.UsbManager;
import android.os.Bundle;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.View;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import java.util.Locale;

public class MainActivity extends Activity {

    private static final int BLUETOOTH_DISCOVERABILITY_DURATION = 60;
    private static final String ACTION_USB_PERMISSION = "abbad.hamza.permission.ACTION_USB_PERMISSION";

    private TextView logView;
    private EditText commandInput;
    private CameraCaptureManager captureManager;
    private UsbManager usbManager;
    SurfaceHolder cameraSurfaceHolder;
    BluetoothConnectionManager bluetoothConnectionManager;
    SerialConnectionManager serialConnectionManager;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        cameraSurfaceHolder = ((SurfaceView) findViewById(R.id.surfaceView)).getHolder();
        logView = (TextView) findViewById(R.id.logTextView);
        commandInput = (EditText) findViewById(R.id.messageEditText);
        usbManager = (UsbManager) getSystemService(USB_SERVICE);
        BluetoothAdapter bluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
        if (bluetoothAdapter == null) {
            showMessage(getString(R.string.bluetooth_adapter_error));
            finish();
        }
        serialConnectionManager = new SerialConnectionManager(this, usbManager);
        bluetoothConnectionManager = new BluetoothConnectionManager(this, bluetoothAdapter);
        captureManager = new CameraCaptureManager(this);
    }

    @Override
    protected void onStart() {
        super.onStart();
        // USB serial connection
        IntentFilter usbDeviceIntents = new IntentFilter();
        usbDeviceIntents.addAction(ACTION_USB_PERMISSION);
        usbDeviceIntents.addAction(UsbManager.ACTION_USB_DEVICE_ATTACHED);
        usbDeviceIntents.addAction(UsbManager.ACTION_USB_DEVICE_DETACHED);
        registerReceiver(usbEventsReceiver, usbDeviceIntents);
        // Bluetooth connection
        IntentFilter bluetoothIntents = new IntentFilter();
        bluetoothIntents.addAction(BluetoothAdapter.ACTION_STATE_CHANGED);
        bluetoothIntents.addAction(BluetoothAdapter.ACTION_SCAN_MODE_CHANGED);
        bluetoothIntents.addAction(BluetoothAdapter.ACTION_CONNECTION_STATE_CHANGED);
        registerReceiver(bluetoothEventsReceiver, bluetoothIntents);

        UsbDevice device = serialConnectionManager.getConnectedUSBDevice();
        if (device != null)
            if (!usbManager.hasPermission(device))
                requestUSBPermission(device);
            else serialConnectionManager.openSerialConnection(device);
        if (BluetoothAdapter.getDefaultAdapter().getScanMode() != BluetoothAdapter.SCAN_MODE_CONNECTABLE_DISCOVERABLE)
            requestEnableBluetoothDiscoverability();
        else
            bluetoothConnectionManager.startServer();
    }

    @Override
    protected void onResume() {
        super.onResume();
        captureManager.startCamera();
    }

    @Override
    protected void onPause() {
        super.onPause();
        captureManager.stopCamera();
    }

    @Override
    protected void onStop() {
        super.onStop();
        closeBluetoothConnection();
        serialConnectionManager.closeConnection();
        unregisterReceiver(bluetoothEventsReceiver);
        unregisterReceiver(usbEventsReceiver);
    }

    private void requestUSBPermission(UsbDevice device) {
        Intent permissionIntent = new Intent(ACTION_USB_PERMISSION);
        PendingIntent pi = PendingIntent.getBroadcast(this, 0, permissionIntent, 0);
        usbManager.requestPermission(device, pi);
    }

    private BroadcastReceiver usbEventsReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            if (intent.getAction().equals(ACTION_USB_PERMISSION)){
                if (intent.getExtras().getBoolean(UsbManager.EXTRA_PERMISSION_GRANTED)) {
                    UsbDevice arduinoDevice = intent.getParcelableExtra(UsbManager.EXTRA_DEVICE);
                    serialConnectionManager.openSerialConnection(arduinoDevice);
                } else appendLog(getString(R.string.serial_permission_rejected));
            }
            else if (intent.getAction().equals(UsbManager.ACTION_USB_DEVICE_ATTACHED)) {
                UsbDevice device = intent.getParcelableExtra(UsbManager.EXTRA_DEVICE);
                appendLog(String.format(Locale.ENGLISH, getString(R.string.serial_device_connected), device.getVendorId()));
                if (!usbManager.hasPermission(device))
                    requestUSBPermission(device);
                else serialConnectionManager.openSerialConnection(device);
            }
            else if (intent.getAction().equals(UsbManager.ACTION_USB_DEVICE_DETACHED))
                serialConnectionManager.closeConnection();
        }
    };

    private void requestEnableBluetoothDiscoverability() {
        Intent discoverabilityIntent = new Intent(BluetoothAdapter.ACTION_REQUEST_DISCOVERABLE);
        discoverabilityIntent.putExtra(BluetoothAdapter.EXTRA_DISCOVERABLE_DURATION, BLUETOOTH_DISCOVERABILITY_DURATION);
        startActivity(discoverabilityIntent);
    }

    private void closeBluetoothConnection() {
        bluetoothConnectionManager.stopServer();
        bluetoothConnectionManager.stopReceiving();
    }

    private BroadcastReceiver bluetoothEventsReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            Bundle extras = intent.getExtras();
            switch (intent.getAction()) {
                case BluetoothAdapter.ACTION_STATE_CHANGED:
                    if (extras.getInt(BluetoothAdapter.EXTRA_STATE) == BluetoothAdapter.STATE_TURNING_OFF)
                            closeBluetoothConnection();
                    break;
                case BluetoothAdapter.ACTION_SCAN_MODE_CHANGED:
                    switch (extras.getInt(BluetoothAdapter.EXTRA_SCAN_MODE)) {
                        case BluetoothAdapter.SCAN_MODE_CONNECTABLE_DISCOVERABLE:
                            if (!bluetoothConnectionManager.isRunning())
                                bluetoothConnectionManager.startServer();
                            break;
                        case BluetoothAdapter.SCAN_MODE_NONE:
                        case BluetoothAdapter.ERROR:
                            closeBluetoothConnection();
                            break;
                        default:
                            requestEnableBluetoothDiscoverability();
                    }
                    break;
                case BluetoothAdapter.ACTION_CONNECTION_STATE_CHANGED:
                    if (extras.getInt(BluetoothAdapter.EXTRA_CONNECTION_STATE) == BluetoothAdapter.STATE_DISCONNECTING)
                        closeBluetoothConnection();
                    break;
            }

        }
    };

    void appendLog(final String text) {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                logView.append(text+'\n');
            }
        });
    }

    void showMessage(final String message) {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                Toast.makeText(MainActivity.this, message, Toast.LENGTH_SHORT).show();
            }
        });
    }

    public void sendMessageButtonClicked(View view) {
        serialConnectionManager.sendSerialData(commandInput.getText().toString().getBytes());
        commandInput.setText("");
    }

    public void resetBluetoothButtonClicked(View view) {
        if (bluetoothConnectionManager.isRunning()) closeBluetoothConnection();
        if (BluetoothAdapter.getDefaultAdapter().getScanMode() != BluetoothAdapter.SCAN_MODE_CONNECTABLE_DISCOVERABLE)
            requestEnableBluetoothDiscoverability();
        else bluetoothConnectionManager.startServer();
    }

    public void resetSerialButtonClicked(View view) {
        serialConnectionManager.closeConnection();
        UsbDevice usbDevice = serialConnectionManager.getConnectedUSBDevice();
        if (usbDevice != null) {
            if (!usbManager.hasPermission(usbDevice))
                requestUSBPermission(usbDevice);
            else serialConnectionManager.openSerialConnection(usbDevice);
        } else showMessage(getString(R.string.no_serial_device));
    }

    public void captureButtonClicked(View view) {
        captureManager.takePicture();
    }

}
