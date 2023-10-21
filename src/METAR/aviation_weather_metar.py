from __future__ import annotations
import urllib.request
from urllib.error import URLError, HTTPError, ContentTooShortError
import logging
import xml.etree.ElementTree as ET
from datetime import datetime

from METAR.METAR import METAR

# As of October 16, 2023 the ADDS has been retired in favor of the new aviationweather.gov
# adds_metar_data_server_base_url = ''.join((
# 		r'https://www.aviationweather.gov/adds/dataserver_current/httpparam?',
# 		r'datasource=metars&',
# 		r'requestType=retrieve&',
# 		r'format=xml&',
# 		r'mostRecentForEachStation=constraint&',
# 		r'hoursBeforeNow=24&'))

aviation_weather_dataserver_base_url = ''.join((
	r'https://aviationweather.gov/cgi-bin/data/dataserver.php?',
	r'datasource=metars&',
	r'requestType=retrieve&',
	r'format=xml&',
	r'mostRecentForEachStation=constraint&',
	r'hoursBeforeNow=24&'
))

class METAR_Retrieve_Failure(Exception):
	"""Exception for failure to retrieve METAR for various reasons"""

def retrieve_METAR_of_stations(station_id_list: list[str],
							   logger: logging.Logger = logging.getLogger('retrieve_METAR_of_stations')
							   ) -> list[METAR | None]:
	'''
	Retrieves and parses METAR data for a list of stations provided by their station IDs

	:param station_id_list: list of station ID strings to generate METARs from
	:return: list of METAR objects (or None if failure) corresponding to station IDs in argument list
	'''
	# Initialize the return list
	metar_data_list: list[METAR | None] = [None]*len(station_id_list)

	# Combine the station_id_list into the safe string
	station_id_str = get_station_list_string(station_id_list)
	logger.debug(f'Station String: {station_id_str}')

	# Get the request URL to the aviationweather.gov server
	url = ''.join((aviation_weather_dataserver_base_url,
		f'stationString={station_id_str}'
	))
	logger.debug(f'URL: {url}')

	# Retrieve the server result the METAR data
	try:
		with urllib.request.urlopen(url) as metarURL:
			result_xml = metarURL.read()
	except (HTTPError, URLError, ContentTooShortError):
		logger.exception(f'Error retreiving data from {url}')
		raise METAR_Retrieve_Failure(f'Error retreiving data from {url}')
	
	if result_xml == None:
		logger.debug(f'No XML from url: {url}')
		raise METAR_Retrieve_Failure(f'No xml received from URL requests: {url}')

	# Parse the retrieved data
	try:
		result_dict = parse_METAR_xml(result_xml)
	except ValueError:
		logger.debug(f'parsing failure')
		raise METAR_Retrieve_Failure(f'Failure to parse retrieved METAR xml from url: {url}')

	# Populate the output list with the retrieved data
	for station_id in station_id_list:
		try:
			station_metar = result_dict[station_id]
		except KeyError:
			logger.error(f'No METAR data retrieved for: {station_id}')
			continue
		else:
			metar_data_list[station_id_list.index(station_id)] = station_metar

	return metar_data_list

# Helper function for XML parsing
def searchForTag(root,elemTag):
	'''
	Searches the XML tree for the element tag starting at the root
	'''
	foundElem = None
	if root.tag == elemTag:
		return root
	else:
		for child in root:
			foundElem = searchForTag(child,elemTag)
			if foundElem != None:
				break
	return foundElem

