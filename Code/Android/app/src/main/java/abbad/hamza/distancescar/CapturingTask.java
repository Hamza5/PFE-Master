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
            File file = new File(directory, "Distances.txt");
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
            if (!img.compress(Bitmap.CompressFormat.JPEG, 5, photoOutputStream))
                throw new IOException();
            photoOutputStream.close();
        }
    }

    static final long TASK_REPEATING_FREQUENCY = 500; // milliseconds
    static ConcurrentLinkedQueue<Distance> distancesQueue = new ConcurrentLinkedQueue<>();
    static ConcurrentLinkedQueue<Picture> picturesQueue = new ConcurrentLinkedQueue<>();

    private MainActivity mainActivity;
    private Handler h;

    CapturingTask(MainActivity parent, Handler handler) {
        mainActivity = parent;
        h = handler;
    }

    @Override
    public void run() {
        while (!distancesQueue.isEmpty() && !picturesQueue.isEmpty()) {
            try {
                Distance distance = distancesQueue.poll();
                Picture picture = picturesQueue.poll();
                if (distance.dist == 0) continue;
                picture.save(mainActivity.getExternalFilesDir(Environment.DIRECTORY_PICTURES));
                Log.i(CapturingTask.class.getName(), "Picture "+picture.id+" saved");
                distance.save(mainActivity.getExternalFilesDir(Environment.DIRECTORY_PICTURES));
                Log.i(CapturingTask.class.getName(), "Distance "+distance.id+" saved");
            } catch (IOException ex) {
                mainActivity.showMessage(mainActivity.getString(R.string.camera_photo_save_error));
            }
        }
        mainActivity.serialConnectionManager.requestDistances();
        mainActivity.serialConnectionManager.requestTemperature();
        mainActivity.captureManager.takePicture();
        h.postDelayed(this, TASK_REPEATING_FREQUENCY);
    }

}
