import parser

class presenceParser (parser.parser) :

    # Presence indicates groups of people and the times when they are present
    #   in a given tracked location
	name = 'Presence'
	access = 'public'
	no_parse = True

	def __init__ (self):
		pass

