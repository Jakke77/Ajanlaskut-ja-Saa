package fi.jakke77.saawidget;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Shader;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Locale;

/** Native graph of the selected source's hourly values; never an image from a web page. */
public final class ForecastGraph {
    private ForecastGraph() {}
    public static Bitmap render(ForecastData data, WidgetConfig config, long now, int width, int height) {
        // Keep RemoteViews comfortably below the Binder transaction limit on high-density phones.
        width = Math.max(180, Math.min(640, width)); height = Math.max(72, Math.min(320, height));
        if ((long)width * height > 150000) height = 150000 / width;
        Bitmap image = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
        Canvas canvas = new Canvas(image); WidgetPalette colors = WidgetPalette.from(config.palette);
        Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG); float unit = Math.max(.65f, Math.min(width / 320f,height / 95f));
        List<ForecastData.Hour> hours = data == null ? java.util.Collections.emptyList() : data.upcoming(now, config.hours);
        paint.setColor(colors.muted); paint.setTextSize(10 * unit);
        if (hours.isEmpty()) { paint.setTextAlign(Paint.Align.CENTER);canvas.drawText("Ennuste puuttuu · avaa sovellus", width/2f, height/2f, paint); return image; }
        boolean showRain = height >= 110 * unit;
        float left = 30 * unit, right = width - 10 * unit, top = 16 * unit;
        float bottom = height - (showRain ? 48 : 23) * unit;
        bottom = Math.max(top + 18 * unit, bottom);
        double min = Double.POSITIVE_INFINITY, max = Double.NEGATIVE_INFINITY, rainMax = .5;
        for (ForecastData.Hour hour : hours) { min=Math.min(min,hour.tempC);max=Math.max(max,hour.tempC);if(Double.isFinite(hour.rainMm))rainMax=Math.max(rainMax,hour.rainMm); }
        min = Math.floor(min - 1); max = Math.ceil(max + 1);
        float usable = right-left;
        long start=now/ForecastData.HOUR*ForecastData.HOUR;
        double span=(config.hours-1)*ForecastData.HOUR;
        paint.setColor(colors.muted); paint.setTextAlign(Paint.Align.LEFT); canvas.drawText("°C", 0, 10 * unit, paint);
        int gridCount = bottom-top < 45*unit ? 2 : 3;
        for (int i=0;i<gridCount;i++) {
            float y=top+(bottom-top)*i/(gridCount-1);double temp=max-(max-min)*i/(gridCount-1);
            paint.setColor(colors.muted);paint.setTextAlign(Paint.Align.RIGHT);canvas.drawText(String.format(Locale.ROOT,"%.0f",temp),left-6*unit,y+3*unit,paint);
            paint.setColor((colors.muted & 0x00ffffff) | 0x35000000);paint.setStrokeWidth(unit);canvas.drawLine(left,y,right,y,paint);
        }
        Path line = new Path(), fill = new Path();long previous=Long.MIN_VALUE;float previousX=left;
        for(int i=0;i<hours.size();i++) {
            ForecastData.Hour hour=hours.get(i);
            float x = left+(float)((hour.epochMs-start)/span)*usable;
            float y = top+(float)((max-hours.get(i).tempC)/(max-min))*(bottom-top);
            if(previous==Long.MIN_VALUE||hour.epochMs-previous>ForecastData.HOUR){
                if(previous!=Long.MIN_VALUE){fill.lineTo(previousX,bottom);fill.close();}
                line.moveTo(x,y);fill.moveTo(x,bottom);fill.lineTo(x,y);
            }else{line.lineTo(x,y);fill.lineTo(x,y);}
            previous=hour.epochMs;previousX=x;
        }
        fill.lineTo(previousX,bottom);fill.close();
        paint.setStyle(Paint.Style.FILL);paint.setShader(new LinearGradient(0,top,0,bottom,(colors.accent&0x00ffffff)|0x65000000,colors.accent&0x00ffffff,Shader.TileMode.CLAMP));canvas.drawPath(fill,paint);paint.setShader(null);
        paint.setColor(colors.accent);paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(2.5f*unit);paint.setStrokeCap(Paint.Cap.ROUND);canvas.drawPath(line,paint);paint.setStyle(Paint.Style.FILL);
        // Points remain visible for an isolated hour on either side of a missing source interval.
        for(ForecastData.Hour hour:hours){float x=left+(float)((hour.epochMs-start)/span)*usable;float y=top+(float)((max-hour.tempC)/(max-min))*(bottom-top);canvas.drawCircle(x,y,1.8f*unit,paint);}
        DateTimeFormatter time = DateTimeFormatter.ofPattern("HH",Locale.ROOT).withZone(ZoneId.of(config.timezone));
        int interval = config.hours > 16 ? 6 : 3;
        paint.setColor(colors.muted);paint.setTextSize(10*unit);
        for(int slot=0;slot<config.hours;slot++) {
            if(slot%interval!=0 && slot!=config.hours-1)continue;
            if(slot==config.hours-1 && slot%interval!=0 && slot%interval<2)continue;
            float x=left+(float)slot/(config.hours-1)*usable;
            paint.setTextAlign(slot==0?Paint.Align.LEFT:slot==config.hours-1?Paint.Align.RIGHT:Paint.Align.CENTER);
            canvas.drawText(time.format(Instant.ofEpochMilli(start+slot*ForecastData.HOUR)),x,height-4*unit,paint);
        }
        if(showRain) {
            float rainBottom = height-20*unit, rainTop = bottom+8*unit, barWidth=Math.max(2*unit, Math.min(9*unit, usable/hours.size()*.65f));
            boolean knownRain=false,missingRain=false;
            for(int i=0;i<hours.size();i++) {
                double rain=hours.get(i).rainMm;float x=left+(float)((hours.get(i).epochMs-start)/span)*usable;
                if(!Double.isFinite(rain)){missingRain=true;paint.setColor(colors.muted);paint.setStrokeWidth(unit);canvas.drawLine(x-2*unit,rainBottom-2*unit,x+2*unit,rainBottom-2*unit,paint);continue;}
                knownRain=true;if(rain<=0)continue;
                float y=rainBottom-(float)(rain/rainMax)*(rainBottom-rainTop);paint.setColor(colors.rain);
                canvas.drawRoundRect(x-barWidth/2,y,x+barWidth/2,rainBottom,unit,unit,paint);
            }
            paint.setColor(colors.rain);paint.setTextAlign(Paint.Align.LEFT);paint.setTextSize(8*unit);
            canvas.drawText(knownRain?"mm/h":"Sade —",0,rainTop+8*unit,paint);
            if(knownRain)canvas.drawText(String.format(new Locale("fi","FI"),"%.1f",rainMax),0,rainBottom-2*unit,paint);
            if(knownRain&&missingRain){paint.setTextAlign(Paint.Align.RIGHT);paint.setColor(colors.muted);canvas.drawText("— ei tietoa",right,rainTop+5*unit,paint);}
        }
        return image;
    }
}
