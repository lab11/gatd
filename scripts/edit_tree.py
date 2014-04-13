import urwid


default_commands = urwid.command_map.copy()
urwid.command_map['enter'] = 'cursor down'
palette = [('title', 'default,bold', 'default'),]

class MyButton(urwid.Button):
	def __init__ (self, label, on_press=None, user_data=None):
		self._command_map = default_commands
		super(MyButton, self).__init__(label, on_press, user_data)

class ConversationListBox(urwid.ListBox):


	def __init__(self, tree):
		piles = []
		top = []
		top.append(urwid.Text(u"Edit the keys. Select finished when done."))
		top.append(urwid.Divider())
		piles.append(urwid.Pile(top))

		self.editor = urwid.Edit(('title', ''),
		                         edit_text=self.textTree(0, tree),
		                         multiline=True)

		piles.append(urwid.Pile([self.editor]))

		bot = []
		bot.append(urwid.Divider())
		bot.append(MyButton('finished', self.finish))
		piles.append(urwid.Pile(bot))

		body = urwid.SimpleFocusListWalker(piles)

		self._command_map['enter'] = 'cursor down'

		super(ConversationListBox, self).__init__(body)

	def textTree (self, indent, tree):
		if not tree:
			return ''

		text = ''
		for k in tree:
			text += ' '*indent + k['key'] + '\n'
			text += self.textTree(indent+2, k['children'])

		return text


	def finish (self, a):
		raise urwid.ExitMainLoop()


def edit_tree (tree):
	editor = ConversationListBox(tree)
	urwid.MainLoop(editor, palette).run()
	return editor.editor.edit_text

