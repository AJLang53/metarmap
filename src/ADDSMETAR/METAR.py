import logging
from datetime import datetime, timezone

class METAR:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._raw_text = None
        self._observation_time = None
        self._latitude = None
        self._longitude = None
        self._temp_c = None
        self._dewpoint_c = None
        self._wind_dir_degrees = None
        self._wind_speed_kt = None
        self._wind_gust_kt = None
        self._visibility_statute_mi = None
        self._altim_in_hg = None
        self._sea_level_pressure_mb = None
        self._wx_string = None
        self._flight_category = None
        self._precip_in = None
        self._metar_type = None
        self._elevation_m = None
        self._quality_control_flag = None
        self._sky_condition = []
        return
    
    @property
    def raw_text(self):
        return self._raw_text

    @raw_text.setter
    def raw_text(self,raw_text):
        self._raw_text = raw_text

    @property
    def observation_time(self):
        return self._observation_time
    
    @observation_time.setter
    def observation_time(self,observation_time: str):
        '''
        Convert observation_time to datetime object for easier use later
        '''
        observationTimeObj = None
        try:
            year = int(observation_time.split('T')[0].split('-')[0])
            month = int(observation_time.split('T')[0].split('-')[1])
            day = int(observation_time.split('T')[0].split('-')[2])
            hourzulu = int(observation_time.split('T')[1].split(':')[0])
            minute = int(observation_time.split('T')[1].split(':')[1])
            second = int(observation_time.split('T')[1].split(':')[2].split('Z')[0])
        except:
            self.logger.exception('Error parsing observationTime')

        try:
            observationTimeObj = datetime(year,month,day,hourzulu,minute,second,tzinfo=timezone.utc)
        except:
            self.logger.exception(f'Error creating datetime object for observationTime: {observation_time}')

        if observationTimeObj != None:
            self._observation_time = observationTimeObj
        else:
            self._observation_time = observation_time

    @property
    def latitude(self):
        return self._latitude
    
    @latitude.setter
    def latitude(self,val):
        float_val = None
        try:
            float_val = float(val)
        except Exception as e:
            self.logger.exception(f'Failed converting {val} to float')
        if float_val != None:
            self._latitude = float_val
        else:
            self._latitude = val

    @property
    def longitude(self):
        return self._longitude
    
    @longitude.setter
    def longitude(self,val):
        float_val = None
        try:
            float_val = float(val)
        except Exception as e:
            self.logger.exception(f'Failed converting {val} to float')
        if float_val != None:
            self._longitude = float_val
        else:
            self._longitude = val

    @property
    def temp_c(self):
        return self._temp_c
    
    @temp_c.setter
    def temp_c(self,val):
        float_val = None
        try:
            float_val = float(val)
        except Exception as e:
            self.logger.exception(f'Failed converting {val} to float')
        if float_val != None:
            self._temp_c = float_val
        else:
            self._temp_c = val

    @property
    def dewpoint_c(self):
        return self._temp_c
    
    @dewpoint_c.setter
    def dewpoint_c(self,val):
        float_val = None
        try:
            float_val = float(val)
        except Exception as e:
            self.logger.exception(f'Failed converting {val} to float')
        if float_val != None:
            self._dewpoint_c = float_val
        else:
            self._dewpoint_c = val

    @property
    def wind_dir_degrees(self):
        return self._wind_dir_degrees
    
    @wind_dir_degrees.setter
    def wind_dir_degrees(self,val):
        float_val = None
        try:
            float_val = float(val)
        except Exception as e:
            self.logger.exception(f'Failed converting {val} to float')
        if float_val != None:
            self._wind_dir_degrees = float_val
        else:
            self._wind_dir_degrees = val

    @property
    def wind_speed_kt(self):
        return self._wind_speed_kt
    
    @wind_speed_kt.setter
    def wind_speed_kt(self,val):
        int_val = None
        try:
            int_val = int(val)
        except Exception as e:
            self.logger.exception(f'Failed converting {val} to int')
        if int_val != None:
            self._wind_speed_kt = int_val
        else:
            self._wind_speed_kt = val

    @property
    def wind_gust_kt(self):
        return self._wind_gust_kt
    
    @wind_gust_kt.setter
    def wind_gust_kt(self,val):
        int_val = None
        try:
            int_val = int(val)
        except Exception as e:
            self.logger.exception(f'Failed converting {val} to int')
        if int_val != None:
            self._wind_gust_kt = int_val
        else:
            self._wind_gust_kt = val

    @property
    def visibility_statute_mi(self):
        return self._visibility_statute_mi
    
    @visibility_statute_mi.setter
    def visibility_statute_mi(self,val):
        float_val = None
        try:
            float_val = float(val)
        except Exception as e:
            self.logger.exception(f'Failed converting {val} to float')
        if float_val != None:
            self._visibility_statute_mi = float_val
        else:
            self._visibility_statute_mi = val

    @property
    def altim_in_hg(self):
        return self._altim_in_hg
    
    @altim_in_hg.setter
    def altim_in_hg(self,val):
        float_val = None
        try:
            float_val = float(val)
        except Exception as e:
            self.logger.exception(f'Failed converting {val} to float')
        if float_val != None:
            self._altim_in_hg = float_val
        else:
            self._altim_in_hg = val

    @property
    def sea_level_pressure_mb(self):
        return self._sea_level_pressure_mb
    
    @sea_level_pressure_mb.setter
    def sea_level_pressure_mb(self,val):
        float_val = None
        try:
            float_val = float(val)
        except Exception as e:
            self.logger.exception(f'Failed converting {val} to float')
        if float_val != None:
            self._sea_level_pressure_mb = float_val
        else:
            self._sea_level_pressure_mb = val

    @property
    def wx_string(self):
        return self._wx_string
    
    @wx_string.setter
    def wx_string(self,val):
        '''
        TODO decode wx_strings https://www.aviationweather.gov/docs/metar/wxSymbols_anno2.pdf
        '''
        self._wx_string = val

    @property
    def flight_category(self):
        return self._flight_category
    
    @flight_category.setter
    def flight_category(self,val):
        self._flight_category = val

    @property
    def precip_in(self):
        return self._sea_level_pressure_mb
    
    @precip_in.setter
    def precip_in(self,val):
        float_val = None
        try:
            float_val = float(val)
        except Exception as e:
            self.logger.exception(f'Failed converting {val} to float')
        if float_val != None:
            self._precip_in = float_val
        else:
            self._precip_in = val

    @property
    def metar_type(self):
        return self._metar_type
    
    @metar_type.setter
    def metar_type(self,val):
        self._metar_type = val

    @property
    def elevation_m(self):
        return self._elevation_m
    
    @elevation_m.setter
    def elevation_m(self,val):
        float_val = None
        try:
            float_val = float(val)
        except Exception as e:
            self.logger.exception(f'Failed converting {val} to float')
        if float_val != None:
            self._elevation_m = float_val
        else:
            self._elevation_m = val

    @property
    def quality_control_flag(self):
        return self._quality_control_flag
    
    @quality_control_flag.setter
    def quality_control_flag(self,val):
        self._quality_control_flag = val

    @property
    def sky_condition(self):
        return self._sky_condition
    
    def add_sky_condition(self,sky_cover: str, cloud_base_ft_agl):
        '''
        Appends the sky condition to the sky_condition list
        Each sky condition comes in the following form <sky_condition sky_cover="FEW" cloud_base_ft_agl="4300"/>
        There can be multiple of these items, so each should be a dictionary
        '''
        try:
            int_cloud_base_ft_agl = int(cloud_base_ft_agl)
            cloud_base_ft_agl = int_cloud_base_ft_agl
        except Exception as e:
            self.logger.exception(f'Failed converting {cloud_base_ft_agl} to float')

        sky_condition_dict = {
            'sky_cover': sky_cover,
            'cloud_base_ft_agl': cloud_base_ft_agl
        }
        try:
            self._sky_condition.append(sky_condition_dict)
        except Exception as e:
            self.logger.exception(f'Failed to append sky condition to list')
