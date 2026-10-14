package fi.jakke77.saawidget;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public final class WeatherBootReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context,Intent intent){if(intent==null||(!Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())&&!Intent.ACTION_MY_PACKAGE_REPLACED.equals(intent.getAction())))return;WeatherUpdateJobService.schedule(context);WeatherUpdateJobService.refreshNow(context);for(int id:WeatherWidgetUpdater.widgetIds(context))WeatherWidgetUpdater.renderCached(context,id);}
}
