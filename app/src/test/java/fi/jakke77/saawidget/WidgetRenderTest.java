package fi.jakke77.saawidget;

import android.appwidget.AppWidgetManager;
import android.content.ComponentName;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.os.Bundle;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.RemoteViews;
import android.widget.TextView;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import java.io.File;
import java.io.FileOutputStream;
import java.util.ArrayList;
import java.util.List;
import static org.junit.Assert.*;

/** Execute Android's real RemoteViews layout/actions and software drawing, without a launcher. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=28)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class WidgetRenderTest {
    private Context context(){return RuntimeEnvironment.getApplication();}
    private WidgetConfig config(String provider,String palette){return new WidgetConfig(provider,"Pöllönkangas, Oulu",65.0701,25.5071,"Europe/Helsinki",palette,12);}
    private ForecastData fixture(WidgetConfig config,boolean offline){
        long now=System.currentTimeMillis(),start=now/ForecastData.HOUR*ForecastData.HOUR;List<ForecastData.Hour> hours=new ArrayList<>();
        for(int i=0;i<12;i++)hours.add(new ForecastData.Hour(start+i*ForecastData.HOUR,-17.8+i*1.5,i==4?Double.NaN:(i>6?.2*(i-6):0),3.2,"cloudy"));
        return new ForecastData(config.provider,config.place,config.latitude,config.longitude,offline?now-3*ForecastData.HOUR:now,hours,offline?"Ei verkkoyhteyttä":"");
    }
    private View render(Class<?> provider,WidgetConfig config,ForecastData data,int widthDp,int heightDp){
        Context context=context();Bundle options=new Bundle();options.putInt(AppWidgetManager.OPTION_APPWIDGET_MIN_WIDTH,widthDp);options.putInt(AppWidgetManager.OPTION_APPWIDGET_MIN_HEIGHT,heightDp);
        RemoteViews remote=WeatherWidgetUpdater.createViews(context,42,new ComponentName(context,provider),options,config,data,"",false);
        View view=remote.apply(context,new FrameLayout(context));float density=context.getResources().getDisplayMetrics().density;
        int width=Math.round(widthDp*density),height=Math.round(heightDp*density);
        view.measure(View.MeasureSpec.makeMeasureSpec(width,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(height,View.MeasureSpec.EXACTLY));view.layout(0,0,width,height);
        return view;
    }
    private void assertTextFitsVertically(View view,int id){TextView text=view.findViewById(id);assertTrue("Visible height for "+id,text.getHeight()>0);assertTrue("Line should fit at minimum widget height: "+text.getText(),text.getLineHeight()<=text.getHeight());}
    private void export(View view,String filename)throws Exception{
        String directory=System.getProperty("saawidget.qaDir");if(directory==null)return;
        Bitmap bitmap=Bitmap.createBitmap(view.getWidth(),view.getHeight(),Bitmap.Config.ARGB_8888);view.draw(new Canvas(bitmap));
        File folder=new File(directory);assertTrue(folder.isDirectory()||folder.mkdirs());try(FileOutputStream out=new FileOutputStream(new File(folder,filename))){assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,out));}
    }
    @Test public void oneByOneReallyAppliesActionsAndFitsAtMinimumHeight()throws Exception{
        WidgetConfig config=config("fmi","ubuntu");View view=render(WeatherWidgetProvider.class,config,fixture(config,true),40,40);
        TextView temperature=view.findViewById(R.id.widget_temperature),source=view.findViewById(R.id.widget_source);
        assertEquals("-18°",temperature.getText().toString());assertEquals("enn. · IL !",source.getText().toString());
        assertTextFitsVertically(view,R.id.widget_temperature);assertTextFitsVertically(view,R.id.widget_source);
        assertTrue(temperature.getPaint().measureText(temperature.getText().toString())<=temperature.getWidth());
        assertTrue(source.getPaint().measureText(source.getText().toString())<=source.getWidth()+.1f);
        assertTrue(view.getContentDescription().toString().contains("Ilmatieteen laitos"));
        export(render(WeatherWidgetProvider.class,config,fixture(config,false),76,76),"widget-1x1-fixture.png");
    }
    @Test public void wideLayoutKeepsTemperatureWindAndSourceAtOneCellHeight()throws Exception{
        WidgetConfig config=config("yr","copper");View view=render(WeatherWideWidgetProvider.class,config,fixture(config,false),110,40);
        assertEquals("-18°",((TextView)view.findViewById(R.id.widget_temperature)).getText().toString());
        assertEquals("3,2 m/s",((TextView)view.findViewById(R.id.widget_wind)).getText().toString());
        for(int id:new int[]{R.id.widget_temperature,R.id.widget_place,R.id.widget_wind,R.id.widget_source,R.id.widget_status})assertTextFitsVertically(view,id);
        assertTrue(view.findViewById(R.id.widget_refresh).isClickable());
        export(render(WeatherWideWidgetProvider.class,config,fixture(config,false),166,76),"widget-2x1-fixture.png");
    }
    @Test public void forecastLayoutAcceptsRealBitmapAndAccessibleSourceValues()throws Exception{
        WidgetConfig config=config("openmeteo","night");View view=render(WeatherForecastWidgetProvider.class,config,fixture(config,false),280,150);
        ImageView graph=view.findViewById(R.id.widget_graph);assertNotNull(graph.getDrawable());assertTrue(graph.getHeight()>0);
        assertTextFitsVertically(view,R.id.widget_temperature);
        assertTrue(graph.getContentDescription().toString().contains("Open-Meteo"));assertTrue(graph.getContentDescription().toString().contains("sade ei tiedossa"));
        assertTrue(view.findViewById(R.id.widget_refresh).isClickable());
        export(view,"widget-4x2-fixture.png");export(render(WeatherForecastWidgetProvider.class,config,fixture(config,false),280,300),"widget-4x4-fixture.png");
    }
    @Test public void noCurrentSourceHourStaysBlankInAppliedRemoteViews(){
        WidgetConfig config=config("fmi","mint");ForecastData all=fixture(config,false);List<ForecastData.Hour> future=new ArrayList<>(all.hours);future.remove(0);
        ForecastData missing=new ForecastData(all.provider,all.place,all.latitude,all.longitude,all.fetchedAt,future,"");
        View view=render(WeatherWidgetProvider.class,config,missing,76,76);
        assertEquals("—",((TextView)view.findViewById(R.id.widget_temperature)).getText().toString());assertTrue(view.getContentDescription().toString().contains("puuttuu"));
    }
    @Test public void coldTwoDigitTemperatureFitsOneCellWithLargerSystemFonts(){
        WidgetConfig config=config("fmi","ubuntu");ForecastData all=fixture(config,false);List<ForecastData.Hour> hours=new ArrayList<>(all.hours);
        ForecastData.Hour first=hours.get(0);hours.set(0,new ForecastData.Hour(first.epochMs,-42,0,first.windMps,first.symbol));
        ForecastData cold=new ForecastData(all.provider,all.place,all.latitude,all.longitude,all.fetchedAt,hours,"");
        for(float scale:new float[]{1f,1.3f}){
            RuntimeEnvironment.setFontScale(scale);View view=render(WeatherWidgetProvider.class,config,cold,40,40);TextView temperature=view.findViewById(R.id.widget_temperature);
            assertEquals("-42°",temperature.getText().toString());assertTextFitsVertically(view,R.id.widget_temperature);assertTextFitsVertically(view,R.id.widget_source);
            assertTrue("Entire cold temperature fits at font scale "+scale,temperature.getPaint().measureText(temperature.getText().toString())<=temperature.getWidth());
        }
    }
    @Test public void graphActuallyDrawsAndRemainsWithinRemoteViewsBitmapBudget()throws Exception{
        WidgetConfig config=config("fmi","ubuntu");ForecastData data=fixture(config,false);Bitmap image=ForecastGraph.render(data,config,System.currentTimeMillis(),1000,1000);
        assertTrue(image.getWidth()<=640);assertTrue(image.getHeight()<=320);assertTrue(image.getAllocationByteCount()<=600000);
        int orange=WidgetPalette.from("ubuntu").accent,blue=WidgetPalette.from("ubuntu").rain;boolean line=false,rain=false;
        for(int y=0;y<image.getHeight();y++)for(int x=0;x<image.getWidth();x++){int color=image.getPixel(x,y);if(color==orange)line=true;if(color==blue)rain=true;}
        assertTrue("Native canvas produced a temperature line",line);assertTrue("Large widget still produced rain after bitmap-size cap",rain);
    }
    @Test public void widgetSettingsPersistIndependentlyFromAppDefaults(){
        WidgetConfig app=config("yr","ubuntu"),first=config("fmi","copper"),second=new WidgetConfig("openmeteo","Helsinki",60.17,24.94,"Europe/Helsinki","night",24);
        app.save(context(),-1);first.save(context(),101);second.save(context(),102);
        assertEquals("yr",WidgetConfig.load(context(),-1).provider);assertEquals("fmi",WidgetConfig.load(context(),101).provider);
        WidgetConfig restored=WidgetConfig.load(context(),102);assertEquals("openmeteo",restored.provider);assertEquals("Helsinki",restored.place);assertEquals(24,restored.hours);assertEquals("night",restored.palette);
        WidgetConfig.delete(context(),101);assertEquals("yr",WidgetConfig.load(context(),101).provider);assertEquals("openmeteo",WidgetConfig.load(context(),102).provider);
    }
}
