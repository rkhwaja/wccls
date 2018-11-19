from datetime import datetime
from logging import debug
from os import makedirs
from os.path import join
from re import search
from tempfile import gettempdir

from requests_html import HTMLSession

from .wccls import ActiveHold, CheckedOutItem, HeldItem, ShippedItem, SuspendedHold

__all__ = ["BiblioCommons", "MultnomahBiblioCommons", "WcclsBiblioCommons"]

class BiblioCommons:
	def __init__(self, subdomain, login, password, debug_=False):
		self._debug = debug_
		self._domain = f"https://{subdomain}.bibliocommons.com"
		self._session = HTMLSession()
		self._Login(login, password)
		self.items = self._CheckedOut() + self._ReadyForPickup() + self._InTransit() + self._NotYetAvailable() + self._Suspended()

	def _Login(self, login, password):
		loginPage = self._session.get(f"{self._domain}/user/login")
		loginForm = loginPage.html.find(".loginForm", first=True)
		formData = {}
		for input_ in loginForm.find("input"):
			formData[input_.attrs["name"]] = input_.attrs["value"] if "value" in input_.attrs else ""
		formData["user_pin"] = password
		formData["name"] = login
		_ = self._session.post(loginForm.attrs["action"], data=formData)

	def _DumpDebugFile(self, filename, content):
		if not self._debug:
			return
		directory = join(gettempdir(), "log", "wccls")
		makedirs(directory, exist_ok=True)
		with open(join(directory, filename), "wb") as theFile:
			theFile.write(content)

	def _ParseItems(self, url, dumpfile, parseFunction):
		result = []
		# if there are no items in "ready_for_pickup", for instance, it will redirect back to the holds index, which we don't want
		page = self._session.get(url, allow_redirects=False)
		self._DumpDebugFile(dumpfile, page.content)
		page.raise_for_status()
		for listItem in page.html.find(".item-row"):
			debug(listItem)
			result.append(parseFunction(listItem))
		return result

	def _Suspended(self):
		return self._ParseItems(f"{self._domain}/v2/holds/suspended", "suspended.html", _ParseSuspended)

	def _NotYetAvailable(self):
		return self._ParseItems(f"{self._domain}/v2/holds/not_yet_available", "not-yet-available.html", _ParseNotYetAvailable)

	def _ReadyForPickup(self):
		return self._ParseItems(f"{self._domain}/v2/holds/ready_for_pickup", "ready-for-pickup.html", _ParseReadyForPickup)

	def _InTransit(self):
		return self._ParseItems(f"{self._domain}/v2/holds/in_transit", "in-transit.html", _ParseInTransit)

	def _CheckedOut(self):
		return self._ParseItems(f"{self._domain}/v2/checkedout", "checked-out.html", _ParseCheckedOut)

class WcclsBiblioCommons(BiblioCommons):
	def __init__(self, login, password, debug_=False):
		super().__init__(subdomain="wccls", login=login, password=password, debug_=debug_)

class MultnomahBiblioCommons(BiblioCommons):
	def __init__(self, login, password, debug_=False):
		super().__init__(subdomain="multcolib", login=login, password=password, debug_=debug_)

def _ParseSuspended(listItem):
	return SuspendedHold(
		title=listItem.find(".title-content", first=True).text,
		reactivationDate=_ParseDate2(listItem))

def _ParseNotYetAvailable(listItem):
	holdInfo = _ParseHoldPosition(listItem)
	return ActiveHold(
		title=listItem.find(".title-content", first=True).text,
		activationDate=_ParseDate2(listItem), # TODO - this isn't an activation date anymore - it's the expiry date
		queuePosition=holdInfo[0],
		queueSize=None, # Not shown on the initial screen anymore
		copies=holdInfo[1])

def _ParseReadyForPickup(listItem):
	return HeldItem(
		title=listItem.find(".title-content", first=True).text,
		expiryDate=_ParseDate("", listItem.find(".cp-short-formatted-date", first=True)))

def _ParseInTransit(listItem):
	return ShippedItem(
		title=listItem.find(".title-content", first=True).text,
		shippedDate=None) # they don't seem to show this anymore

def _ParseCheckedOut(listItem):
	renewals = 1 # we don't know how many renewals are really left - this just means at least one
	if listItem.find(".cp-held-copies-count", first=True) is not None:
		renewals = 0
	renewCountText = listItem.find(".cp-renew-count span:nth-of-type(2)", first=True)
	if renewCountText is not None:
		renewals = 4 - int(renewCountText.text[0])
	return CheckedOutItem(
		title=listItem.find(".title-content", first=True).text,
		dueDate=_ParseDate("", listItem.find(".cp-short-formatted-date", first=True)),
		renewals=renewals, # really should be a "renewable" flag
		isOverdrive=False) # need an example

def _ParseDate(prefix, element):
	assert element.text.startswith(prefix), f"{element.text}"
	return datetime.strptime(element.text[len(prefix):], "%b %d, %Y").date()

def _ParseDate2(listItem):
	dateAttr = listItem.find(".cp-short-formatted-date", first=True)
	if dateAttr is None:
		return None
	# text value here seems to have been run through some javascript
	return datetime.strptime(dateAttr.text, "%b %d, %Y").date()

def _ParseHoldPosition(listItem):
	text = listItem.find(".cp-hold-position", first=True).text
	match = search(r"\#(\d+) on (\d+) cop", text)
	return (match.group(1), match.group(2))
