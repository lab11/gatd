# Runs through the archive table and checks if any
#  archived records can now be parsed


class archiveCleaner ():

	def __init__ (self, db, pm):
		self.db = db
		self.pm = pm

	def process (self):
		for record in self.db.getArchives():

			try:
				if self.pm.isAddrKnown(data=record['data'], meta=record['meta']):
					# parse
					ret = self.pm.parsePacket(data=record['data'], meta=record['meta'])
					# save in database
					self.db.writeFormatted(ret)

					# delete record from archive
					self.db.deleteArchive(record['_id'])

				else:
					# has no address
					#self.db.deleteArchive(record['_id'])
					pass

			except FE.BadPacket as e:
				print e

			except FE.ParserError as e:
				print e

			except UnicodeDecodeError:
				pass

