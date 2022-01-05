from abc import abstractmethod, ABC
from dataclasses import asdict
from datetime import date, datetime
from os import environ
from json import dump, load, JSONEncoder
from pathlib import Path

from httpx import Client

from wccls import Checkout, FormatType, HoldNotReady, HoldPaused, HoldReady, Item, Parser, StatusType

class ItemJsonEncoder(JSONEncoder):
	def default(self, o):
		if isinstance(o, date):
			return o.isoformat()
		if isinstance(o, Item):
			return asdict(o) | {'status': str(o.status)}
		if isinstance(o, FormatType):
			return str(o)
		return super().default(o)

def ItemObjectHook(o):
	if 'status' not in o:
		return o
	for key, value in o.items():
		if key == 'status' and value.startswith('StatusType.'):
			o['status'] = StatusType[o['status'][11:]]
		elif key == 'format' and value.startswith('Format.'):
			o['format'] = FormatType[o['format'][7:]]
		elif key in {'dueDate', 'reactivationDate', 'expiryDate', 'activationDate'}:
			o[key] = datetime.fromisoformat(o[key]).date()
	if o['status'] == StatusType.Checkout:
		return Checkout(o['title'], o['isDigital'], o['format'], o['dueDate'], o['renewals'])
	if o['status'] == StatusType.HoldNotReady:
		return HoldNotReady(o['title'], o['isDigital'], o['format'], o['activationDate'], o['queuePosition'], o['copies'])
	if o['status'] == StatusType.HoldPaused:
		return HoldPaused(o['title'], o['isDigital'], o['format'], o['reactivationDate'])
	if o['status'] == StatusType.HoldReady:
		return HoldReady(o['title'], o['isDigital'], o['format'], o['expiryDate'])

	return o

def FilenameFromRequest(request):
	return request.url.split('/')[-1].replace('?', '_')

class BaseWrapper(ABC):
	def __init__(self, subdomain, fileset, login, password):
		self._rootPath = Path('tests') / Path('filesets') / fileset
		self._subdomain = subdomain
		self._parser = Parser(subdomain, login, password)
		reqs = self._parser.Receive(None, None)
		while len(reqs) > 0:
			req = reqs.pop()
			resp = self._DoRequest(req)
			reqs.extend(self._parser.Receive(req.url, resp))
		self.items = self._parser.items

	@abstractmethod
	def _DoRequest(self, request):
		pass

class CompareWrapper(BaseWrapper):
	def __init__(self, subdomain, fileset, login, password):
		super().__init__(subdomain, fileset, login, password)
		with open(self._rootPath / 'output.json', encoding='utf-8') as f:
			self.expectedItems = load(f, object_hook=ItemObjectHook)

	def _DoRequest(self, request):
		path = self._rootPath / FilenameFromRequest(request)
		with open(path, encoding='utf-8') as f:
			return f.read()

class SaveToFileWrapper(BaseWrapper):
	def __init__(self, subdomain, fileset, login, password):
		self._session = Client() # we need this initialized before we're called back on _DoRequest
		super().__init__(subdomain, fileset, login, password)
		with open(self._rootPath / 'output.json', 'w', encoding='utf-8') as f:
			dump(self.items, f, cls=ItemJsonEncoder, indent='\t')

	def _DoRequest(self, request):
		if request.verb == 'GET':
			response = self._session.get(request.url, follow_redirects=request.allowRedirects)
		elif request.verb == 'POST':
			response = self._session.post(request.url, data=request.data, follow_redirects=request.allowRedirects)
		else:
			assert False, f'Unexpected request: {request}'
		response.raise_for_status()
		responseText = response.text.replace(environ['SCRUB_EMAIL'], 'SCRUBBED_EMAIL')
		responseText = responseText.replace(environ['WCCLS_CARD_NUMBER'], 'WCCLS_CARD_NUMBER')
		responseText = responseText.replace(environ['MULTCOLIB_CARD_NUMBER'], 'MULTCOLIB_CARD_NUMBER')
		with open(self._rootPath / FilenameFromRequest(request), 'w', encoding='utf-8') as f:
			f.write(responseText)
		return responseText

def testWcclsParser(collect, fileset):
	if collect == 'save':
		wrapper = SaveToFileWrapper('wccls', fileset, environ['WCCLS_CARD_NUMBER'], environ['WCCLS_PASSWORD'])
	elif collect == 'test':
		wrapper = CompareWrapper('fake_subdomain', fileset, 'fake_login', 'fake_password')
		assert len(wrapper.items) == len(wrapper.expectedItems)
		for item, expectedItem in zip(wrapper.items, wrapper.expectedItems):
			assert item == expectedItem, expectedItem
	else:
		assert False, f'Invalid collect strategy: {collect}'
