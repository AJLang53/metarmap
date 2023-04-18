import urllib.request
import logging

# Set Up Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(ch)

class ADDSMETAR:
	def __init__(self):
		return

	@staticmethod
	def concatListwithSpace(list):
		id_str = ''
		for id in id_list:
			id_str += id
			id_str += '%20'
		id_str = id_str[0:-3]
		return id_str

	def retrieveMETARData(stationList,params):
		'''
		Retrieves the current
		'''
		return

if __name__ == '__main__':
	# Test script for module
	ADDSMETAR = ADDSMETAR()
	ADDSMETAR.retrieveMETARData(['KSLE','KPDX'])
