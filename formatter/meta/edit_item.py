import urwid


default_commands = urwid.command_map.copy()
urwid.command_map['enter'] = 'cursor down'
palette = [('title', 'default,bold', 'default'),]

class MyButton(urwid.Button):
	def __init__ (self, label, on_press=None, user_data=None):
		self._command_map = default_commands
		super(MyButton, self).__init__(label, on_press, user_data)

class ConversationListBox(urwid.ListBox):

	contained_elements = []
	values = []

	def __init__(self, **kwargs):
		piles = []
		top = []
		top.append(urwid.Text(u"Edit the values. Select finished when done."))
		top.append(urwid.Divider())
		piles.append(urwid.Pile(top))

		p = list(range(len(kwargs)))
		self.contained_elements = list(range(len(kwargs)))

		for key, value in kwargs.iteritems():
			info = key.split('_')
			name = info[2]
			idx  = int(info[1])
			if type(value) == tuple and len(value) == 2:
				p[idx] = self.addStrSection(name, value[0], value[1])
				self.contained_elements[idx] = 'str'
			elif type(value) == dict:
				p[idx] = self.addKeyValueSection(name, value)
				self.contained_elements[idx] = 'kv'

		for pile in p:
			piles.append(pile)

		bot = []
		bot.append(MyButton('finished', self.finish))
		piles.append(urwid.Pile(bot))

		body = urwid.SimpleFocusListWalker(piles)

		self._command_map['enter'] = 'cursor down'

		super(ConversationListBox, self).__init__(body)

	def addStrSection (self, name, key, value):
		req = []
		req.append(urwid.Text(('title', name.upper())))
		req.append(urwid.Edit(('title', u"  {}: ".format(key)),
		                      edit_text=value))
		req.append(urwid.Divider())
		return urwid.Pile(req)

	def addKeyValueSection (self, name, kv):
		section = []
		section.append(urwid.Text(('title', name.upper())))
		for k in kv:
			section.append(urwid.Edit(('title', u"  key: "), edit_text=k))
			section.append(urwid.Edit(('title', u"  val: "), edit_text=kv[k]))
		section.append(MyButton('add new additional', self.addNewKeyValue))
		section.append(urwid.Divider())
		return urwid.Pile(section)

	def addNewKeyValue (self, a):
		k = urwid.Edit(('title', u"  key: "))
		v = urwid.Edit(('title', u"  val: "))
		self.focus.contents.insert(len(self.focus.contents)-2,
		                           (k, self.focus.options()))
		self.focus.contents.insert(len(self.focus.contents)-2,
		                           (v, self.focus.options()))
		self.focus.focus_position = self.focus.focus_position-2

	def finish (self, a):
		k = None

		i = 1
		for ce in self.contained_elements:

			if ce == 'str':
				self.values.append(self.body[i][1].edit_text)
			elif ce == 'kv':
				self.values.append({})
				# Iterate the additional items
				for e in self.body[i].contents:
					try:
						val = e[0].edit_text
						if k == None:
							k = val
						else:
							self.values[-1][k] = val
							k = None
					except AttributeError:
						pass
			i += 1

		raise urwid.ExitMainLoop()


def edit_meta (req_key, req_key_val, query, additional):
	editor = ConversationListBox(_0_required_key=(req_key, req_key_val),
	                             _1_query=query,
	                             _2_additional=additional)
	urwid.MainLoop(editor, palette).run()
	e_req_key    = editor.values[0]
	e_query      = editor.values[1]
	e_additional = editor.values[2]
	return (e_req_key, e_query, e_additional)

def edit_gateway_key (prefix, additional):
	editor = ConversationListBox(_0_prefix=('prefix', prefix),
	                             _1_additional=additional)
	urwid.MainLoop(editor, palette).run()
	e_prefix     = editor.values[0]
	e_additional = editor.values[1]
	return (e_prefix, e_additional)
