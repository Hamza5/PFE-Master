package abbad.hamza.distancescar;

import android.os.Handler;

class CapturingTask implements Runnable {

    static final long TASK_REPEATING_FREQUENCY = 500;// milliseconds

    private MainActivity mainActivity;
    private Handler h;

    CapturingTask(MainActivity parent, Handler handler) {
        mainActivity = parent;
        h = handler;
    }

    @Override
    public void run() {
        mainActivity.serialConnectionManager.requestDistances();
        mainActivity.serialConnectionManager.requestTemperature();
        h.postDelayed(this, TASK_REPEATING_FREQUENCY);
    }

}
