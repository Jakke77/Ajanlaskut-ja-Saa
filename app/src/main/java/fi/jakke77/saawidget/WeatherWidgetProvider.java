package fi.jakke77.saawidget;

import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Compact 1×1; larger providers share the same lifecycle and update logic. */
public class WeatherWidgetProvider extends AppWidgetProvider {
    private static final ExecutorService RENDER=Executors.newSingleThreadExecutor();
    @Override public void onEnabled(Context context){WeatherUpdateJobService.schedule(context);}
    @Override public void onUpdate(Context context,AppWidgetManager manager,int[] ids){
        WeatherUpdateJobService.schedule(context);PendingResult pending=goAsync();
        RENDER.execute(()->{try{for(int id:ids)WeatherWidgetUpdater.renderCached(context,id);WeatherUpdateJobService.refreshNow(context);}finally{pending.finish();}});
    }
    @Override public void onReceive(Context context,Intent intent){
        if(WeatherWidgetUpdater.ACTION_REFRESH.equals(intent.getAction())){
            int id=intent.getIntExtra(AppWidgetManager.EXTRA_APPWIDGET_ID,AppWidgetManager.INVALID_APPWIDGET_ID);
            PendingResult pending=goAsync();
            RENDER.execute(()->{try{if(WeatherWidgetUpdater.belongsToApp(context,id)){WeatherWidgetUpdater.renderCached(context,id);WeatherUpdateJobService.refreshNow(context);}}finally{pending.finish();}});return;
        }
        super.onReceive(context,intent);
    }
    @Override public void onAppWidgetOptionsChanged(Context context,AppWidgetManager manager,int id,Bundle options){WeatherWidgetUpdater.renderCached(context,id);}
    @Override public void onDeleted(Context context,int[] ids){for(int id:ids)WidgetConfig.delete(context,id);}
    @Override public void onRestored(Context context,int[] oldIds,int[] newIds){
        for(int i=0;i<Math.min(oldIds.length,newIds.length);i++){WidgetConfig.load(context,oldIds[i]).save(context,newIds[i]);WidgetConfig.delete(context,oldIds[i]);}
        // The host follows restoration with APPWIDGET_UPDATE; avoid duplicate network work here.
    }
}
