"""Same 777-local-day Veri Aika rules as Ajanlaskut ja Sää 1.12.3."""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

ZONE = ZoneInfo('Europe/Helsinki')
EPOCH = date(2026, 6, 26)
CUTOVER = time(1, 7, 7)


def blood_label(moment):
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError('Aikaleima tarvitsee aikavyöhykkeen.')
    local = moment.astimezone(ZONE)
    day = local.date() - timedelta(days=local.time() < CUTOVER)
    ordinal = (day - EPOCH).days
    if ordinal < 0:
        return f'{-ordinal}. päivä ennen Veri Ajan alkua', ''
    position = ordinal % 777
    return (f'{position % 7 + 1}. päivä · {position // 7 + 1}. viikko · vuosi {ordinal // 777 + 1:04d}',
            f'Vuoden päivä {position + 1}/777')