def parse_METAR_xml(metarXML: str, logger: logging.Logger | None = None) -> dict[str, METAR]:
	'''
	Parses the xml received from the aviationweather.gov text dataserver
	METAR objects for each station
	'''

	# Initialize the result dictionary
	result: dict[str, METAR] = {}
	if logger is None:
		logger = logging.getLogger(f'parse_METAR_XML')

	# Create an element tree from the text retrieved from dataserver
	tree = ET.ElementTree(ET.fromstring(metarXML))
	root = tree.getroot()
	
	# Get the data tag, and check that there is a num_results attribute
	data = searchForTag(root,'data')
	if data == None:
		raise ValueError(f'Found no data element in xml: {metarXML}')
	
	try:
		num_results = data.attrib['num_results']
		logger.debug(f'Found data element with {num_results} result')
	except KeyError:
		raise ValueError(f'Data element did not have a num_results attribute')
		
	# There should be children <METAR> tags, each defining one station result
	for child in data:
		# Get all METAR children
		if child.tag != 'METAR':
			logger.warning(f'Non-METAR element found under <data>: {child.tag}')
			continue
		else:
			# Get the station_id, log error if not found and pass on this tag
			# The result dict can't handle an unidentified result
			station_id = searchForTag(child,'station_id')
			logger.debug(f'Found station_id: {station_id.text}')
			if station_id == None:
				logger.error(f'No Station ID found for METAR: {child}')
				continue
			
			# The station_id is the inner text of the xml tag
			station_id = station_id.text
	
			# For valid METAR children, we need to add the station_id as a key into the dict, and then
			# parse the child tags into the METAR data object
			result[station_id] = METAR(station = station_id)	# Initialize blank METAR object
			for element in child:
				# Check if the METAR object has an attribute defined for this property
				# Properties of the METAR object align with these labels
				if hasattr(result[station_id],element.tag):
					logger.debug(f'{station_id} has attr {element.tag}: {element.text}')
					# If it does, set it
					try:
						setattr(result[station_id],element.tag,element.text)
					except AttributeError:
						# Handle tags that do not support setters
						if element.tag == 'sky_condition':
							try:
								cloud_base_ft_agl = element.attrib['cloud_base_ft_agl']
							except KeyError:
								cloud_base_ft_agl = None

							try:
								sky_cover = element.attrib['sky_cover']
							except KeyError:
								sky_cover = None
							result[station_id].add_sky_condition(
								sky_cover = sky_cover,
								cloud_base_ft_agl = cloud_base_ft_agl
								)
						else:
							logger.error(f'Unexpected Attribute in METAR dataset: {element.tag}')
							continue
	return result

def check_Server_Connection(logger: logging.Logger = logging.getLogger('check_Server_Connection')) -> bool:
	"""Attempts to reach the aviationweather.gov/cgi-bin/data/dataserver, returns success as bool"""
	success = False
	try:
		urllib.request.urlopen(r'https://aviationweather.gov/cgi-bin/data/dataserver.php?')
		success = True
		logger.debug('Successfully connected to aviationweather.gov dataserver')
	except (URLError, HTTPError, ContentTooShortError):
		logger.exception(f'Unable to connect to aviationweather.gov dataserver at {datetime.now()}')
	
	return success

def get_station_list_string(station_id_list: list[str]) -> str:
	"""
	Produces a string of the list that can be inserted into the http reques
	
	:param station_id_list: The list of stations ids to produce the string from
	:return: string of ids joined properly
	"""
	station_id_url_str = ''
	station_id_url_str = '%20'.join(station_id_list)
	return station_id_url_str

class Aviation_Weather_METAR:
	"""Object to manage a pre-determined set of stations and retrieve updated METAR data"""
	def __init__(self, stations: list[str] | None = None):
		self._logger = logging.getLogger(f'{self.__class__.__name__}')

		self._metar_data: dict[str, METAR | None] = {}	# Data dictionary, holds the current data for the stations that this object manages

		#  initialize the metar_data dictionary with the set of input stations (if present)
		if stations is not None:
			for station in stations:
				self.add_station(station)
		return
	
	@property
	def station_id_list(self):
		'''
		Property: the list of station ids being monitored
		Sources from the metar_data dictionary so it remains up to date with additions
		'''
		return list(self._metar_data.keys())

	def update_METAR_data(self) -> bool:
		'''
		Retrieves new METAR data for all stations in the stations list
		Source is aviationweather.gov dataserver
		'''

		try:
			metar_list = retrieve_METAR_of_stations(self.station_id_list)
		except METAR_Retrieve_Failure:
			self._logger.error(f'Failure to retrieve METAR data')
			pass
		else:
			for station in self.station_id_list:
				self._metar_data[station] = metar_list[self.station_id_list.index(station)]
			return True
		return False
	
	def add_station(self, station_id: str) -> None:
		"""
		Add a station ID by str to the metar_data dict
		"""
		self._metar_data[station_id] = METAR()

	def remove_station(self, station_id: str):
		"""Remove a station from the station_id list to track"""
		try:
			self._metar_data.pop(station_id)
		except KeyError:
			self._logger.debug(f'Attempted to remove a station that was not being tracked: {station_id}')
			pass
		return
	
# if __name__ == '__main__':
# 	station_id = 'KSLE'
# 	result = retrieve_METAR_of_station(station_id)
# 	print(result)

	# metar_set = ADDSMETAR(['KOSH', 'KSLE', 'KONP'])
	# metar_set.update_METAR_data()
	# print(metar_set.get_METAR_of_station('KSLE'))