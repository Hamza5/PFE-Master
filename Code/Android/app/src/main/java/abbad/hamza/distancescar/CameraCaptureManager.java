package abbad.hamza.distancescar;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.hardware.Camera;
import android.util.Log;
import android.view.SurfaceHolder;

import java.io.IOException;

class CameraCaptureManager {

    private static final String DEFAULT_FLASH_MODE = Camera.Parameters.FLASH_MODE_OFF;
    private static final int JPEG_QUALITY = 50;
    static final int ORIENTATION_ANGLE = 270;

    private Camera camera;
    private MainActivity mainActivity;
    private Camera.PictureCallback pictureCapturedCallback = new Camera.PictureCallback() {
        @Override
        public void onPictureTaken(byte[] bytes, Camera camera) {
            Bitmap bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.length);
            CapturingTask.picturesQueue.add(new CapturingTask.Picture(bitmap));
            Log.i(SerialConnectionManager.class.getName(), "Picture received in "+(System.currentTimeMillis()-CapturingTask.lastDistancesRequest.get())+"ms");
            camera.startPreview();
        }
    };

    CameraCaptureManager(MainActivity parent) {
        mainActivity = parent;
        SurfaceHolder.Callback previewCallback = new SurfaceHolder.Callback() {
            @Override
            public void surfaceCreated(SurfaceHolder surfaceHolder) {

            }

            @Override
            public void surfaceChanged(SurfaceHolder surfaceHolder, int i, int i1, int i2) {
                if (surfaceHolder.getSurface() != null) {
                    try {
                        if (camera != null) {
                            camera.stopPreview();
                            camera.setPreviewDisplay(surfaceHolder);
                            camera.startPreview();
                        }
                    } catch (IOException ex) {
                        String errorMessage = mainActivity.getString(R.string.camera_preview_error);
                        mainActivity.showMessage(errorMessage);
                        Log.e(CameraCaptureManager.class.getName(), errorMessage);
                        mainActivity.bluetoothConnectionManager.sendToComputer("EM".getBytes());
                    }
                }
            }

            @Override
            public void surfaceDestroyed(SurfaceHolder surfaceHolder) {

            }
        };
        mainActivity.cameraSurfaceHolder.addCallback(previewCallback);
    }

    void startCamera() {
        if (camera != null) {
            try {
                Camera.Parameters parameters = camera.getParameters();
                if (parameters.getSupportedFlashModes() != null)
                    parameters.setFlashMode(DEFAULT_FLASH_MODE);
                parameters.setPictureSize(640, 480);  // Minimum supported size
                parameters.setJpegQuality(JPEG_QUALITY);
                camera.setParameters(parameters);
                camera.setDisplayOrientation(ORIENTATION_ANGLE);
                camera.setPreviewDisplay(mainActivity.cameraSurfaceHolder);
                camera.startPreview();
            } catch (IOException ex) {
                String errorMessage = mainActivity.getString(R.string.camera_preview_error);
                mainActivity.showMessage(errorMessage);
                Log.e(getClass().getName(), errorMessage);
                mainActivity.bluetoothConnectionManager.sendToComputer("EM".getBytes());
            }
        } else {
            camera = Camera.open();
            if (camera == null) {
                String errorMessage = mainActivity.getString(R.string.camera_open_error);
                mainActivity.showMessage(errorMessage);
                Log.e(getClass().getName(), errorMessage);
                mainActivity.bluetoothConnectionManager.sendToComputer("EM".getBytes());
            }
            else startCamera();
        }
    }

    void stopCamera() {
        if (camera != null) {
            camera.stopPreview();
            camera.release();
            camera = null;
        }
    }

    void takePicture() {
        CapturingTask.lastPictureRequest.set(System.currentTimeMillis());
        if (camera != null)
            camera.takePicture(null, null, pictureCapturedCallback);
    }

    void toggleFlashMode() {
        Camera.Parameters parameters = camera.getParameters();
        String flashMode = parameters.getFlashMode();
        if (flashMode != null) {
            boolean enabled = flashMode.equals(Camera.Parameters.FLASH_MODE_TORCH);
            parameters.setFlashMode(enabled ? Camera.Parameters.FLASH_MODE_OFF : Camera.Parameters.FLASH_MODE_TORCH);
            camera.setParameters(parameters);
        }
    }

}
