# coding=UTF-8
from datetime import datetime, timedelta
from logging import debug, error, warning
from os.path import join
from re import match, search
from tempfile import gettempdir

from bs4 import BeautifulSoup
from requests import Session

from .wccls import ActiveHold, CancelledHold, CheckedOutItem, HeldItem, ParseError, PendingItem, ShippedItem, SuspendedHold

__all__ = ["WcclsMobile"]

class WcclsMobile:
	def __init__(self, login, password, debug_=False):
		self._host = "https://catalog.wccls.org"
		self._debug = debug_
		self._session = Session()
		self._Login(login, password)
		self.items = self._CheckedOutItems() + self._Holds()

	def _Login(self, login, password):
		# get on this returns the login form, post logs in
		loginUrl = self._host + '/Mobile/MyAccount/Logon'

		loginParameters = {
			'barcodeOrUsername': login,
			'password': password,
			'rememberMe': 'true' # doesn't seem to matter whether we say true or false
		}
		response = self._session.post(loginUrl, data=loginParameters)
		debug(f"Login reponse: {response}")

	def _ParseCheckedOutItem(self, tr): # pylint: disable=no-self-use,too-many-locals
		td = tr("td")[1] # zeroth td is the renewal checkbox
		title = td("a")[0].text # title is in the <a> tag
		allText = td.text.strip()[len(title):]
		splits = allText.split(' renewals leftDue: ')
		if len(splits) == 2:
			renewals = int(splits[0])
			datePlus = splits[1]
			justDate = match(r"(\d+/\d+/\d{4})", datePlus).group(1)
			dueDate = datetime.strptime(justDate, '%m/%d/%Y').date()
			isOverdrive = td("select")
			assert isinstance(isOverdrive, list)
			return CheckedOutItem(title, dueDate, renewals, len(isOverdrive) != 0)

		splits = allText.split("\xa0")

		if len(splits) >= 2:
			dueDate = datetime.strptime(splits[1], '%m/%d/%Y').date()
			return CheckedOutItem(title, dueDate, 0, True)

		assert False, "Unexpected format"
		index = allText.find("Due:")
		if index != -1:
			dueDate = datetime.strptime(allText[index + 5:], '%m/%d/%Y').date()
			return CheckedOutItem(title, dueDate, 0, False)

		warning("Failed to parse: " + allText.strip())
		return None

	def _ParseCheckedOutPage(self, pageNumber):
		response = self._session.get(f"{self._host}/Mobile/MyAccount/ItemsOut?page={pageNumber}", timeout=60)
		self._DumpDebugFile(f"itemsout-{pageNumber}.html", response.text)
		soup = BeautifulSoup(response.content, "html.parser")

		items = []
		for tr in soup.find_all(lambda e: e.name == "tr" and len(e("td")) != 0):
			checkedOutItem = self._ParseCheckedOutItem(tr)
			if checkedOutItem is not None:
				items.append(checkedOutItem)
		return soup, items

	def _CheckedOutItems(self): # pylint: disable=too-many-locals
		soup, items = self._ParseCheckedOutPage(0)

		breadcrumbsDiv = soup.find_all('div', id='breadcrumbs')
		breadcrumbsText = breadcrumbsDiv[0].text
		totalItemsMatch = search(r'\((\d+)', breadcrumbsText)
		if totalItemsMatch is None:
			return []
		totalItems = int(totalItemsMatch.group(1))
		itemsPerPage = 5
		totalPages = -(-totalItems // itemsPerPage) # round up
		debug(f"totalItems={totalItems}, totalPages={totalPages}")

		for page in range(1, totalPages):
			items.extend(self._ParseCheckedOutPage(page)[1])

		# assert(totalItems == len(items))
		return items

	def _ParseHold(self, tr): # pylint: disable=no-self-use,too-many-return-statements,too-many-locals
		td1 = tr('td')[1]
		anchors = td1.find_all('a')
		title = anchors[0].text
		if len(anchors) >= 2 and anchors[1].text == 'Check Out':
			# the desktop site has the expiry date, but not the mobile site
			return HeldItem(title=title, expiryDate=None)

		text = td1.text[len(title):]
		match_ = search(r'(Held|Pending|Shipped|Active|Inactive|Cancelled|Unclaimed)\s*\((.*)\)', text)
		if match_ is None:
			errorMessage = f'Failed to parse hold. text="{text}"'
			error(errorMessage)
			raise ParseError(errorMessage)

		status = match_.group(1)
		date = match_.group(2)

		if status == "Pending":
			return PendingItem(title=title, reservationDate=datetime.strptime(date.strip(), "as of %m/%d/%Y").date())

		if status == "Shipped":
			date = datetime.now().date() - timedelta(days=int(date.strip()[:-8]))
			return ShippedItem(title=title, shippedDate=date)

		if status == "Active":
			date = datetime.strptime(date.strip()[6:], '%m/%d/%Y').date()
			td2 = tr('td')[2]
			splits = td2.text.strip().split(' Of ')
			listPos = int(splits[0].strip())
			listSize = int(splits[1].strip())
			return ActiveHold(title=title, activationDate=date, queuePosition=listPos, queueSize=listSize, copies=None)

		if status == "Inactive":
			date = datetime.strptime(date.strip()[6:], '%m/%d/%Y').date()
			return SuspendedHold(title=title, reactivationDate=date)

		if status == "Cancelled":
			date = datetime.strptime(date.strip()[3:], '%m/%d/%Y').date()
			return CancelledHold(title=title, cancellationDate=date)

		if status == "Held":
			if date == "until tomorrow":
				days = 1
			elif date == "until today":
				days = 0
			else:
				match_ = search(r'for (\d+) more day', date)
				days = int(match_.group(1))
			date = (datetime.today() + timedelta(days=days)).date()
			return HeldItem(title=title, expiryDate=date)

		if status == "Unclaimed":
			raise ParseError("Unclaimed stuff is now cancelled")

		raise ParseError(f"Unknown status type: {status}, text={text}")

	def _ParseHoldsPage(self, pageNumber):
		response = self._session.get(f"{self._host}/Mobile/MyAccount/Holds?page={pageNumber}", timeout=60)
		self._DumpDebugFile(f"holds-{pageNumber}.html", response.text)
		soup = BeautifulSoup(response.content, "html.parser")

		items = []
		for tr in soup.find_all(lambda e: e.name == "tr" and len(e("td")) != 0):
			hold = self._ParseHold(tr)
			items.append(hold)
		return soup, items

	def _Holds(self):
		try:
			soup, items = self._ParseHoldsPage(0)

			footer = soup.find_all("div", class_="list-footer-options")[0].text
			pages = int(search(r"Page\s+1\s+of\s+(\d+)", footer).group(1))

			for page in range(1, pages):
				items.extend(self._ParseHoldsPage(page)[1])
		except IndexError as e:
			raise ParseError from e

		return items

	def _DumpDebugFile(self, filename, content):
		if not self._debug:
			return
		with open(join(gettempdir(), "log", filename), "w") as theFile:
			theFile.write(content)
