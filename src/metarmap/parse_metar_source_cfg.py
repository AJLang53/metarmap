from __future__ import annotations
from metarmap.METAR_SOURCE import METAR_SOURCE, Demo_METAR_Source
from METAR import Aviation_Weather_METAR_Thread

def parse_metar_source_cfg(dict: dict[str, str | int]) -> METAR_SOURCE:
    try:
        type = dict['type']
    except KeyError:
        raise ValueError(f'No type in dict')
    
    if type == 'Aviation_Weather_METAR_Thread':
        return Aviation_Weather_METAR_Thread.from_cfg(dict)
    elif type == 'Demo_METAR_Source':
        return Demo_METAR_Source.from_cfg(dict)