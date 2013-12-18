#!/usr/bin/env python


import urwid


default_commands = urwid.command_map.copy()
urwid.command_map['enter'] = 'cursor down'
palette = [('title', 'default,bold', 'default'),]

class MyButton(urwid.Button):
	def __init__ (self, label, on_press=None, user_data=None):
		self._command_map = default_commands
		super(MyButton, self).__init__(label, on_press, user_data)

class ConversationListBox(urwid.ListBox):
	req_key = ''
	query = {}
	additional = {}

	def __init__(self, req_key, req_key_val, query, additional):
		piles = []
		top = []
		top.append(urwid.Text(u"Edit the values. Select finished when done."))
		top.append(urwid.Divider())
		piles.append(urwid.Pile(top))

		req = []
		req.append(urwid.Text(('title', u"REQUIRED KEY")))
		req.append(urwid.Edit(('title', u"  {}: ".format(req_key)), edit_text=req_key_val))
		req.append(urwid.Divider())
		piles.append(urwid.Pile(req))

		queries = []
		queries.append(urwid.Text(('title', u"QUERY")))
		for k in query:
			queries.append(urwid.Edit(('title', u"  key: "), edit_text=k))
			queries.append(urwid.Edit(('title', u"  val: "), edit_text=query[k]))
		queries.append(MyButton('add new query', self.addNewKeyValue))
		queries.append(urwid.Divider())
		piles.append(urwid.Pile(queries))

		addits = []
		addits.append(urwid.Text(('title', u"ADDITIONAL")))
		for k in additional:
			addits.append(urwid.Edit(('title', u"  key: "), edit_text=k))
			addits.append(urwid.Edit(('title', u"  val: "), edit_text=additional[k]))
			title = ''
		addits.append(MyButton('add new additional', self.addNewKeyValue))
		addits.append(urwid.Divider())
		piles.append(urwid.Pile(addits))

		bot = []
		bot.append(MyButton('finished', self.finish))
		piles.append(urwid.Pile(bot))

		body = urwid.SimpleFocusListWalker(piles)

		self._command_map['enter'] = 'cursor down'

		super(ConversationListBox, self).__init__(body)

	def addNewKeyValue (self, a):
		k = urwid.Edit(('title', u"  key: "))
		v = urwid.Edit(('title', u"  val: "))
		self.focus.contents.insert(len(self.focus.contents)-2, (k, self.focus.options()))
		self.focus.contents.insert(len(self.focus.contents)-2, (v, self.focus.options()))
		self.focus.focus_position = self.focus.focus_position-2

	def finish (self, a):
		k = None

		self.req_key = self.body[1][1].edit_text

		# Iterate the query items
		for e in self.body[2].contents:
			try:
				val = e[0].edit_text
				if k == None:
					k = val
				else:
					self.query[k] = val
					k = None
			except AttributeError:
				pass

		# Iterate the additional items
		for e in self.body[3].contents:
			try:
				val = e[0].edit_text
				if k == None:
					k = val
				else:
					self.additional[k] = val
					k = None
			except AttributeError:
				pass


		raise urwid.ExitMainLoop()

	def keypress(self, size, key):
		key = super(ConversationListBox, self).keypress(size, key)
		if key == 'enter':
			return urwid.CURSOR_DOWN

		return key



def edit_meta (req_key, req_key_val, query, additional):
	editor = ConversationListBox(req_key, req_key_val, query, additional)
	urwid.MainLoop(editor, palette).run()
	return (editor.req_key, editor.query, editor.additional)
