from __future__ import annotations
import urllib.request
import logging
import xml.etree.ElementTree as ET
from datetime import datetime

from METAR.METAR import METAR

adds_metar_data_server_base_url = ''.join((
		r'https://www.aviationweather.gov/adds/dataserver_current/httpparam?',
		r'datasource=metars&',
		r'requestType=retrieve&',
		r'format=xml&',
		r'mostRecentForEachStation=constraint&',
		r'hoursBeforeNow=24&'))

def retrieve_METAR_of_station(station_id: str) -> METAR | None:
	'''
	Returns METAR of provided station ID from live lookup

	Returns None if it could not be retrieved or parsed
	'''
	metar_data: METAR | None = None

	url = ''.join((adds_metar_data_server_base_url,
		f'stationString={station_id}'
	))

	# Grab the METAR data
	with urllib.request.urlopen(url) as metarURL:
		result_xml = metarURL.read()

	if result_xml != None:
		result_dict = parse_METAR_xml(result_xml)
	
	if result_dict is not None:
		try:
			metar_data = result_dict[station_id]
		except KeyError:
			pass

	return metar_data

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
	Parses the xml received from the ADDS text dataserver
	METAR objects for each station
	'''

	result: dict[str, METAR] = {}
	if logger is None:
		logger = logging.getLogger(f'parse_METAR_XML')

	# Create an element tree from the text retrieved from ADDS
	tree = ET.ElementTree(ET.fromstring(metarXML))
	root = tree.getroot()
	
	# Get the data tag, and check that there is a num_results attribute
	data = searchForTag(root,'data')
	if data == None:
		logger.debug(f'Found no data element in xml: {metarXML}')
		return
	else:
		try:
			num_results = data.attrib['num_results']
			logger.debug(f'Found data element with {num_results} result')
		except KeyError:
			logger.warning('Data element did not have a num_results attribute')
			return
		
		# There should be children "METAR", each defining one result
		for child in data:
			# Get all METAR children
			if child.tag != 'METAR':
				logger.warning(f'Non-METAR element found under data: {child.tag}')
				continue
			else:
				station_id = searchForTag(child,'station_id')
				logger.debug(f'Found station_id: {station_id.text}')
				# Log an error if there is no station ID
				if station_id == None:
					logger.error(f'No Station ID found for METAR: {child}')
					continue
		
				station_id = station_id.text
		
				# For valid METAR children that are being monitored, 
				# First reset the METAR object to default
				# Then process their children
				result[station_id] = METAR(station = station_id)
				for element in child:
					# Check if the METAR object has an attribute defined for this property
					if hasattr(result[station_id],element.tag):
						logger.debug(f'{station_id} has attr {element.tag}: {element.text}')
						# If it does, run it
						try:
							setattr(result[station_id],element.tag,element.text)
						except AttributeError as AE:
							# Sky Condition is not expected to have a setter, apply behavior here
							if element.tag == 'sky_condition':
								try:
									cloud_base_ft_agl = element.attrib['cloud_base_ft_agl']
								except:
									cloud_base_ft_agl = None

								try:
									sky_cover = element.attrib['sky_cover']
								except:
									sky_cover = None
								result[station_id].add_sky_condition(
									sky_cover = sky_cover,
									cloud_base_ft_agl = cloud_base_ft_agl
									)
							else:
								logger.error(f'Unexpected Attribute in METAR dataset: {element.tag}')
								continue
	return result

class ADDSMETAR:
	"""Object to manage a pre-determined set of stations and retrieve updated METAR data"""
	def __init__(self, stations: list[str] | None = None):
		self._logger = logging.getLogger(f'{self.__class__.__name__}')

		self._metar_data: dict[str, METAR] = {}	# Data dictionary, holds the current data for the stations that this object manages

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
		station_id_list = None
		try:
			station_id_list = list(self._metar_data.keys())
			return station_id_list
		except Exception as e:
			self._logger.exception(f'Failed to get list of station ID keys')
			raise Exception(f'Failed to get list of station ID keys')
	
	@property
	def station_id_url_str(self) -> str:
		'''
		Property: the list of station ids being monitored as a url safe string
		Sources from the metar_data dictionary so it remains up to date with additions
		'''
		station_id_url_str = ''
		id_list = self.station_id_list
		station_id_url_str = '%20'.join(id_list)
		return station_id_url_str
	
	def get_METAR_of_station(self, station_id: str):
		"""Provide the cached METAR data for the station_id"""
		metar_data = None
		try:
			metar_data = self._metar_data[station_id]
		except KeyError:
			self._logger.exception(f'Tried to access METAR of station not being monitored: {station_id}')
		return metar_data

	def _check_ADDS_Server_Connection(self) -> bool:
		"""Attempts to reach the aviationweather.gov/adds/dataserver, returns success as bool"""
		success = False
		try:
			urllib.request.urlopen(r'https://www.aviationweather.gov/adds/dataserver_current')
			success = True
			self._logger.debug('Successfully connected to ADDS dataserver')
		except urllib.request.URLError as e:
			self._logger.warning(f'Unable to connect to ADDS dataserver at {datetime.now()}')
		
		return success

	def update_METAR_data(self) -> bool:
		'''
		Retrieves new METAR data for all stations in the stations list
		Source is aviationweather.gov dataserver
		'''

		id_str = self.station_id_url_str
		url = ''.join((adds_metar_data_server_base_url,
			f'stationString={id_str}'
		))

		success = True
		result_xml = None

		# Grab the METAR data
		try:
			with urllib.request.urlopen(url) as metarURL:
				result_xml = metarURL.read()
				self._logger.debug(f'Retrived {result_xml} from {url}')
		except Exception as e:
			self._logger.exception(f'Failed to retrieve data from URL: {url}')
			success = False

		if result_xml != None:
			try:
				result_dict = parse_METAR_xml(result_xml)
				self._metar_data = result_dict
			except:
				self._logger.exception('Parsing Failure')
				success = False

		return success
	
	def add_station(self, station_id: str) -> bool:
		"""
		Add a station ID by str to the metar_data dict
		
		Attempt to acquire a METAR for the station ID, do not add if failure to retrieve
		Return True if added, False if not
		"""
		if self._check_ADDS_Server_Connection():		# If we can reach the server, check the station METAR
			if retrieve_METAR_of_station(station_id) is not None:
				self._metar_data[station_id] = METAR()
				return True
		return False
	
	def remove_station(self, station_id: str):
		"""Remove a station from the station_id list to track"""
		try:
			self._metar_data.pop(station_id)
		except KeyError:
			self._logger.debug(f'Attempted to remove a station that was not being tracked: {station_id}')
			pass
		return
	
if __name__ == '__main__':
	station_id = 'KSLE'
	result = retrieve_METAR_of_station(station_id)
	print(result)

	metar_set = ADDSMETAR(['KOSH', 'KSLE', 'KONP'])
	metar_set.update_METAR_data()
	print(metar_set.get_METAR_of_station('KSLE'))