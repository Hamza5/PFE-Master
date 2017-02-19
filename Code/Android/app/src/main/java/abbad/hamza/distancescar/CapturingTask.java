package abbad.hamza.distancescar;

import android.graphics.Bitmap;
import android.os.Environment;
import android.os.Handler;
import android.util.Log;

import java.io.File;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.text.DecimalFormat;
import java.util.concurrent.ConcurrentLinkedQueue;

class CapturingTask implements Runnable {

    private static final String DISTANCES_FILE_NAME = "Distances.txt";

    static class Distance implements Comparable<Distance> {
        float dist;
        private long id;
        Distance(float distance) {
            dist = distance;
            id = System.currentTimeMillis();
        }
        @Override
        public int compareTo(Distance distance) {
            return (int) (id - distance.id);
        }
        void save(File directory) throws IOException {
            File file = new File(directory, DISTANCES_FILE_NAME);
            FileWriter textWriter = new FileWriter(file, true);
            textWriter.write(new DecimalFormat("0.00").format(dist));
            textWriter.write('\n');
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

    static final long TASK_REPEATING_FREQUENCY = 500; // milliseconds
    static ConcurrentLinkedQueue<Distance> distancesQueue = new ConcurrentLinkedQueue<>();
    static ConcurrentLinkedQueue<Picture> picturesQueue = new ConcurrentLinkedQueue<>();

    private MainActivity mainActivity;
    private Handler h;
    private File savingDirectory;

    CapturingTask(MainActivity parent, Handler handler) {
        mainActivity = parent;
        h = handler;
        File[] externalDirs = mainActivity.getExternalFilesDirs(Environment.DIRECTORY_PICTURES);
        savingDirectory = externalDirs[externalDirs.length-1];
        Log.i(getClass().getName(), savingDirectory.getAbsolutePath());
    }

    @Override
    public void run() {
        while (!distancesQueue.isEmpty() && !picturesQueue.isEmpty()) {
            try {
                Distance distance = distancesQueue.poll();
                Picture picture = picturesQueue.poll();
                picture.save(savingDirectory);
                Log.i(CapturingTask.class.getName(), "Picture "+picture.id+" saved");
                distance.save(savingDirectory);
                Log.i(CapturingTask.class.getName(), "Distance "+distance.id+" saved");
            } catch (IOException ex) {
                String errorMessage = mainActivity.getString(R.string.camera_photo_save_error);
                mainActivity.showMessage(errorMessage);
                Log.e(getClass().getName(), errorMessage);
            }
        }
        mainActivity.serialConnectionManager.requestDistances();
        mainActivity.serialConnectionManager.requestTemperature();
        mainActivity.captureManager.takePicture();
        h.postDelayed(this, TASK_REPEATING_FREQUENCY);
    }

}
