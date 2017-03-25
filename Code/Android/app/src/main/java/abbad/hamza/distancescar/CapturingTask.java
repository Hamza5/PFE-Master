package abbad.hamza.distancescar;

import android.graphics.Bitmap;
import android.os.Environment;
import android.os.Handler;
import android.util.Log;

import java.io.File;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.FilenameFilter;
import java.io.IOException;
import java.util.Locale;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.atomic.AtomicBoolean;

class CapturingTask implements Runnable {

    private static final String DISTANCES_FILE_NAME = "Distances.txt";

    static class Distance {
        float[] dists;
        private long id;
        Distance(float[] distances) {
            dists = distances;
            id = System.currentTimeMillis();
        }
        void save(File directory) throws IOException {
            File file = new File(directory, DISTANCES_FILE_NAME);
            FileWriter textWriter = new FileWriter(file, true);
            String distancesPrinted = String.format(Locale.ENGLISH, "%.2f|%.2f|%.2f%n", dists[0], dists[1], dists[2]);
            textWriter.write(distancesPrinted);
            textWriter.close();
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
            FileOutputStream photoOutputStream = new FileOutputStream(file);
            if (!img.compress(Bitmap.CompressFormat.JPEG, 100, photoOutputStream))
                throw new IOException();
            photoOutputStream.close();
        }
    }

    private static final long TASK_REPEATING_FREQUENCY = 100; // milliseconds
    private static final long CAPTURE_SAVING_FREQUENCY = 500; // milliseconds
    private static final long TEMPERATURE_CHECKING_FREQUENCY = 2000; // milliseconds
    private static AtomicBoolean capture = new AtomicBoolean(false);
    static ConcurrentLinkedQueue<Distance> distancesQueue = new ConcurrentLinkedQueue<>();
    static ConcurrentLinkedQueue<Picture> picturesQueue = new ConcurrentLinkedQueue<>();

    private MainActivity mainActivity;
    private Handler h;
    private File savingDirectory;
    private int dataCount;
    private long lastCaptureTime;
    private long lastTempTime;

    CapturingTask(MainActivity parent, Handler handler) {
        mainActivity = parent;
        h = handler;
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
        if (!distancesQueue.isEmpty() && !picturesQueue.isEmpty()) {
            try {
                Distance distance = distancesQueue.poll();
                Picture picture = picturesQueue.poll();
                if (capture.get() && currentTime - lastCaptureTime >= CAPTURE_SAVING_FREQUENCY) {
                    lastCaptureTime = currentTime;
                    picture.save(savingDirectory);
                    Log.i(CapturingTask.class.getName(), "Picture "+picture.id+" saved");
                    distance.save(savingDirectory);
                    Log.i(CapturingTask.class.getName(), "Distance "+distance.id+" saved");
                    dataCount++;
                    mainActivity.bluetoothConnectionManager.sendToComputer(String.format(Locale.ENGLISH, "C%d", dataCount).getBytes());
                }
            } catch (IOException ex) {
                String errorMessage = mainActivity.getString(R.string.camera_photo_save_error);
                mainActivity.showMessage(errorMessage);
                Log.e(getClass().getName(), errorMessage);
            }
        }
        mainActivity.serialConnectionManager.requestDistances();
        mainActivity.captureManager.takePicture();
        h.postDelayed(this, TASK_REPEATING_FREQUENCY);
    }

    static void toggleCapture() {
        capture.set(!capture.get());
    }

}
