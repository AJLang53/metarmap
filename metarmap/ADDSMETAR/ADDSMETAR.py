import urllib.request
import logging
import xml.etree.ElementTree as ET
import datetime as datetime

from .METAR import METAR

logger = logging.getLogger(__name__)

class ADDSMETAR:
	def __init__(self, stations: list = None):
		self.logger = logger
		self._last_update_time = None			# Time object to synchronize updates
		self._initializeStations(stations)		# initialize the metar_data dictionary with the set of input stations
		return
	
	def _initializeStations(self,stations):
		'''
		Takes the input stations list and returns the initial metar data dictionary
		'''
		init_dict = {}
		# If no stations provided, return empty dictionary
		if stations == None:
			self.logger.debug('No stations provided, instantiating empty metar_data dict')
			self._metar_data = {}
		else:
			# check if a single station as provided as a string, add it to its own list
			if type(stations) == str:
				self.logger.debug('Single station input, converting to list of one element')
				stations = [stations]

			# Iterate through all stations in list, adding to dict with a fresh METAR object if string
			for station_id in stations:
				if type(station_id) == str:
					try:
						init_dict[station_id] = METAR()
					except Exception as e:
						self.logger.exception(f'Failed to add {station_id} to metar data dictionary')
				else:
					self.logger.debug(f'Tried to add non-string to station list: {station_id}')
			self._metar_data = init_dict
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
		except Exception as e:
			self.logger.exception(f'Failed to get list of station ID keys')

		return station_id_list
	
	@property
	def station_id_url_str(self):
		'''
		Property: the list of station ids being monitored as a url safe string
		Sources from the metar_data dictionary so it remains up to date with additions
		'''
		station_id_url_str = ''
		try:
			id_list = self.station_id_list
			if id_list != None:
				for id in id_list:
					station_id_url_str += id
					station_id_url_str += '%20'
				station_id_url_str = station_id_url_str[0:-3]
			else:
				self.logger.debug(f'Tried to create a station_id_url_str, but station_id_list was None')
		except Exception as e:
			logger.exception('Failed to produce station_id_url_str')
		
		return station_id_url_str
	
	def getMETARofStation(self,station_id: str):
		'''
		Returns the current METAR for the provided station_id
		'''
		metar_data = None
		try:
			metar_data = self._metar_data[station_id]
		except KeyError as ke:
			self.logger.exception(f'Tried to access METAR of station not being monitored: {station_id}')
		except Exception as e:
			self.logger.exception(f'Failed to retrieve METAR for {station_id}')
		return metar_data

	def _updateMETARData(self):
		'''
		Retrieves new METAR data for all stations in the stations list
		Source is aviationweather.gov dataserver
		'''

		id_str = self.station_id_url_str
		url = ''.join((
			r'https://www.aviationweather.gov/adds/dataserver_current/httpparam?',
			r'datasource=metars&',
			r'requestType=retrieve&',
			r'format=xml&',
			r'mostRecentForEachStation=constraint&',
			r'hoursBeforeNow=24&',
			f'stationString={id_str}'
		))

		results = None
		try:
			with urllib.request.urlopen(url) as metarURL:
				result_xml = metarURL.read()
				logger.debug(f'Retrived {result_xml} from {url}')
		except Exception as e:
			logger.exception(f'Failed to retrieve data from URL: {url}')
		try:
			self._parseMETARXML(result_xml)
		except:
			logger.exception('Parsing Failure')

		return
	
	def _parseMETARXML(self,metarXML: str):
		'''
		Parses the xml received from the ADDS text dataserver into the metar_data dictionary
		METAR objects for each station
		'''

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

		try:
			tree = ET.ElementTree(ET.fromstring(metarXML))
			root = tree.getroot()
		except Exception as e:
			self.logger.exception(f'Failed to generate ElementTree from xml: {metarXML}')
			return
		
		data = searchForTag(root,'data')
		if data == None:
			self.logger.debug(f'Found no data element in xml: {metarXML}')
			return
		else:
			try:
				num_results = data.attrib['num_results']
				self.logger.debug(f'Found data element with {num_results} result')
			except:
				self.logger.exception('Data element did not have a num_results attribute')
				return
			
			for child in data:
				# Get all METAR children
				if child.tag != 'METAR':
					self.logger.debug(f'Non-METAR element found under data: {child.tag}')
					continue
				else:
					station_id = searchForTag(child,'station_id')
					# Log an error if there is no station ID
					if station_id == None:
						self.logger.error(f'No Station ID found for METAR: {child}')
						continue
			
					station_id = station_id.text
					# Log an error if this ID was not expected, ignore it
					if station_id not in self._metar_data:   
						self.logger.error(f'XML contains an Station ID that is not in the station ID list. ID: {station_id}, id_list: {self.station_id_list}')
						continue
			
			# For valid METAR children that are being monitored, 
			# First reset the METAR object to default
			# Then process their children
			self._metar_data[station_id] = METAR()
			for element in child:
				# Check if the METAR object has an attribute defined for this property
				if hasattr(self._metar_data[station_id],element.tag):
					# If it does, run it
					try:
						setattr(self._metar_data[station_id],element.tag,element.text)
					except AttributeError as AE:
						# Sky Condition is not expected to have a setter, apply behavior here
						if element.tag == 'sky_condition':
							self._metar_data[station_id].add_sky_condition(
								sky_cover = element.attrib['sky_cover'],
								cloud_base_ft_agl = element.attrib['cloud_base_ft_agl']
								)
						else:
							self.logger.exception(f'Unexpected Attribute in METAR dataset: {element.tag}')
							continue

	def addStation(self, station_id: str):
		'''
		Adds a station to the object stations dictionary for monitoring
		'''
		if type(station_id) == str:
			try:
				self._metar_data[station_id] = METAR()
			except Exception as e:
				self.logger.exception(f'Failed to add {station_id} to metar data dictionary')
		else:
			self.logger.debug(f'Tried to add non-string to station list: {station_id}')

		return
	
	def removeStation(self, station_id: str):
		'''
		Removes a station from the object stations dictionary
		'''
		self.logge.debug(f'Tried to call unimplemented function: removeStation with arg: {station_id}')
		raise Exception('removeStation is not implemented')
	

if __name__ == '__main__':
	# Test script for module
	ADDSMETAR = ADDSMETAR()
	ADDSMETAR.retrieveMETARData(['KSLE','KPDX'])
