import urllib.request
import logging
import xml.etree.ElementTree as ET
import threading
import queue
from datetime import datetime, timedelta

from ADDSMETAR.METAR import METAR

logger = logging.getLogger(__name__)

class ADDSMETAR:
	
	def __init__(self, stations = None):
		self._initializeStations(stations)		# initialize the metar_data dictionary with the set of input stations
		return
	
	@property
	def logger(self):
		return logging.getLogger(__name__)
	
	def _initializeStations(self,stations):
		'''
		Takes the input stations list and returns the initial metar data dictionary (No data populated)
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
			return station_id_list
		except Exception as e:
			self.logger.exception(f'Failed to get list of station ID keys')
			raise Exception(f'Failed to get list of station ID keys')

	
	@property
	def station_id_url_str(self):
		'''
		Property: the list of station ids being monitored as a url safe string
		Sources from the metar_data dictionary so it remains up to date with additions
		'''
		station_id_url_str = ''
		try:
			id_list = self.station_id_list
			station_id_url_str = '%20'.join(id_list)
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

		success = True
		result_xml = None

		# Grab the METAR data
		try:
			with urllib.request.urlopen(url) as metarURL:
				result_xml = metarURL.read()
				logger.debug(f'Retrived {result_xml} from {url}')
		except Exception as e:
			logger.exception(f'Failed to retrieve data from URL: {url}')
			success = False

		if result_xml != None:
			try:
				self._parseMETARXML(result_xml)
			except:
				logger.exception('Parsing Failure')
				success = False

		return success
	
	def _parseMETARXML(self,metarXML: str):
		'''
		Parses the xml received from the ADDS text dataserver
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

		# Create an element tree from the text retrieved from ADDS
		try:
			tree = ET.ElementTree(ET.fromstring(metarXML))
			root = tree.getroot()
		except Exception as e:
			self.logger.exception(f'Failed to generate ElementTree from xml: {metarXML}')
			return
		
		# Get the data tag, and check that there is a num_results attribute
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
			
			# There should be children "METAR", each defining one result
			for child in data:
				# Get all METAR children
				if child.tag != 'METAR':
					self.logger.debug(f'Non-METAR element found under data: {child.tag}')
					continue
				else:
					station_id = searchForTag(child,'station_id')
					self.logger.debug(f'Found station_id: {station_id}')
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
							self.logger.debug(f'{station_id} has attr {element.tag}')
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
							except Exception as e:
								self.logger.exception(f'Unexpected Exception while attempting to set attribute {element.tag}')

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
		self.logger.debug(f'Tried to call unimplemented function: removeStation with arg: {station_id}')
		raise Exception('removeStation is not implemented')

