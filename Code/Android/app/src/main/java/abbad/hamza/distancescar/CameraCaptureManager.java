package abbad.hamza.distancescar;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Matrix;
import android.hardware.Camera;
import android.os.Environment;
import android.view.SurfaceHolder;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

class CameraCaptureManager {

    private static final String FLASH_MODE = Camera.Parameters.FLASH_MODE_OFF;
    private static final String FOCUS_MODE = Camera.Parameters.FOCUS_MODE_FIXED;
    private static final String SCENE_MODE = Camera.Parameters.SCENE_MODE_STEADYPHOTO;
    private static final String FILENAME_FORMAT = "'IMG_'yyyyMMdd_HHmmss'.jpg'";
    private static final int ORIENTATION_ANGLE = 270;

    private Camera camera;
    private MainActivity mainActivity;
    private Camera.PictureCallback pictureCapturedCallback = new Camera.PictureCallback() {
        @Override
        public void onPictureTaken(byte[] bytes, Camera camera) {
            File photo = new File(mainActivity.getExternalFilesDir(Environment.DIRECTORY_PICTURES), new SimpleDateFormat(FILENAME_FORMAT, Locale.ENGLISH).format(new Date()));
            try {
                Bitmap bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.length);
                FileOutputStream photoOutputStream = new FileOutputStream(photo);
                Bitmap processed = process(bitmap);
                if (!processed.compress(Bitmap.CompressFormat.JPEG, 10, photoOutputStream))
                    throw new IOException();
                photoOutputStream.close();
            } catch (IOException ex) {
                mainActivity.showMessage(mainActivity.getString(R.string.camera_photo_save_error));
            }
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
                        mainActivity.showMessage(mainActivity.getString(R.string.camera_preview_error));
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
                    parameters.setFlashMode(FLASH_MODE);
                if (parameters.getSupportedFocusModes() != null)
                    parameters.setFocusMode(FOCUS_MODE);
                if (parameters.getSupportedSceneModes() != null)
                    parameters.setSceneMode(SCENE_MODE);
                List<Camera.Size> sizes = parameters.getSupportedPictureSizes();
                int argmin = 0;
                for (int i=1; i<sizes.size(); i++)
                    if (sizes.get(i).width < sizes.get(argmin).width) argmin = i;
                parameters.setPictureSize(sizes.get(argmin).width, sizes.get(argmin).height);  // Minimum supported size
                camera.setParameters(parameters);
                camera.setDisplayOrientation(ORIENTATION_ANGLE);
                camera.setPreviewDisplay(mainActivity.cameraSurfaceHolder);
                camera.startPreview();
            } catch (IOException ex) {
                mainActivity.showMessage(mainActivity.getString(R.string.camera_preview_error));
            }
        } else {
            camera = Camera.open();
            if (camera == null)
                mainActivity.showMessage(mainActivity.getString(R.string.camera_open_error));
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
        if (camera != null)
            camera.takePicture(null, null, pictureCapturedCallback);
    }

    private Bitmap process(Bitmap image) {
        Matrix transformationMatrix = new Matrix();
        transformationMatrix.postRotate(ORIENTATION_ANGLE);
        return Bitmap.createBitmap(image, 0, 0, image.getWidth(), image.getHeight(), transformationMatrix, true);
    }

}
