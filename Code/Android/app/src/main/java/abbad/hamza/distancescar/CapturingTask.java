package abbad.hamza.distancescar;

import android.graphics.Bitmap;
import android.os.Environment;
import android.os.Handler;
import android.util.Log;

import java.io.File;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.util.Locale;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.atomic.AtomicBoolean;

class CapturingTask implements Runnable {

    private static final String DISTANCES_FILE_NAME = "Distances.txt";

    static class Distance implements Comparable<Distance> {
        float[] dists;
        private long id;
        Distance(float[] distances) {
            dists = distances;
            id = System.currentTimeMillis();
        }
        @Override
        public int compareTo(Distance distance) {
            return (int) (id - distance.id);
        }
        void save(File directory) throws IOException {
            File file = new File(directory, DISTANCES_FILE_NAME);
            FileWriter textWriter = new FileWriter(file, true);
            String distancesPrinted = String.format(Locale.ENGLISH, "%.2f|%.2f|%.2f%n", dists[0], dists[1], dists[2]);
            textWriter.write(distancesPrinted);
            textWriter.close();
        }
    }
    static class Picture implements Comparable<Picture> {
        Bitmap img;
        private long id;
        Picture(Bitmap picture) {
            img = picture;
            id = System.currentTimeMillis();
        }
        @Override
        public int compareTo(Picture picture) {
            return (int) (id - picture.id);
        }
        void save(File directory) throws IOException {
            File file = new File(directory, "IMG_"+id+".jpg");
            FileOutputStream photoOutputStream = new FileOutputStream(file);
            if (!img.compress(Bitmap.CompressFormat.JPEG, 100, photoOutputStream))
                throw new IOException();
            photoOutputStream.close();
        }
    }

    private static final float NEEDED_TURN_DISTANCE = 0.2f;
    private static final float NEEDED_FORWARD_DISTANCE = 0.4f;
    private static final long CAPTURE_SAVING_FREQUENCY = 500; // milliseconds
    private static final long TASK_REPEATING_FREQUENCY = 100; // milliseconds
    private static AtomicBoolean navigation = new AtomicBoolean(false);
    static ConcurrentLinkedQueue<Distance> distancesQueue = new ConcurrentLinkedQueue<>();
    static ConcurrentLinkedQueue<Picture> picturesQueue = new ConcurrentLinkedQueue<>();

    private MainActivity mainActivity;
    private Handler h;
    private File savingDirectory;
    private long lastCaptureTime;
    private boolean right;

    CapturingTask(MainActivity parent, Handler handler) {
        mainActivity = parent;
        h = handler;
        File[] externalDirs = mainActivity.getExternalFilesDirs(Environment.DIRECTORY_PICTURES);
        savingDirectory = externalDirs[externalDirs.length-1];
        Log.i(getClass().getName(), savingDirectory.getAbsolutePath());
        lastCaptureTime = System.currentTimeMillis();
    }

    @Override
    public void run() {
        if (!distancesQueue.isEmpty() && !picturesQueue.isEmpty()) {
            try {
                Distance distance = distancesQueue.poll();
                Picture picture = picturesQueue.poll();
                long currentTime = System.currentTimeMillis();
                if (currentTime - lastCaptureTime >= CAPTURE_SAVING_FREQUENCY) {
                    lastCaptureTime = currentTime;
                    picture.save(savingDirectory);
                    Log.i(CapturingTask.class.getName(), "Picture "+picture.id+" saved");
                    distance.save(savingDirectory);
                    Log.i(CapturingTask.class.getName(), "Distance "+distance.id+" saved");
                }
                String distancesString = String.format(Locale.ENGLISH, "%.2f|%.2f|%.2f",
                        distance.dists[0], distance.dists[1], distance.dists[2]);
                mainActivity.bluetoothConnectionManager.sendToComputer(distancesString.getBytes());
                if (navigation.get())
                    navigate(distance);
            } catch (IOException ex) {
                String errorMessage = mainActivity.getString(R.string.camera_photo_save_error);
                mainActivity.showMessage(errorMessage);
                Log.e(getClass().getName(), errorMessage);
            }
        }
        if (navigation.get()) {
            mainActivity.serialConnectionManager.requestDistances();
            mainActivity.serialConnectionManager.requestTemperature();
            mainActivity.captureManager.takePicture();
        }
        h.postDelayed(this, TASK_REPEATING_FREQUENCY);
    }

    private void navigate(Distance d) {
        Log.i(getClass().getName(), "navigate");
        for (int i = 0; i < d.dists.length; i++) {
            if (d.dists[i] == 0) d.dists[i] = Float.MAX_VALUE;
        }
        float distance = Float.MAX_VALUE;
        for (float dist : d.dists) distance = Math.min(dist, distance);
        if (distance < NEEDED_TURN_DISTANCE) {
            mainActivity.serialConnectionManager.moveBackward();
            right = Math.random() < 0.5;
        } else if (distance < NEEDED_FORWARD_DISTANCE) {
            if (right) mainActivity.serialConnectionManager.turnRight();
            else mainActivity.serialConnectionManager.turnLeft();
        } else
            mainActivity.serialConnectionManager.moveForward();
    }

    static void setNavigation(boolean enabled) {
        navigation.set(enabled);
    }

}
