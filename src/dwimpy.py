# This is an implementation of the dwim model
# in Python, to check the algorithms work.

import sys
import codecs
import requests
import getpass
import cookielib
import glob
import ConfigParser
from bs4 import BeautifulSoup

CONFIG_FILENAME = 'dwimpy.conf'

class Fetcher(object):
	def __init__(self,
		server='www.dreamwidth.org',
		debug=False):

		self._session = requests.Session()

		self._server = server
		self._debug = debug

		self._session.cookies = cookielib.LWPCookieJar('dwimpy-cookies.txt')
		try:
			self._session.cookies.load()
		except IOError:
			print 'You have no current cookies.'

	def _url(self, server, uri):
		if server is None:
			server = self._server

		return 'https://%s%s' % (server, uri)

	def fetch(self, uri,
		server = None,
		post_vars = None):

		url = self._url(server, uri)

		if post_vars is None:
			sys.stdout.write('  -- GET '+url + ' ... ')
			page = self._session.get(url)
		else:
			sys.stdout.write('  -- POST '+url + ' ... ')
			page = self._session.post(url,
				data = post_vars)

		sys.stdout.write('%d\n' % (page.status_code,))
		self._session.cookies.save()

		if self._debug:
			maxfile = 0
			for filename in glob.glob('*.html'):
				filename = filename[:filename.index('.')]
				try:
					filenumber = int(filename)
				except ValueError:
					filenumber = 0 # not a number, ignore

				maxfile = max(maxfile, filenumber)

			maxfile += 1
			filename = '%06d.html' % (maxfile,)
			file(filename, 'w').write(page.content)
			sys.stdout.write('    -- page saved to %s.\n' % (filename,))

		page.raise_for_status()

		return BeautifulSoup(page.content,
			'html.parser')

	def has_cookies(self):
		return len(self._session.cookies)!=0

class Dwimpy(object):
	def __init__(self, fetcher):
		self._fetcher = fetcher

		self._config = ConfigParser.ConfigParser()
		self._config.read(CONFIG_FILENAME)

	def _save_config(self):
		self._config.write(file(CONFIG_FILENAME, 'w'))

	def login(self):
		# At present we log in if they don't have cookies.
		# It's more complicated than that (cookies may have
		# expired, etc) but we'll deal with that in a
		# later version.

		if self._fetcher.has_cookies():
			sys.stdout.write('You appear to be logged in already.\n')
			return

		sys.stdout.write('You don\'t seem to be logged in. Logging in.\n')

		soup = self._fetcher.fetch('/login')

		fields = {}

		for field in soup.find_all('input'):
			if field.has_attr('name') and field.has_attr('value'):
				fields[field['name']] = field['value']

		username = raw_input("Username: ")
		password = getpass.getpass()

		fields['user'] = username
		fields['password'] = password

		page2 = self._fetcher.fetch('/login',
			post_vars = fields)

		if not config.has_section('cache'):
			config.add_section('cache')

		config.set('cache', 'username', username)

		self._save_config()

	def username(self):
		return self._config.get(
			'cache', 'username',
			raw=True)

class UI(object):
	def __init__(self, dwimpy):
		self._dwimpy = dwimpy
		self._dwimpy.login()

	def menu(self,
		title,
		options):

		print
		print '== %s ==' % (title,)
		for (number, line) in zip(range(len(options)), options):
			print '%4d. %s' % (number+1, line[0])

		choice = None
		while choice is None:
			try:
				choice = int(raw_input(title+'> '))
			except ValueError:
				print 'Please give an integer answer.'

			if choice is not None and (choice<1 or choice>len(options)):
				print 'Please choose a menu option.'
				choice = None

		return options[choice-1][1]()

	def show_lastn(self):
		print 'You are ',self._dwimpy.username()
		print 'show lastn'

	def show_read(self):
		print 'show read'

	def mainmenu(self):
		self.menu('Main menu',
			[('Your own recent entries',
				lambda: self.show_lastn(),
			),
			('Your reading page',
				lambda: self.show_read(),
			),
			])


def utf8Fix():
	sys.stdout = codecs.getwriter(sys.stdout.encoding)(sys.stdout)

def main():
	utf8Fix()

	debug = True

	fetcher = Fetcher(debug=debug)
	dwimpy = Dwimpy(fetcher=fetcher)
	ui = UI(dwimpy=dwimpy)

	ui.mainmenu()

if __name__=='__main__':
	main()
