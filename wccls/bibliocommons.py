from os import makedirs
from os.path import join
from tempfile import gettempdir

from httpx import Client

from .parser import Parser
from .wccls import ParseError

class BiblioCommons:
	def __init__(self, subdomain, login, password, debug_=False):
		self._debug = debug_
		self._parser = Parser(subdomain, login, password)
		session = Client()
		try:
			reqs = self._parser.Receive(None, None)
			while len(reqs) > 0:
				req = reqs.pop()
				resp = self._DoRequest(session, req)
				reqs.extend(self._parser.Receive(req.url, resp))
		except ValueError as e:
			raise ParseError from e
		except AttributeError as e:
			raise ParseError from e

	def _DoRequest(self, session, request):
		if request.verb == 'GET':
			response = session.get(request.url, follow_redirects=request.allowRedirects)
		elif request.verb == 'POST':
			response = session.post(request.url, data=request.data, follow_redirects=request.allowRedirects)
		else:
			assert False, f'Unexpected request: {request}'
		response.raise_for_status()
		self._DumpDebugFile('any.html', response.content)
		return response.text

	@property
	def items(self):
		return self._parser.items

	def _DumpDebugFile(self, filename, text):
		if not self._debug:
			return
		directory = join(gettempdir(), 'log', 'wccls')
		makedirs(directory, exist_ok=True)
		with open(join(directory, filename), 'wb') as theFile:
			theFile.write(text)

class WcclsBiblioCommons(BiblioCommons):
	def __init__(self, login, password, debug_=False):
		super().__init__(subdomain='wccls', login=login, password=password, debug_=debug_)

class MultCoLibBiblioCommons(BiblioCommons):
	def __init__(self, login, password, debug_=False):
		super().__init__(subdomain='multcolib', login=login, password=password, debug_=debug_)
