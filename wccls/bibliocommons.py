from datetime import datetime
from pprint import pprint

from requests_html import HTMLSession

from .wccls import ActiveHold, CheckedOutItem, HeldItem, SuspendedHold

__all__ = ["WcclsBiblioCommons"]

class WcclsBiblioCommons:
	def __init__(self, username, password, debug_=False):
		self._debug = debug_
		self._session = HTMLSession()
		self._Login(username, password)
		self.items = self._CheckedOutItems()
		# self.items.append(self._HeldItems())

	def _Login(self, username, password):
		loginPage = self._session.get("https://wccls.bibliocommons.com/user/login?destination=%2F")
		loginForm = loginPage.html.find(".loginForm", first=True)
		formData = {}
		for input_ in loginForm.find("input"):
			formData[input_.attrs["name"]] = input_.attrs["value"] if "value" in input_.attrs else ""
		formData["user_pin"] = password
		formData["name"] = username
		loggedInPage = self._session.post(loginForm.attrs["action"], data=formData)

	def _DumpDebugFile(self, filename, content):
		if not self._debug:
			return
		with open(join(gettempdir(), "log", filename), "wb") as theFile:
			theFile.write(content)

	def _ParseDate(self, prefix, element):
		assert element.text.startswith(prefix)
		return datetime.strptime(element.text[len(prefix):], "%b %d, %Y").date()

	def _HeldItems(self):
		result = []
		page = self._session.get("https://wccls.bibliocommons.com/holds")
		self._DumpDebugFile("holds.html", page.content)
		for listItem in page.html.find(".listItem)"):
			holdStatusElement = listItem.find(".hold_status_icon")
			classes = holdStatusElement.attrs["class"].split(" ")
			if "icon-ok-circled" in classes:
				result.append(HeldItem(
				title=listItem.find(".title", first=True).text,
				expiryDate=self._ParseDate("Pickup by: \xa0", listItem.find(".pick_up_date", first=True))))
			elif "icon-truck" in classes:
				result.append(ShippedItem(
					title=listItem.find(".title", first=True).text,
					shippedDate=None)) # need an example
			elif "icon-minus-circled" in classes:
				result.append(ActiveHold(
					title=listItem.find(".title", first=True).text,
					activationDate=None, # need an example
					queuePosition=None, # need to parse it out of .hold_position
					queueSize=None)) # need to parse it out of .hold_position
			elif "icon-pause-circled":
				result.append(SuspendedHold(
					title=listItem.find(".title", first=True).text,
					reactivationDate=_ParseDate("", listItem.find(".hold_expiry_date"))))

		return result

	def _CheckedOutItems(self):
		result = []
		checkedOutUrl = "https://wccls.bibliocommons.com/checkedout"
		page = self._session.get(checkedOutUrl)
		self._DumpDebugFile("checked-out-items.html", page.content)
		for listItem in page.html.find(".listItem"):
			result.append(CheckedOutItem(
				title=listItem.find(".title", first=True).text,
				dueDate=self._ParseDate("Due on: \xa0", listItem.find(".checkedout_due_date", first=True)),
				renewals=0, # need an example
				isOverdrive=False)) # need an example
		return result
