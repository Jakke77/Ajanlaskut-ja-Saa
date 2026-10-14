package fi.jakke77.saawidget;

import android.app.job.JobInfo;
import android.app.job.JobParameters;
import android.app.job.JobScheduler;
import android.app.job.JobService;
import android.content.ComponentName;
import android.content.Context;
import java.util.HashMap;
import java.util.Map;

/** System-managed background work: no always-running service or battery exemption request. */
public final class WeatherUpdateJobService extends JobService {
    private static final int JOB_ID=7051, IMMEDIATE_JOB_ID=7052;
    private final Map<Integer,JobParameters> active=new HashMap<>();
    public static void schedule(Context context){
        JobScheduler scheduler=(JobScheduler)context.getSystemService(Context.JOB_SCHEDULER_SERVICE);
        if(scheduler==null)return;JobInfo existing=scheduler.getPendingJob(JOB_ID);if(existing!=null)return;
        scheduler.schedule(new JobInfo.Builder(JOB_ID,new ComponentName(context,WeatherUpdateJobService.class)).setPeriodic(30*60*1000L,10*60*1000L).setRequiredNetworkType(JobInfo.NETWORK_TYPE_ANY).setPersisted(true).build());
    }
    public static void refreshNow(Context context){JobScheduler scheduler=(JobScheduler)context.getSystemService(Context.JOB_SCHEDULER_SERVICE);if(scheduler!=null)scheduler.schedule(new JobInfo.Builder(IMMEDIATE_JOB_ID,new ComponentName(context,WeatherUpdateJobService.class)).setMinimumLatency(0).setRequiredNetworkType(JobInfo.NETWORK_TYPE_ANY).build());}
    @Override public boolean onStartJob(JobParameters params){active.put(params.getJobId(),params);WeatherWidgetUpdater.refreshAll(this,()->new android.os.Handler(android.os.Looper.getMainLooper()).post(()->{if(active.get(params.getJobId())==params){active.remove(params.getJobId());jobFinished(params,false);}}));return true;}
    @Override public boolean onStopJob(JobParameters params){active.remove(params.getJobId());return true;}
}
