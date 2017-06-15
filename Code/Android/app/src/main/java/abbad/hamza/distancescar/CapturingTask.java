package abbad.hamza.distancescar;

import android.graphics.Bitmap;
import android.graphics.Matrix;
import android.os.Environment;
import android.os.Handler;
import android.util.Log;

import java.io.File;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.FilenameFilter;
import java.io.IOException;
import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.util.Arrays;
import java.util.Locale;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicLong;

class CapturingTask implements Runnable {

    private static final String DISTANCES_FILE_NAME = "Distances.txt";
    private static final int CORP_MARGIN = 80;
    private static final int PICTURE_WIDTH = 96;
    private static final int PICTURE_HEIGHT = 96;

    static class Distance {
        float[] dists;
        Distance(float[] distances) {
            dists = distances;
        }
        void save(File directory, long pictureID) throws IOException {
            File file = new File(directory, DISTANCES_FILE_NAME);
            StringBuilder distancesPrinted = new StringBuilder(pictureID+",");
            for (float dist : dists) {
                distancesPrinted.append(new DecimalFormat("0.00", new DecimalFormatSymbols(Locale.ENGLISH)).format(dist));
                distancesPrinted.append(",");
            }
            distancesPrinted.replace(distancesPrinted.length()-1, distancesPrinted.length(), "\n");
            FileWriter textWriter = new FileWriter(file, true);
            textWriter.write(distancesPrinted.toString());
            textWriter.close();
        }
        @Override
        public String toString() {
            return Arrays.toString(dists);
        }
    }
    static class Picture {
        Bitmap img;
        private long id;
        Picture(Bitmap picture) {
            img = picture;
            id = System.currentTimeMillis();
        }
        void save(File directory) throws IOException {
            File file = new File(directory, "IMG_"+id+".jpg");
            Bitmap processed = postProcess(img);
            FileOutputStream photoOutputStream = new FileOutputStream(file);
            if (!processed.compress(Bitmap.CompressFormat.JPEG, 100, photoOutputStream))
                throw new IOException();
            photoOutputStream.close();
        }
        private Bitmap postProcess(Bitmap image) { // Corp and resize
            Matrix transformationMatrix = new Matrix();
            transformationMatrix.postRotate(CameraCaptureManager.ORIENTATION_ANGLE);
            Bitmap rotated = Bitmap.createBitmap(image, 0, 0, image.getWidth(), image.getHeight(), transformationMatrix, true);
            Bitmap cropped = Bitmap.createBitmap(rotated, 0, CORP_MARGIN, rotated.getWidth(), rotated.getHeight()-2*CORP_MARGIN);
            return Bitmap.createScaledBitmap(cropped, PICTURE_WIDTH, PICTURE_HEIGHT, false);
        }
    }

    private static final long TASK_REPEATING_FREQUENCY = 200; // milliseconds
    private static final long CAPTURE_SAVING_FREQUENCY = 500; // milliseconds
    private static final long TEMPERATURE_CHECKING_FREQUENCY = 2000; // milliseconds
    private static AtomicBoolean capture = new AtomicBoolean(false);
    static final ConcurrentLinkedQueue<Distance> distancesQueue = new ConcurrentLinkedQueue<>();
    static final ConcurrentLinkedQueue<Picture> picturesQueue = new ConcurrentLinkedQueue<>();
    static final AtomicLong lastPictureRequest = new AtomicLong();
    static final AtomicLong lastDistancesRequest = new AtomicLong();

    private MainActivity mainActivity;
    private Handler h;
    private File savingDirectory;
    private int dataCount;
    private long lastCaptureTime;
    private long lastTempTime;

    CapturingTask(MainActivity parent, Handler handler) {
        mainActivity = parent;
        h = handler;
//        savingDirectory = mainActivity.getExternalFilesDir(Environment.DIRECTORY_PICTURES);
        File[] externalDirs = mainActivity.getExternalFilesDirs(Environment.DIRECTORY_PICTURES);
        savingDirectory = externalDirs[externalDirs.length-1]; // The last one should be on the SD card
        dataCount = savingDirectory.list(new FilenameFilter() {
            @Override
            public boolean accept(File file, String s) {
                return s.endsWith(".jpg") && s.startsWith("IMG_");
            }
        }).length;
        Log.i(getClass().getName(), String.format(Locale.ENGLISH, "%d captures saved in %s", dataCount, savingDirectory.getAbsolutePath()));
        lastTempTime = lastCaptureTime = System.currentTimeMillis();
    }

    @Override
    public void run() {
        long currentTime = System.currentTimeMillis();
        if (currentTime - lastTempTime >= TEMPERATURE_CHECKING_FREQUENCY) {
            lastTempTime = currentTime;
            mainActivity.serialConnectionManager.requestTemperature();
            // This is not the right place for the following instruction, but at least now the information can be displayed anytime
            mainActivity.bluetoothConnectionManager.sendToComputer(String.format(Locale.ENGLISH, "C%d", dataCount).getBytes());
        }
        while (!distancesQueue.isEmpty() && !picturesQueue.isEmpty()) {
            Distance distance = distancesQueue.poll();
            Picture picture = picturesQueue.poll();
            if (capture.get() && currentTime - lastCaptureTime >= CAPTURE_SAVING_FREQUENCY) {
                lastCaptureTime = currentTime;
                try {
                    picture.save(savingDirectory);
                    distance.save(savingDirectory, picture.id);
                    dataCount++;
                    mainActivity.bluetoothConnectionManager.sendToComputer(String.format(Locale.ENGLISH, "C%d", dataCount).getBytes());
                } catch (IOException ex) {
                    String errorMessage = mainActivity.getString(R.string.camera_photo_save_error);
                    mainActivity.showMessage(errorMessage);
                    Log.e(getClass().getName(), errorMessage);
                    mainActivity.bluetoothConnectionManager.sendToComputer("EC".getBytes());
                }
            }
        }
        if (capture.get() || mainActivity.serialConnectionManager.navigation.get()) {
            mainActivity.serialConnectionManager.requestDistances();
            mainActivity.captureManager.takePicture();
        }
        h.postDelayed(this, TASK_REPEATING_FREQUENCY);
    }

    static void toggleCapture() {
        boolean old = capture.get();
        capture.compareAndSet(old, !old);
    }

}
