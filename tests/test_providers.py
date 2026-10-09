"""Rain intervals, shared scales, parser safety, cache isolation and DST."""
from datetime import datetime,timedelta
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock
from urllib.parse import parse_qs, urlparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from asaa.weather.providers import *

NOW=datetime(2026,10,5,2,20,tzinfo=UTC)

def foreca_body(rows, stamp=NOW):
    return 'var page_settings = {t:'+str(int(stamp.timestamp()))+'}; data_1h: '+repr(rows)

def row(day='5.10.',hour='05.00',rain=0,temp=5):
    return dict(dt=day,hi=hour,r=rain,t=temp,ws=4,wd=180,wg=8,s='n400',tf=2)

class ProviderTests(unittest.TestCase):
    def test_extended_fmi_request_covers_last_rain_interval(self):
        query = parse_qs(urlparse(SiteCache('fmi', Place()).request(NOW).full_url).query)
        start = instant(query['starttime'][0])
        end = instant(query['endtime'][0])
        self.assertEqual(end-start, timedelta(hours=25))
        self.assertEqual(query['timestep'], ['60'])

    def test_24_slots_across_dst_preserve_every_real_hour(self):
        start = datetime(2026,10,25,0,tzinfo=UTC)
        times = slots(start,count=24)
        self.assertEqual(len(times),24)
        self.assertEqual([t.astimezone(TZ).hour for t in times[:2]],[3,3])
        self.assertEqual(times[-1]-times[0],timedelta(hours=23))

    def test_foreca_rain_uses_following_interval_end(self):
        body=foreca_body([row(rain=8),row(hour='06.00',rain=1.5)])
        f=parse_foreca(body,NOW,NOW)
        self.assertEqual(f.hours[0].rain,1.5)
        self.assertIsNone(f.hours[1].rain)
        self.assertEqual(f.hours[0].feels_like,2)

    def test_foreca_parser_never_executes_expressions(self):
        body=foreca_body([row()]).replace("'t': 5","'t': __import__('os').system('false')")
        with self.assertRaises((ValueError,SyntaxError)): parse_foreca(body,NOW,NOW)

    def test_foreca_dst_keeps_two_03_hours(self):
        stamp=datetime(2026,10,25,0,tzinfo=TZ)
        f=parse_foreca(foreca_body([row('25.10.','03.00'),row('25.10.','03.00'),row('25.10.','04.00')],stamp),stamp,stamp)
        times=[h.time for h in f.hours]
        self.assertEqual(times[1]-times[0],timedelta(hours=1))
        self.assertEqual(times[2]-times[1],timedelta(hours=1))

    def test_foreca_new_year_uses_page_timestamp(self):
        stamp=datetime(2026,12,31,23,tzinfo=TZ)
        f=parse_foreca(foreca_body([row('31.12.','23.00'),row('1.1.','00.00')],stamp),stamp,stamp)
        self.assertEqual(f.hours[1].time.astimezone(TZ).year,2027)

    def test_fmi_xml_combines_parameters_and_shifts_rain(self):
        parts=[]
        for t,rain in [('2026-10-05T02:00:00Z',9),('2026-10-05T03:00:00Z',.8)]:
            for key,value in dict(Temperature=5,WindSpeedMS=3,WindDirection=90,Precipitation1h=rain,WeatherSymbol3=32).items():
                parts.append(f'<e:BsWfsElement><e:Time>{t}</e:Time><e:ParameterName>{key}</e:ParameterName><e:ParameterValue>{value}</e:ParameterValue></e:BsWfsElement>')
        f=parse_fmi('<root xmlns:e="urn:test">'+''.join(parts)+'</root>',NOW,NOW)
        self.assertEqual(f.hours[0].rain,.8)
        self.assertIsNone(f.hours[0].gust)
        self.assertEqual(f.hours[0].symbol,'cloudyrain')

    def test_same_slots_and_scales_for_every_source(self):
        times=slots(NOW)
        a=Forecast((Hour(times[0],2,0,2,3,0,'cloudy'),),NOW,NOW)
        b=Forecast((Hour(times[1],18,4,8,12,0,'cloudy'),),NOW,NOW)
        expected=common_scales([a,b],times)
        self.assertEqual(common_scales([b,a],times),expected)
        self.assertEqual(aligned(b,times)[0],None)
        self.assertEqual(aligned(b,times)[1].temperature,18)
        self.assertLess(expected.temperature[0],2)
        self.assertGreater(expected.temperature[1],18)
        self.assertGreater(expected.wind,12)
        self.assertEqual(expected.rain,4)

    def test_separate_location_caches_and_legacy_shared_met(self):
        with tempfile.TemporaryDirectory() as d:
            a=provider_caches(Place(),Path(d))
            b=provider_caches(Place('Helsinki',60.17,24.94),Path(d))
            for key in PROVIDERS: self.assertNotEqual(a[key].path,b[key].path)
            self.assertEqual(a['yr'].path.name,'forecast.json')
            self.assertEqual(a['yr'].url,URL)

    def test_site_offline_backoff_and_preserves_data(self):
        with tempfile.TemporaryDirectory() as d:
            opener=Mock(side_effect=OSError('offline'))
            c=SiteCache('foreca',Place(),Path(d),opener)
            atomic_write(c.path,json.dumps(dict(provider='foreca',location=Place().key,
                body=foreca_body([row(),row(hour='06.00')]),fetched=NOW.isoformat(),next_request=NOW.isoformat())))
            f=c.fetch(NOW)
            self.assertTrue(f.error)
            c.fetch(NOW+timedelta(minutes=1))
            self.assertEqual(opener.call_count,1)

    def test_bad_site_body_does_not_replace_good_cached_data(self):
        with tempfile.TemporaryDirectory() as d:
            response=Mock(); response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False)
            response.read.return_value=b'<html>changed site</html>';response.headers={}
            c=SiteCache('foreca',Place(),Path(d),Mock(return_value=response))
            original=foreca_body([row(),row(hour='06.00')])
            atomic_write(c.path,json.dumps(dict(provider='foreca',location=Place().key,body=original,fetched=NOW.isoformat())))
            f=c.fetch(NOW)
            self.assertTrue(f.error)
            self.assertEqual(c.read()['body'],original)

    def test_symbols_are_our_own_normalized_codes(self):
        self.assertEqual(foreca_symbol('d421'),'cloudysleet_day')
        self.assertEqual(foreca_symbol('n000'),'clearsky_night')
        self.assertEqual(fmi_symbol(63),'cloudyrainthunder')
        self.assertEqual(fmi_symbol(53),'cloudysnow')
        self.assertEqual(fmi_symbol(999),'unknown')

if __name__=='__main__':unittest.main()
