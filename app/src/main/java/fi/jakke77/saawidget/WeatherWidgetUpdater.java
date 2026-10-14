package fi.jakke77.saawidget;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProviderInfo;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.util.TypedValue;
import android.widget.RemoteViews;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

/** One rendering and refresh path for app actions, the background job and all widget sizes. */
public final class WeatherWidgetUpdater {
    public static final String ACTION_REFRESH = "fi.jakke77.saawidget.REFRESH_WIDGET";
    private WeatherWidgetUpdater() {}
    public static int[] widgetIds(Context context) {
        AppWidgetManager manager=AppWidgetManager.getInstance(context);List<Integer> result=new ArrayList<>();
        for(Class<?> type : new Class<?>[]{WeatherWidgetProvider.class,WeatherWideWidgetProvider.class,WeatherForecastWidgetProvider.class})
            for(int id:manager.getAppWidgetIds(new ComponentName(context,type)))result.add(id);
        int[] ids=new int[result.size()];for(int i=0;i<ids.length;i++)ids[i]=result.get(i);return ids;
    }
    public static boolean belongsToApp(Context context,int id) {
        AppWidgetProviderInfo info=AppWidgetManager.getInstance(context).getAppWidgetInfo(id);
        if(info==null||!context.getPackageName().equals(info.provider.getPackageName()))return false;
        String name=info.provider.getClassName();return name.equals(WeatherWidgetProvider.class.getName())||name.equals(WeatherWideWidgetProvider.class.getName())||name.equals(WeatherForecastWidgetProvider.class.getName());
    }
    public static void update(Context context,int id){refresh(context,id,()->{});}
    public static void refresh(Context context,int id){refresh(context,id,()->{});}
    public static void updateAll(Context context){refreshAll(context,()->{});}
    public static void refreshAll(Context context,Runnable completion){updateIds(context,widgetIds(context),completion);}
    public static void updateIds(Context context,int[] ids,Runnable completion){
        if(ids==null||ids.length==0){completion.run();return;}
        AtomicInteger remaining=new AtomicInteger(ids.length);
        for(int id:ids)refresh(context,id,()->{if(remaining.decrementAndGet()==0)completion.run();});
    }
    public static void refresh(Context context,int id,Runnable completion){
        Context app=context.getApplicationContext();
        if(!belongsToApp(app,id)){completion.run();return;}
        WidgetConfig config=WidgetConfig.load(app,id);WeatherRepository repository=WeatherRepository.get(app);
        try{render(app,id,config,repository.getCached(config),"",true);}catch(RuntimeException ignored){}
        repository.load(config,(data,error)->{
            try{
                // A configuration may have changed, or the host may have deleted the widget during I/O.
                if(belongsToApp(app,id)){
                    WidgetConfig current=WidgetConfig.load(app,id);
                    if(current.key().equals(config.key()))render(app,id,current,data,error,false);
                }
            }finally{completion.run();}
        });
    }
    public static void renderCached(Context context,int id){
        if(!belongsToApp(context,id))return;
        WidgetConfig config=WidgetConfig.load(context,id);render(context,id,config,WeatherRepository.get(context).getCached(config),"",false);
    }
    private static int background(String palette){
        return "copper".equals(palette)?R.drawable.widget_background_copper:"mint".equals(palette)?R.drawable.widget_background_mint:"night".equals(palette)?R.drawable.widget_background_night:R.drawable.widget_background_ubuntu;
    }
    private static void render(Context context,int id,WidgetConfig config,ForecastData data,String error,boolean loading){
        AppWidgetManager manager=AppWidgetManager.getInstance(context);AppWidgetProviderInfo info=manager.getAppWidgetInfo(id);if(info==null)return;
        manager.updateAppWidget(id,createViews(context,id,info.provider,manager.getAppWidgetOptions(id),config,data,error,loading));
    }
    /** Build the real RemoteViews separately from host delivery so layouts can be exercised on Android. */
    static RemoteViews createViews(Context context,int id,ComponentName provider,Bundle options,WidgetConfig config,ForecastData data,String error,boolean loading){
        String type=provider.getClassName();boolean forecast=type.equals(WeatherForecastWidgetProvider.class.getName()),wide=type.equals(WeatherWideWidgetProvider.class.getName());
        RemoteViews views=new RemoteViews(context.getPackageName(),forecast?R.layout.weather_widget_forecast:wide?R.layout.weather_widget_wide:R.layout.weather_widget_compact);
        WidgetPalette colors=WidgetPalette.from(config.palette);long now=System.currentTimeMillis();ForecastData.Hour current=data==null?null:data.current(now);
        views.setInt(R.id.widget_root,"setBackgroundResource",background(config.palette));
        views.setTextViewText(R.id.widget_temperature,WidgetPresentation.temperature(current));views.setTextColor(R.id.widget_temperature,colors.text);
        views.setTextViewText(R.id.widget_source,WidgetPresentation.sourceBadge(config,data,now));views.setTextColor(R.id.widget_source,colors.muted);
        String status=WidgetPresentation.status(data,now,config.timezone);
        if(data==null&&loading)status="Haetaan ennustetta…";
        else if(data==null&&error!=null&&!error.isEmpty())status="Offline · ennuste puuttuu";
        views.setContentDescription(R.id.widget_root,WidgetPresentation.description(config,data,now));
        Intent open=new Intent(context,MainActivity.class).setAction(Intent.ACTION_VIEW).setData(Uri.parse("saawidget://widget/"+id)).putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID,id).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TOP);
        views.setOnClickPendingIntent(R.id.widget_root,PendingIntent.getActivity(context,id,open,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE));
        if(wide||forecast){
            views.setTextViewText(R.id.widget_place,config.place);views.setTextColor(R.id.widget_place,colors.text);
            String shownStatus=wide?status.replace("Päivitetty ","").replace("Vanha ennuste · ","! ").replace("Offline · ","! "):status;
            views.setTextViewText(R.id.widget_status,shownStatus);views.setTextColor(R.id.widget_status,colors.muted);
            Intent refresh=new Intent(ACTION_REFRESH).setComponent(provider).setData(Uri.parse("saawidget://widget/"+id+"/refresh")).putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID,id);
            views.setOnClickPendingIntent(R.id.widget_refresh,PendingIntent.getBroadcast(context,id,refresh,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE));
            if(wide){views.setTextViewText(R.id.widget_wind,WidgetPresentation.wind(current).replace("Tuuli ",""));views.setTextColor(R.id.widget_wind,colors.text);}
        }
        if(!forecast){
            int minWidth=options.getInt(AppWidgetManager.OPTION_APPWIDGET_MIN_WIDTH,56);
            int minHeight=options.getInt(AppWidgetManager.OPTION_APPWIDGET_MIN_HEIGHT,56);
            float font=wide?Math.max(18,Math.min(28,Math.min(minWidth*.18f,(minHeight-8)*.75f))):Math.max(16,Math.min(40,Math.min(minWidth*.4f,(minHeight-18)*.75f)));
            float sourceFont=wide?8:9;
            if(!wide){
                float density=context.getResources().getDisplayMetrics().density,availableWidth=Math.max(8,minWidth-8)*density;
                Paint measure=new Paint(Paint.ANTI_ALIAS_FLAG);measure.setTypeface(Typeface.create("sans-serif",Typeface.BOLD));measure.setTextSize(font*density);
                float textWidth=measure.measureText(WidgetPresentation.temperature(current));
                if(textWidth>availableWidth)font*=availableWidth/textWidth;
                measure.setTextSize(font*density);Paint.FontMetrics metrics=measure.getFontMetrics();float availableHeight=Math.max(8,minHeight-19)*density;
                if(metrics.descent-metrics.ascent>availableHeight)font*=availableHeight/(metrics.descent-metrics.ascent);
                measure.setTypeface(Typeface.create("sans-serif",Typeface.NORMAL));measure.setTextSize(sourceFont*density);
                float sourceWidth=measure.measureText(WidgetPresentation.sourceBadge(config,data,now));
                if(sourceWidth>availableWidth)sourceFont*=availableWidth/sourceWidth;
            }
            // A 1-cell widget has fixed geometry: keep both values visible when system fonts grow.
            views.setTextViewTextSize(R.id.widget_temperature,TypedValue.COMPLEX_UNIT_DIP,font);
            views.setTextViewTextSize(R.id.widget_source,TypedValue.COMPLEX_UNIT_DIP,sourceFont);
            if(wide){views.setTextViewTextSize(R.id.widget_place,TypedValue.COMPLEX_UNIT_DIP,9);views.setTextViewTextSize(R.id.widget_wind,TypedValue.COMPLEX_UNIT_DIP,9);views.setTextViewTextSize(R.id.widget_status,TypedValue.COMPLEX_UNIT_DIP,8);}
        }
        if(forecast){
            views.setTextViewTextSize(R.id.widget_temperature,TypedValue.COMPLEX_UNIT_DIP,20);
            int width=options.getInt(AppWidgetManager.OPTION_APPWIDGET_MIN_WIDTH,280),height=options.getInt(AppWidgetManager.OPTION_APPWIDGET_MIN_HEIGHT,150);
            float density=Math.min(2f,context.getResources().getDisplayMetrics().density);
            Bitmap graph=ForecastGraph.render(data,config,now,(int)(Math.max(180,width-16)*density),(int)(Math.max(40,height-66)*density));
            views.setImageViewBitmap(R.id.widget_graph,graph);
            views.setContentDescription(R.id.widget_graph,WidgetPresentation.graphDescription(config,data,now));
        }
        return views;
    }
}
