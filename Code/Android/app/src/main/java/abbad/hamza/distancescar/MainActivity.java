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
import android.os.Handler;
import android.text.Editable;
import android.text.TextWatcher;
import android.util.Log;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.View;
import android.widget.EditText;
import android.widget.SeekBar;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.ToggleButton;

import java.text.DecimalFormat;

public class MainActivity extends Activity {

    private static final int BLUETOOTH_DISCOVERABILITY_DURATION = 60; // seconds
    private static final String ACTION_USB_PERMISSION = "abbad.hamza.permission.ACTION_USB_PERMISSION";

    private ToggleButton serialButton;
    private ToggleButton bluetoothButton;
    private TextView bluetoothConnectionTextView;
    private TextView distanceValueTextView;
    private TextView temperatureValueTextView;
    private UsbManager usbManager;
    SurfaceHolder cameraSurfaceHolder;
    BluetoothConnectionManager bluetoothConnectionManager;
    SerialConnectionManager serialConnectionManager;
    CameraCaptureManager captureManager;
    SeekBar powerSeekBar;
    EditText delayEditText;
    private Handler handler;
    private Toast messagesToast;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        cameraSurfaceHolder = ((SurfaceView) findViewById(R.id.surfaceView)).getHolder();
        serialButton = (ToggleButton) findViewById(R.id.serialConnectionButton);
        bluetoothButton = (ToggleButton) findViewById(R.id.bluetoothConnectionButton);
        bluetoothConnectionTextView = (TextView) findViewById(R.id.bluetoothConnectedTextView);
        distanceValueTextView = (TextView) findViewById(R.id.distanceValueTextView);
        temperatureValueTextView = (TextView) findViewById(R.id.temperatureValueTextView);
        delayEditText = (EditText) findViewById(R.id.delayEditText);
        powerSeekBar = (SeekBar) findViewById(R.id.powerSeekBar);
        usbManager = (UsbManager) getSystemService(USB_SERVICE);
        BluetoothAdapter bluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
        if (bluetoothAdapter == null) {
            showMessage(getString(R.string.bluetooth_adapter_error));
            finish();
        }
        serialConnectionManager = new SerialConnectionManager(this, usbManager);
        bluetoothConnectionManager = new BluetoothConnectionManager(this, bluetoothAdapter);
        captureManager = new CameraCaptureManager(this);
        handler = new Handler();
        powerSeekBar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override
            public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                serialConnectionManager.setEnginesPower(progress);
            }

            @Override
            public void onStartTrackingTouch(SeekBar seekBar) {

            }

            @Override
            public void onStopTrackingTouch(SeekBar seekBar) {

            }
        });
        delayEditText.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence charSequence, int i, int i1, int i2) {

            }

            @Override
            public void onTextChanged(CharSequence charSequence, int i, int i1, int i2) {

            }

            @Override
            public void afterTextChanged(Editable editable) {
                String text = editable.toString();
                if (!text.isEmpty())
                    serialConnectionManager.setMovingTime(Integer.parseInt(text));
            }
        });

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
            if (!usbManager.hasPermission(device)) requestUSBPermission(device);
            else openSerialConnection(device);
        else serialButton.setChecked(false);
        if (BluetoothAdapter.getDefaultAdapter().getScanMode() != BluetoothAdapter.SCAN_MODE_CONNECTABLE_DISCOVERABLE)
            requestEnableBluetoothDiscoverability();
        else {
            bluetoothConnectionManager.startServer();
            bluetoothButton.setChecked(true);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        captureManager.startCamera();
    }

    @Override
    protected void onPause() {
        captureManager.stopCamera();
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        closeBluetoothConnection();
        closeSerialConnection();
        unregisterReceiver(bluetoothEventsReceiver);
        unregisterReceiver(usbEventsReceiver);
        super.onDestroy();
    }

    private void requestUSBPermission(UsbDevice device) {
        serialButton.setChecked(false);
        Intent permissionIntent = new Intent(ACTION_USB_PERMISSION);
        PendingIntent pi = PendingIntent.getBroadcast(this, 0, permissionIntent, 0);
        usbManager.requestPermission(device, pi);
    }

    private void openSerialConnection(UsbDevice device) {
        serialConnectionManager.openSerialConnection(device);
    }

    void serialConnectionOpened() {
        serialButton.setChecked(true);
        handler.postDelayed(new CapturingTask(this, handler), CapturingTask.TASK_REPEATING_FREQUENCY);
    }

    private void closeSerialConnection() {
        handler.removeCallbacksAndMessages(null);
        serialConnectionManager.closeConnection();
        serialButton.setChecked(false);
    }

    private BroadcastReceiver usbEventsReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            if (intent.getAction().equals(ACTION_USB_PERMISSION)){
                if (intent.getExtras().getBoolean(UsbManager.EXTRA_PERMISSION_GRANTED)) {
                    UsbDevice arduinoDevice = intent.getParcelableExtra(UsbManager.EXTRA_DEVICE);
                    openSerialConnection(arduinoDevice);
                } else {
                    serialButton.setChecked(false);
                }
            }
            else if (intent.getAction().equals(UsbManager.ACTION_USB_DEVICE_ATTACHED)) {
                UsbDevice device = intent.getParcelableExtra(UsbManager.EXTRA_DEVICE);
                if (!usbManager.hasPermission(device))
                    requestUSBPermission(device);
                else openSerialConnection(device);
            }
            else if (intent.getAction().equals(UsbManager.ACTION_USB_DEVICE_DETACHED)) {
                closeSerialConnection();
            }
        }
    };

    private void requestEnableBluetoothDiscoverability() {
        bluetoothButton.setChecked(false);
        Intent discoverabilityIntent = new Intent(BluetoothAdapter.ACTION_REQUEST_DISCOVERABLE);
        discoverabilityIntent.putExtra(BluetoothAdapter.EXTRA_DISCOVERABLE_DURATION, BLUETOOTH_DISCOVERABILITY_DURATION);
        startActivity(discoverabilityIntent);
    }

    private void closeBluetoothConnection() {
        bluetoothConnectionManager.stopServer();
        bluetoothConnectionManager.stopReceiving();
        setBluetoothConnectionStatus(false);
    }

    void setBluetoothConnectionStatus(final boolean connected) {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                String text = connected ? getString(R.string.connected_label) : getString(R.string.disconnected_label);
                bluetoothConnectionTextView.setText(text);
            }
        });
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
                            if (!bluetoothConnectionManager.isRunning()) {
                                bluetoothButton.setChecked(true);
                                bluetoothConnectionManager.startServer();
                            }
                            break;
                        case BluetoothAdapter.SCAN_MODE_NONE:
                        case BluetoothAdapter.ERROR:
                            closeBluetoothConnection();
                            bluetoothButton.setChecked(false);
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

    void showMessage(final String message) {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                if (messagesToast != null) messagesToast.cancel();
                messagesToast = Toast.makeText(MainActivity.this, message, Toast.LENGTH_SHORT);
                messagesToast.show();
            }
        });
    }

    class DistanceUpdate implements Runnable {
        float distance;
        DistanceUpdate(float minDistance) {
            distance = minDistance;
        }
        @Override
        public void run() {
            if (distance > 0) distanceValueTextView.setText(new DecimalFormat("0.00m").format(distance));
            else distanceValueTextView.setText(R.string.not_available_label);
        }
    }

    void updateDistance(float[] distances) {
        for (int i=0; i<distances.length; i++) {
            if (distances[i] == 0) distances[i] = Float.MAX_VALUE;
        }
        float min = Math.min(Math.min(distances[0], distances[1]), distances[2]);
        distanceValueTextView.post(new DistanceUpdate(min));
    }

    class TemperatureUpdate implements Runnable {
        float temp;
        TemperatureUpdate(float temperature) {
            temp = temperature;
        }
        @Override
        public void run() {
            if (temp > 0) temperatureValueTextView.setText(new DecimalFormat("0.00°C").format(temp));
            else temperatureValueTextView.setText(R.string.not_available_label);
        }
    }

    void updateTemperature(float temperature) {
        temperatureValueTextView.post(new TemperatureUpdate(temperature));
    }

    public void resetBluetoothButtonClicked(View view) {
        if (bluetoothButton.isChecked()) {
            if (BluetoothAdapter.getDefaultAdapter().getScanMode() != BluetoothAdapter.SCAN_MODE_CONNECTABLE_DISCOVERABLE)
                requestEnableBluetoothDiscoverability();
            else {
                bluetoothConnectionManager.startServer();
                bluetoothButton.setChecked(true);
            }
        } else if (bluetoothConnectionManager.isRunning()) closeBluetoothConnection();
    }

    public void resetSerialButtonClicked(View view) {
        if (serialButton.isChecked()) {
            UsbDevice usbDevice = serialConnectionManager.getConnectedUSBDevice();
            if (usbDevice != null) {
                if (!usbManager.hasPermission(usbDevice))
                    requestUSBPermission(usbDevice);
                else {
                    openSerialConnection(usbDevice);
                }
            } else {
                showMessage(getString(R.string.serial_no_device));
                serialButton.setChecked(false);
            }
        } else closeSerialConnection();
    }

    public void forwardButtonClicked(View view) {
        serialConnectionManager.moveForward();
    }

    public void backwardButtonClicked(View view) {
        serialConnectionManager.moveBackward();
    }

    public void leftButtonClicked(View view) {
        serialConnectionManager.turnLeft();
    }

    public void rightButtonClicked(View view) {
        serialConnectionManager.turnRight();
    }

}
