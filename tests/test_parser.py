from abc import abstractmethod, ABC
from dataclasses import asdict
from datetime import date, datetime
from os import environ
from json import dump, load, JSONEncoder
from pathlib import Path

from requests import Session

from wccls import Checkout, FormatType, HoldPaused, Item, Parser, StatusType

class ItemJsonEncoder(JSONEncoder):
	def default(self, o):
		if isinstance(o, date):
			return o.isoformat()
		if isinstance(o, Item):
			return asdict(o) | {'status': str(o.status)}
		if isinstance(o, FormatType): # pylint: disable=isinstance-second-argument-not-valid-type
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
		elif key in {'dueDate', 'reactivationDate', 'expiryDate', 'shippedDate', 'activationDate'}:
			o[key] = datetime.fromisoformat(o[key]).date()
	if o['status'] == StatusType.Checkout:
		return Checkout(o['title'], o['isDigital'], o['format'], o['dueDate'], o['renewals'])
	if o['status'] == StatusType.HoldPaused:
		return HoldPaused(o['title'], o['isDigital'], o['format'], o['reactivationDate'])
	return o

class BaseWrapper(ABC):
	def __init__(self, subdomain, login, password):
		self._rootPath = Path('tests') / subdomain
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
	def __init__(self, subdomain, login, password):
		super().__init__(subdomain, login, password)
		with open(self._rootPath / 'output.json', encoding='utf-8') as f:
			self.expectedItems = load(f, object_hook=ItemObjectHook)

	def _DoRequest(self, request):
		path = self._rootPath / request.url.split('/')[-1]
		with open(path, 'r', encoding='utf-8') as f:
			return f.read()

class SaveToFileWrapper(BaseWrapper):
	def __init__(self, subdomain, login, password):
		self._session = Session() # we need this initialized before we're called back on _DoRequest
		super().__init__(subdomain, login, password)
		with open(self._rootPath / 'output.json', 'w', encoding='utf-8') as f:
			dump(self.items, f, cls=ItemJsonEncoder, indent='\t')

	def _DoRequest(self, request):
		path = self._rootPath / request.url.split('/')[-1]
		if request.verb == 'GET':
			response = self._session.get(request.url, allow_redirects=request.allowRedirects)
		elif request.verb == 'POST':
			response = self._session.post(request.url, data=request.data, allow_redirects=request.allowRedirects)
		else:
			assert False, f'Unexpected request: {request}'
		response.raise_for_status()
		responseText = response.text.replace(environ['SCRUB_EMAIL'], 'SCRUBBED_EMAIL')
		responseText = responseText.replace(environ['WCCLS_CARD_NUMBER'], 'WCCLS_CARD_NUMBER')
		responseText = responseText.replace(environ['MULTCOLIB_CARD_NUMBER'], 'MULTCOLIB_CARD_NUMBER')
		with open(path, 'w', encoding='utf-8') as f:
			f.write(responseText)
		return responseText

def test_wccls(collect):
	if collect == 'save':
		wrapper = SaveToFileWrapper('wccls', environ['WCCLS_CARD_NUMBER'], environ['WCCLS_PASSWORD'])
	elif collect == 'test':
		wrapper = CompareWrapper('wccls', 'fake_login', 'fake_password')
		assert len(wrapper.items) == len(wrapper.expectedItems)
		for item, expectedItem in zip(wrapper.items, wrapper.expectedItems):
			assert item == expectedItem, expectedItem
	else:
		assert False, f'Invalid collect strategy: {collect}'
