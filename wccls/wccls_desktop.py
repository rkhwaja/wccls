from datetime import datetime, timedelta
from logging import debug
from os.path import join
from re import search

from bs4 import BeautifulSoup
from requests import Session

from .wccls import ActiveHold, CancelledHold, CheckedOutItem, HeldItem, PendingItem, ShippedItem, SuspendedHold, UnclaimedHold

__all__ = ["WcclsDesktop"]

class WcclsDesktop:
	def __init__(self, login, password, debug_=False, host='https://catalog.wccls.org'):
		self._debug = debug_
		self._host = host
		self._session = Session()
		self._Login(login, password)
		self.items = self._CheckedOutItems() + self._Holds()

	def _Login(self, login, password):
		# first get https://catalog.wccls.org/polaris/logon.aspx
		# and pull the __VIEWSTATE parameter out of it

		# posts to the same place
		loginUrl = self._host + '/polaris/logon.aspx'
		# display of login page is https://catalog.wccls.org/polaris/logon.aspx

		headers = {
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
			'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.75 Safari/537.36',
		}

		response = self._session.get(loginUrl, headers=headers, timeout=60)
		response.raise_for_status()
		self._SaveDebugFile("logon.html", response.content)

		soup = BeautifulSoup(response.text, "html.parser")

		viewState = soup.find_all(id="__VIEWSTATE")[0]["value"]

		viewStateGenerator = soup.find_all(id="__VIEWSTATEGENERATOR")[0]["value"]

		eventValidation = soup.find_all(id="__EVENTVALIDATION")[0]["value"]

		loginParameters = {
			'__VIEWSTATE': viewState,
			'__VIEWSTATEGENERATOR': viewStateGenerator,
			'__EVENTVALIDATION': eventValidation,
			"textboxBarcodeUsername": login,
			"textboxPassword": password,
			"buttonSubmit": "Log+In"
		}
		headers = {
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
			"Host": "catalog.wccls.org",
			"Connection": "keep-alive",
			'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.75 Safari/537.36',
			"Origin": "Origin: https://catalog.wccls.org",
			"Content-Type": "application/x-www-form-urlencoded"
		}
		r = self._session.post(loginUrl, data=loginParameters, headers=headers, timeout=60)
		r.raise_for_status()
		self._SaveDebugFile("after-login.html", response.content)

	def _SaveDebugFile(self, filename, content):
		if self._debug:
			from tempfile import gettempdir
			with open(join(gettempdir(), "log", filename), "wb") as theFile:
				theFile.write(content)

	def _ParseHoldDate(self, dateString): # pylint: disable=no-self-use
		if dateString == "(until tomorrow)":
			days = 1
		elif dateString == "(until today)":
			days = 0
		else:
			match = search(r'for (\d+) more day', dateString)
			days = int(match.group(1))
		return (datetime.today() + timedelta(days=days)).date()

	def _ParseShippedDate(self, dateString): # pylint: disable=no-self-use
		if dateString == "(yesterday)":
			days = 1
		elif dateString == "(today)":
			days = 0
		else:
			match = search(r"\((\d+) days ago\)", dateString)
			days = int(match.group(1))
		return (datetime.today() - timedelta(days=days)).date()

	def _ParseQueueText(self, queueText): # pylint: disable=no-self-use
		splits = queueText.split(' of ')
		return (int(splits[0].strip()), int(splits[1].strip()))

	def _CheckedOutItems(self):
		itemsOutUrl = self._host + '/polaris/patronaccount/itemsout.aspx'
		r = self._session.get(itemsOutUrl, timeout=60)
		r.raise_for_status()
		self._SaveDebugFile("desktop-checked-out.html", r.content)

		soup = BeautifulSoup(r.text, "html.parser")
		items = []
		for row in soup.find_all(class_="patrongrid-row") + soup.find_all(class_="patrongrid-alternating-row"):
			tds = row.find_all("td")
			renewalsTds = tds[7]
			assert False, "Overdrive doesn't work"
			items.append(CheckedOutItem(title=tds[4].span.a.contents[0],
				dueDate=datetime.strptime(tds[6].span.contents[0], "%m/%d/%Y").date(),
				renewals=int(renewalsTds.span.contents[0]) if renewalsTds.span is not None else None, isOverdrive=False))
		return items

	def _Holds(self):
		url = self._host + '/polaris/patronaccount/requests.aspx'
		r = self._session.get(url, timeout=60)
		r.raise_for_status()
		self._SaveDebugFile("desktop-holds.html", r.content)

		soup = BeautifulSoup(r.text, "html.parser")

		items = []
		for row in soup.find_all(class_="patrongrid-row") + soup.find_all(class_="patrongrid-alternating-row"):
			tds = row.find_all("td")
			title = tds[3].span.a.contents[0]
			status = tds[5].span.contents[0]
			dateInfo = tds[5].find_all("span")[1].contents[0]
			if status == "Held":
				item = HeldItem(title=title,
					expiryDate=self._ParseHoldDate(dateInfo))
			elif status == "Active":
				queueData = self._ParseQueueText(tds[6].span.contents[0])
				item = ActiveHold(title=title,
					activationDate=datetime.strptime(dateInfo, "(since %m/%d/%Y)").date(),
					queuePosition=queueData[0],
					queueSize=queueData[1],
					copies=None)
			elif status == "Shipped":
				item = ShippedItem(title=title,
					shippedDate=self._ParseShippedDate(dateInfo))
			elif status == "Inactive":
				item = SuspendedHold(title=title,
					reactivationDate=datetime.strptime(dateInfo, "(until %m/%d/%Y)").date())
			elif status == "Cancelled":
				item = CancelledHold(title=title,
					cancellationDate=datetime.strptime(dateInfo, "(on %m/%d/%Y)").date())
			elif status == "Pending":
				reservationDate = datetime.strptime(dateInfo, "(as of %m/%d/%Y)").date()
				item = PendingItem(title=title, reservationDate=reservationDate)
			elif status == "Unclaimed":
				item = UnclaimedHold(title=title)
			else:
				debug(f"Status: {status}, dateInfo: {dateInfo}")
				assert False
			items.append(item)
		return items
