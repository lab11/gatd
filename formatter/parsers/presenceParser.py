import parser

class presenceParser (parser.parser):

    # Presence indicates groups of people and the times when they are present
    #   in a given tracked location
	name = 'Presence'
	description = 'List of people in a given space.'
	no_parse = True

	def __init__ (self):
		pass

