from dataclasses import dataclass
from datetime import datetime
from functools import partial
from logging import getLogger
from re import search

from bs4 import BeautifulSoup

from .wccls import Checkout, FormatType, HoldInTransit, HoldNotReady, HoldPaused, HoldReady, ParseError

log = getLogger('bibliocommons')

# These are like the events in the sansio manifesto
@dataclass
class Request:
	verb: str
	url: str
	data: dict
	allowRedirects: bool

def _MakeSoup(response):
	return BeautifulSoup(response, 'html.parser')

class Parser:
	def __init__(self, subdomain, login, password):
		self._domain = f'https://{subdomain}.bibliocommons.com'
		self._login = login
		self._password = password
		self._handlers = {}
		self.items = []

	def Receive(self, url, response):
		try:
			if url is None:
				return [self._GetRequest(f'{self._domain}/user/login', True, self._ProcessLogin)]

			function = self._handlers.get(url, None)
			assert function is not None, 'Unexpected url'
			return function(response)
		except ValueError as e:
			raise ParseError from e
		except AttributeError as e:
			raise ParseError from e

	def _GetRequest(self, url, allowRedirects, function):
		self._handlers[url] = function
		return Request('GET', url, None, allowRedirects)

	def _PostRequest(self, url, formData, allowRedirects, function):
		self._handlers[url] = function
		return Request('POST', url, formData, allowRedirects)

	def _ProcessLoginAction(self, _):
		requests = []
		# if there are no items in "ready_for_pickup", for instance, it will redirect back to the holds index, which we don't want
		requests.append(self._GetRequest(f'{self._domain}/v2/checkedout', False, partial(self._ProcessItems, _ParseCheckedOut)))
		requests.append(self._GetRequest(f'{self._domain}/v2/holds/ready_for_pickup', False, partial(self._ProcessItems, _ParseReadyForPickup)))
		requests.append(self._GetRequest(f'{self._domain}/v2/holds/in_transit', False, partial(self._ProcessItems, _ParseInTransit)))
		requests.append(self._GetRequest(f'{self._domain}/v2/holds/not_yet_available', False, partial(self._ProcessItems, _ParseNotYetAvailable)))
		requests.append(self._GetRequest(f'{self._domain}/v2/holds/suspended', False, partial(self._ProcessItems, _ParseSuspended)))
		return requests

	def _ProcessLogin(self, response):
		soup = _MakeSoup(response)
		loginForm = soup.find_all('form', class_='loginForm')[0]
		formData = {}
		for input_ in loginForm.find('input'):
			formData[input_.attrs['name']] = input_.attrs['value'] if 'value' in input_.attrs else ''
		formData['user_pin'] = self._password
		formData['name'] = self._login
		loginAction = loginForm.attrs['action']
		return [self._PostRequest(loginAction, formData, False, self._ProcessLoginAction)]

	def _ProcessItems(self, ParseFunction, response):
		soup = _MakeSoup(response)
		result = []
		for listItem in soup.find_all(class_='item-row'):
			result.append(ParseFunction(listItem))
		# Make sure the whole parse works before adding items
		self.items.extend(result)
		return []

def _ParseTitle(listItem):
	title = listItem.find_all(class_='title-content')[0].text

	subtitleElement = listItem.find(class_='cp-subtitle')
	if subtitleElement is not None:
		title += ': ' + subtitleElement.text
	return title

def _ParseSuspended(listItem):
	format_ = _ParseFormatInfo(listItem)
	return HoldPaused(
		title=_ParseTitle(listItem),
		reactivationDate=_ParseDate(listItem),
		isDigital=_IsDigital(format_),
		format=format_)

def _ParseNotYetAvailable(listItem):
	holdInfo = _ParseHoldPosition(listItem)
	format_ = _ParseFormatInfo(listItem)
	return HoldNotReady(
		title=_ParseTitle(listItem),
		activationDate=_ParseDate(listItem), # TODO - this isn't an activation date anymore - it's the expiry date
		queuePosition=holdInfo[0],
		queueSize=None, # Not shown on the initial screen anymore
		copies=holdInfo[1],
		isDigital=_IsDigital(format_),
		format=format_)

def _ParseReadyForPickup(listItem):
	format_ = _ParseFormatInfo(listItem)
	return HoldReady(
		title=_ParseTitle(listItem),
		expiryDate=_ParseDate(listItem),
		isDigital=_IsDigital(format_),
		format=format_)

def _ParseInTransit(listItem):
	format_ = _ParseFormatInfo(listItem)
	return HoldInTransit(
		title=_ParseTitle(listItem),
		isDigital=_IsDigital(format_),
		format=format_,
		shippedDate=None) # they don't seem to show this anymore

def _ParseRenewalCount(listItem):
	# if there are holds, there will be no renewals
	if len(listItem.find_all(class_='cp-held-copies-count')) > 0:
		return 0

	# get the renewed count if it's there
	renewCountElement = listItem.find(class_='cp-renew-count')
	if renewCountElement is not None:
		match = search(r'Renewed (\d+) time', renewCountElement.text)
		return 4 - int(match.group(1))

	return 1 # we don't know how many renewals are really left - this just means at least one

def _ParseCheckedOut(listItem):
	format_ = _ParseFormatInfo(listItem)
	return Checkout(
		title=_ParseTitle(listItem),
		dueDate=_ParseDate(listItem),
		renewals=_ParseRenewalCount(listItem), # really should be a "renewable" flag
		isDigital=_IsDigital(format_),
		format=format_)

def _IsDigital(format_):
	return format_ in [FormatType.eBook, FormatType.DownloadableAudiobook]

def _ParseFormatInfo(element):
	formatIndicator = element.find(class_='cp-format-indicator')
	if formatIndicator is None:
		return False
	formatLookup = {
		'Downloadable Audiobook': FormatType.DownloadableAudiobook,
		'eBook': FormatType.eBook,
		'Book': FormatType.Book,
		'DVD': FormatType.DVD,
		'Blu-ray Disc': FormatType.BluRay,
		'Graphic Novel': FormatType.GraphicNovel
	}
	return formatLookup[formatIndicator.text]

def _ParseDate(listItem):
	dateAttr = listItem.find_all(class_='cp-short-formatted-date')[0]
	if dateAttr is None:
		return None
	# text value here seems to have been run through some javascript
	return datetime.strptime(dateAttr.text, '%b %d, %Y').date()

def _ParseHoldPosition(listItem):
	text = listItem.find_all(class_='cp-hold-position')[0].text
	# log.info(text)
	match = search(r'\#(\d+) on (\d+) cop', text)
	return (match.group(1), match.group(2))
