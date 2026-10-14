package fi.jakke77.saawidget;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.view.View;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Locale;

/** Native temperature line and rain bars, aligned to hour starts. */
public final class ForecastGraphView extends View {
    private ForecastData data; private WidgetConfig config; private final Paint p=new Paint(Paint.ANTI_ALIAS_FLAG);
    public ForecastGraphView(Context context){super(context);setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_YES);}
    public void setForecast(ForecastData data,WidgetConfig config){this.data=data;this.config=config;StringBuilder a=new StringBuilder("Tuntiennuste. ");if(data!=null)for(ForecastData.Hour h:data.upcoming(System.currentTimeMillis(),config.hours))a.append(time(h.epochMs)).append(", lämpötila ").append(Math.round(h.tempC)).append(" astetta, sade ").append(Double.isNaN(h.rainMm)?"ei tiedossa":String.format(Locale.getDefault(),"%.1f millimetriä",h.rainMm)).append(". ");setContentDescription(a);invalidate();}
    private String time(long t){return DateTimeFormatter.ofPattern("HH",Locale.getDefault()).withZone(ZoneId.of(config.timezone)).format(Instant.ofEpochMilli(t));}
    @Override protected void onDraw(Canvas canvas){super.onDraw(canvas);if(data==null||config==null)return;List<ForecastData.Hour> rows=data.upcoming(System.currentTimeMillis(),config.hours);if(rows.isEmpty())return;
        float d=getResources().getDisplayMetrics().density;float left=38*d,right=getWidth()-18*d,top=28*d,bottom=getHeight()-72*d;double min=Double.POSITIVE_INFINITY,max=Double.NEGATIVE_INFINITY,rainMax=.5;
        for(ForecastData.Hour h:rows){min=Math.min(min,h.tempC);max=Math.max(max,h.tempC);if(Double.isFinite(h.rainMm))rainMax=Math.max(rainMax,h.rainMm);}min=Math.floor(min-1);max=Math.ceil(max+1);if(max-min<4){double mid=(max+min)/2;min=mid-2;max=mid+2;}
        p.setTypeface(android.graphics.Typeface.create("sans-serif",android.graphics.Typeface.NORMAL));p.setTextSize(11*d);p.setStrokeWidth(d);
        for(int n=0;n<=4;n++){float y=top+(bottom-top)*n/4;p.setColor(Color.rgb(71,56,78));canvas.drawLine(left,y,right,y,p);p.setColor(Color.rgb(198,174,189));canvas.drawText(String.format(Locale.getDefault(),"%.0f°",max-(max-min)*n/4),2*d,y+4*d,p);}
        Path line=new Path();long start=System.currentTimeMillis()/ForecastData.HOUR*ForecastData.HOUR;long previous=Long.MIN_VALUE;
        for(int i=0;i<rows.size();i++){ForecastData.Hour h=rows.get(i);float x=left+(float)(h.epochMs-start)/(Math.max(1,config.hours-1)*ForecastData.HOUR)*(right-left);float y=top+(float)((max-h.tempC)/(max-min))*(bottom-top);if(previous==Long.MIN_VALUE||h.epochMs-previous>ForecastData.HOUR)line.moveTo(x,y);else line.lineTo(x,y);previous=h.epochMs;
            if(Double.isFinite(h.rainMm)&&h.rainMm>0){p.setColor(Color.rgb(130,189,233));float rainY=getHeight()-42*d;float height=(float)(h.rainMm/rainMax)*23*d;canvas.drawRect(x-3*d,rainY-height,x+3*d,rainY,p);}else if(!Double.isFinite(h.rainMm)){p.setColor(Color.rgb(198,174,189));p.setTextAlign(Paint.Align.CENTER);canvas.drawText("—",x,getHeight()-42*d,p);p.setTextAlign(Paint.Align.LEFT);} if(i%Math.max(1,rows.size()/6)==0||i==rows.size()-1){p.setColor(Color.rgb(198,174,189));p.setTextAlign(Paint.Align.CENTER);canvas.drawText(time(h.epochMs),x,getHeight()-23*d,p);p.setTextAlign(Paint.Align.LEFT);}}
        p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(2.5f*d);p.setColor(Color.rgb(233,84,32));canvas.drawPath(line,p);p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(198,174,189));p.setTextSize(11*d);canvas.drawText("Sadeasteikko 0–"+String.format(Locale.getDefault(),"%.1f",rainMax)+" mm/h",left,getHeight()-3*d,p);
    }
}
