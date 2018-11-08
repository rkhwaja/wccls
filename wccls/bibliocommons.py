from datetime import datetime
from logging import debug
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
		with open(join(gettempdir(), "log", filename), "wb") as theFile:
			theFile.write(content)

	def _ParseItems(self, url, dumpfile, parseFunction):
		result = []
		# if there are no items in "ready_for_pickup", for instance, it will redirect back to the holds index, which we don't want
		page = self._session.get(url, allow_redirects=False)
		self._DumpDebugFile(dumpfile, page.content)
		for listItem in page.html.find(".listItem"):
			debug(listItem)
			result.append(parseFunction(listItem))
		return result

	def _Suspended(self):
		return self._ParseItems(f"{self._domain}/holds/index/suspended", "suspended.html", _ParseSuspended)

	def _NotYetAvailable(self):
		return self._ParseItems(f"{self._domain}/holds/index/not_yet_available", "not-yet-available.html", _ParseNotYetAvailable)

	def _ReadyForPickup(self):
		return self._ParseItems(f"{self._domain}/holds/index/ready_for_pickup", "ready-for-pickup.html", _ParseReadyForPickup)

	def _InTransit(self):
		return self._ParseItems(f"{self._domain}/holds/index/in_transit", "in-transit.html", _ParseInTransit)

	def _CheckedOut(self):
		return self._ParseItems(f"{self._domain}/checkedout", "checked-out.html", _ParseCheckedOut)

class WcclsBiblioCommons(BiblioCommons):
	def __init__(self, login, password, debug_=False):
		super().__init__(subdomain="wccls", login=login, password=password, debug_=debug_)

class MultnomahBiblioCommons(BiblioCommons):
	def __init__(self, login, password, debug_=False):
		super().__init__(subdomain="multcolib", login=login, password=password, debug_=debug_)

def _ParseSuspended(listItem):
	return SuspendedHold(
		title=listItem.find(".title", first=True).text,
		reactivationDate=_ParseDate2(listItem))

def _ParseNotYetAvailable(listItem):
	holdInfo = _ParseHoldPosition(listItem)
	return ActiveHold(
		title=listItem.find(".title", first=True).text,
		activationDate=_ParseDate3(listItem),
		queuePosition=holdInfo[0],
		queueSize=None, # Not shown on the initial screen anymore
		copies=holdInfo[1])

def _ParseReadyForPickup(listItem):
	return HeldItem(
		title=listItem.find(".title", first=True).text,
		expiryDate=_ParseDate("Pickup by: ", listItem.find(".pick_up_date", first=True)))

def _ParseInTransit(listItem):
	return ShippedItem(
		title=listItem.find(".title", first=True).text,
		shippedDate=None) # they don't seem to show this anymore

def _ParseCheckedOut(listItem):
	return CheckedOutItem(
		title=listItem.find(".title", first=True).text,
		dueDate=_ParseDate("Due on: \xa0", listItem.find(".checkedout_due_date", first=True)),
		renewals=None, # need an example
		isOverdrive=False) # need an example

def _ParseDate(prefix, element):
	assert element.text.startswith(prefix), f"{element.text}"
	return datetime.strptime(element.text[len(prefix):], "%b %d, %Y").date()

def _ParseDate2(listItem):
	dateAttr = listItem.find("a[data-value]", first=True)
	# text value here seems to have been run through some javascript
	return datetime.strptime(dateAttr.text, "%b %d, %Y").date()

def _ParseDate3(listItem):
	dateAttr = listItem.find(".hold_expiry_date", first=True)
	return datetime.strptime(dateAttr.text, "%b %d, %Y").date()

def _ParseHoldPosition(listItem):
	text = listItem.find(".hold_position", first=True).text
	match = search(r"\#(\d+) on (\d+) cop", text)
	return (match.group(1), match.group(2))
