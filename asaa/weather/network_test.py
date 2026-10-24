"""Explicit live checks in temporary storage; no user settings or cache writes."""
import argparse
from functools import partial
import json
from pathlib import Path
import ssl
from tempfile import TemporaryDirectory
from urllib.request import urlopen
from .providers import Place, provider_caches
from . import network


def main():
    parser = argparse.ArgumentParser(description='Sääpalvelujen HTTPS-yhteystesti')
    parser.add_argument('--providers', choices=('yr', 'fmi', 'foreca'), nargs='+', default=['yr', 'fmi', 'foreca'])
    parser.add_argument('--bundle-only', action='store_true', help='Testaa mukana toimitetuilla julkisilla varmenteilla')
    args = parser.parse_args()
    opener = network.urlopen
    if args.bundle_only:
        import certifi
        context = ssl.create_default_context(cafile=certifi.where())
        opener = partial(urlopen, context=context)
    failed = False
    with TemporaryDirectory(prefix='ajanlaskut-network-') as folder:
        # Same coordinates as the reported Oinaansuo forecast, no user location read.
        place = Place('Oinaansuo, Oulu', 65.07074, 25.51946)
        for key, cache in provider_caches(place, Path(folder)).items():
            if key not in args.providers: continue
            cache.opener = opener
            try:
                forecast = cache.fetch()
                print(json.dumps({'provider': key, 'status': 'OK', 'hours': len(forecast.hours),
                                  'first_hour': forecast.hours[0].time.isoformat()}), flush=True)
                if forecast.error: raise ValueError(forecast.error)
            except Exception as error:
                failed = True
                cause = error.__cause__ or error
                reason = getattr(cause, 'reason', cause)
                print(json.dumps({'provider': key, 'status': 'FAILED', 'message': str(error),
                                  'error_type': type(reason).__name__, 'detail': str(reason)}), flush=True)
    return 1 if failed else 0


if __name__ == '__main__': raise SystemExit(main())
