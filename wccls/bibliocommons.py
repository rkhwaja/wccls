from datetime import datetime
from logging import info
from os.path import join
from re import search
from tempfile import gettempdir

from requests_html import HTMLSession

from .wccls import ActiveHold, CheckedOutItem, HeldItem, ShippedItem, SuspendedHold

__all__ = ["WcclsBiblioCommons"]

class WcclsBiblioCommons:
	def __init__(self, login, password, debug_=False):
		self._debug = debug_
		self._session = HTMLSession()
		self._Login(login, password)
		self.items = self._CheckedOut() + self._ReadyForPickup() + self._InTransit() + self._NotYetAvailable() + self._Suspended()

	def _Login(self, login, password):
		loginPage = self._session.get("https://wccls.bibliocommons.com/user/login")
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

	def _Suspended(self):
		result = []
		page = self._session.get("https://wccls.bibliocommons.com/holds/index/suspended")
		self._DumpDebugFile("suspended.html", page.content)
		for listItem in page.html.find(".listItem"):
			info(listItem)
			result.append(SuspendedHold(
				title=listItem.find(".title", first=True).text,
				reactivationDate=_ParseDate2(listItem)))

		return result

	def _NotYetAvailable(self):
		result = []
		page = self._session.get("https://wccls.bibliocommons.com/holds/index/not_yet_available")
		self._DumpDebugFile("not-yet-available.html", page.content)
		for listItem in page.html.find(".listItem"):
			info(listItem)
			holdInfo = _ParseHoldPosition(listItem)
			result.append(ActiveHold(
				title=listItem.find(".title", first=True).text,
				activationDate=_ParseDate3(listItem),
				queuePosition=holdInfo[0],
				queueSize=None, # Not shown on the initial screen anymore
				copies=holdInfo[1]))

		return result

	def _ReadyForPickup(self):
		result = []
		page = self._session.get("https://wccls.bibliocommons.com/holds/index/ready_for_pickup")
		self._DumpDebugFile("ready-for-pickup.html", page.content)
		for listItem in page.html.find(".listItem"):
			info(listItem)
			result.append(HeldItem(
				title=listItem.find(".title", first=True).text,
				expiryDate=_ParseDate("Pickup by: ", listItem.find(".pick_up_date", first=True))))

		return result

	def _InTransit(self):
		result = []
		page = self._session.get("https://wccls.bibliocommons.com/holds/index/in_transit")
		self._DumpDebugFile("in-transit.html", page.content)
		for listItem in page.html.find(".listItem"):
			info(listItem)
			result.append(ShippedItem(
				title=listItem.find(".title", first=True).text,
				shippedDate=None)) # they don't seem to show this anymore

		return result

	def _CheckedOut(self):
		result = []
		checkedOutUrl = "https://wccls.bibliocommons.com/checkedout"
		page = self._session.get(checkedOutUrl)
		self._DumpDebugFile("checked-out.html", page.content)
		for listItem in page.html.find(".listItem"):
			result.append(CheckedOutItem(
				title=listItem.find(".title", first=True).text,
				dueDate=_ParseDate("Due on: \xa0", listItem.find(".checkedout_due_date", first=True)),
				renewals=None, # need an example
				isOverdrive=False)) # need an example
		return result

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
