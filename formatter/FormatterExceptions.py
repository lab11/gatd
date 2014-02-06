# Exceptions used in GATD

class GatdException(Exception):
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return repr(self.value)

class BadPacket(GatdException):
	pass

class BadParser(GatdException):
	pass

class ParserError(GatdException):
	pass

class ParserNotFound(GatdException):
	pass
