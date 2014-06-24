import ConfigParser
import pymongo
import os
import json

class GatdDataExtractor():
	db = ''
	def __init__(self):
		config_file_path = os.path.realpath("../config/gatd.config")
		config = ConfigParser.SafeConfigParser()
		config.read(config_file_path)
		host = config.get('mongo', 'host')
		port = int(config.get('mongo', 'port'))
		db_username = config.get('mongo', 'username')
		db_password = config.get('mongo', 'password')

		client = pymongo.MongoClient(host, port)
		self.db = client[config.get('mongo', "database")]
		self.db.authenticate(db_username, db_password)

	def extract(self, parameters={}, sort_parameters="", collection='formatted_data'):
		"""
		Lets users run arbitrary find queries on the gatd database
		"""
		c = self.db[collection]
		if len(sort_parameters) == 0:
			data = c.find(spec=parameters)
		else:
			data = c.find(parameters).sort(sort_parameters)

		return data

	def test(self, collection='formatted_data'):
		c = self.db[collection]

		return c.find({"profile_id":"4wbddZCSIj"})


if __name__ == "__main__":
	tq = {"profile_id":"4wbddZCSIj"}
	test = GatdDataExtractor()
	n = test.extract(parameters=tq)
	for row in n:
		print row