class ADDSMETARThread(ADDSMETAR, threading.Thread):
	'''
	A thread that manages stations periodically to make available station METAR data through its queues
	'''

	class NoTimeDeltaAvailableException(Exception):
		pass

	def __init__(self, stations = None,
	      				update_interval: timedelta = timedelta(seconds = 900),		# 15 minute update default
					    stale_data_time: timedelta = timedelta(seconds = 5220),		# 1 Hour, 45 minutes for stale data defaults
	      				stop_request: threading.Event = None,
						new_metar_data: threading.Event = None,
						data_is_stale: threading.Event = None,
						metar_queue: queue.Queue = None
				):
		# Setup Events
		self.stop_request = stop_request									# stop request event that can be used to kill the thread	
		self.new_metar_data = new_metar_data								# new metar data event that this thread will set when new data is on the queue
		self.data_is_stale = data_is_stale

		# Setup Queue
		self._metar_queue = metar_queue

		# Initialize other data
		ADDSMETAR.__init__(self, stations = stations)
		threading.Thread.__init__(self)
		# super(ADDSMETARThread, self).__init__(stations = stations)	# Run ADDSMETAR initializer
		self._update_interval = update_interval		# Setup interval time for updates
		self._stale_data_time = stale_data_time

		# Get the First Update
		if self._checkADDSServerConnection():
			if not self._checkUpdateMETARData():
				self.logger.warning(f'Initial updateMETARData call in ADDSMETARThread __init__ failed to successfully update data dictionary')
			else:
				self._updateMETARQueue()
		else:
			self.logger.warning('No internet connection available in initializer for ADDSMETAR Thread')

		self._last_attempt_time = datetime.now()		# Time object to synchronize updates

	@property
	def logger(self):
		return logging.getLogger(__name__)
	
	def _checkADDSServerConnection(self):
		success = False
		try:
			urllib.request.urlopen(r'https://www.aviationweather.gov/adds/dataserver_current')
			success = True
			self.logger.debug('Successfully connected to ADDS dataserver')
		except urllib.request.URLError as e:
			self.logger.warning(f'Unable to connect to ADDS dataserver at {datetime.now()}')
		
		return success
	
	def _checkUpdateMETARData(self):
		self._last_attempt_time = datetime.now()
		self.logger.debug(f'Update Attempt time: {self._last_attempt_time}')
		if self._updateMETARData():
			self._last_success_time = datetime.now()
			self.logger.debug(f'Update Success time: {self._last_success_time}')
			return True
		else:
			self.logger.debug('Queue not updated because self.PudpateMETARData returned False')
			return False

	def getTimeSinceLastAttempt(self):
		'''
		Compare the current time against the last time that the METAR data was updated
		'''
		
		try:
			currentTime = datetime.now()
			time_delta = currentTime - self._last_attempt_time
		except Exception as e:
			self.logger.error(f'Unable to get time delta since last METAR update')
			raise self.NoTimeDeltaAvailableException()

		return time_delta
	
	def _check_for_stale_data(self):
		'''
		Compare the current time against the last time that the METAR data was successfully update
		'''
		try:
			currentTime = datetime.now()
			time_delta = currentTime - self._last_success_time
		except Exception as e:
			self.logger.error(f'Unable to get time delta since last METAR update')
			raise self.NoTimeDeltaAvailableException()
		
		if time_delta > self._stale_data_time:
			self.logger.debug(f'time since last success: {time_delta} is greater than stale tolerance: {self._stale_data_time}')
			return True
		else:
			return False
	
	def _check_time_delta_against_interval(self):
		'''
		Returns True if either the time_delta since last update is greater than the interval OR
		the time delta could not be established
		'''
		update = False
		try:
			time_delta = self.getTimeSinceLastAttempt()
			if time_delta > self._update_interval:
				update = True
		except self.NoTimeDeltaAvailableException as e:
			self.logger.debug(f'Unable to check time delta, running update')
			update = True
		except Exception as e:
			self.logger.exception(f'Unable to complete time delta check')
			raise Exception('Unable to complete time delta check')

		return update

	def _updateMETARQueue(self):
		'''
		Put the newest METAR data on the queue
		Clean out the queue if there's anything on there first
		'''
		try:
			while not self._metar_queue.empty():		# Call the .get method on the queue until there's nothing in it
				item = self._metar_queue.get()
				self.logger.debug(f'Removed item from queue: {item}')
		except:
			raise Exception('Failed to empty the _metar_queue')
		
		# Put the metar dict onto the queue
		self._metar_queue.put(self._metar_data)
		self.new_metar_data.set()				# Set the new data flag
		self.data_is_stale.clear()				# Clear the stale data flag, if it had been set otherwise
		return

	def loop(self):
		'''
		The thread loop, this is where the action happens
		We want to:
			1. Check how long it has been since we last retrieved data from the internet
			2. If it's been long enough, request new data for all stations
			3. Update the internal station data dictionary
			4. Add the new data to the queue for other processes to have access to
		'''
		try:
			if self._check_time_delta_against_interval():			# Check if it's time to grab data
				if self._checkADDSServerConnection():				# Confirm that there is a valid internet connection to the data_server
					if self._checkUpdateMETARData():				# Attempt the update
						self._updateMETARQueue()					# If new data was successfully retrived, set the fresh flag
				else:
					self._last_attempt_time = datetime.now()			# If we don't have an internet connection, punt for another interval
					if self._check_for_stale_data():				# Check if the data has gone stale (time without update > tolerance)
						self.logger.debug('Setting data_is_stale')
						self.data_is_stale.set()
				
		except:
			self.logger.exception(f'Unhandled Exception in ADDSMETAR Loop')
			pass

	def stop(self):
		self.logger.info(f'Stop request received for {threading.get_ident()}')
		self.stop_request.set()

	def run(self):
		while not self.stop_request.is_set():
			self.loop()
		self.logger.warning('ADDSMETARThread has exited the loop')
		return
