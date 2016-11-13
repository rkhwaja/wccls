# coding=UTF-8
from datetime import datetime, timedelta
from logging import debug, error, warning
from os.path import join
from re import search

from wccls.wccls import ActiveHold, CancelledHold, CheckedOutItem, HeldItem, PendingItem, ShippedItem, SuspendedHold

from bs4 import BeautifulSoup
from requests import Session

class WcclsMobile:
	def __init__(self, login, password, host='https://catalog.wccls.org'):
		self.host = host
		self.session = Session()
		self.Login(login, password)
		self.items = self.CheckedOutItems() + self.Holds()

	def Login(self, login, password):
		# get on this returns the login form, post logs in
		loginUrl = self.host + '/Mobile/MyAccount/Logon'

		loginParameters = {
			'barcodeOrUsername': login,
			'password': password,
			'rememberMe': 'true' # doesn't seem to matter whether we say true or false
		}
		response = self.session.post(loginUrl, data=loginParameters)
		debug("Login reponse: {}".format(response))

	def ParseCheckedOutItem(self, tr):
		title = tr('td')[1]('a')[0].text
		allText = tr('td')[1].text.strip()[len(title):]
		splits = allText.split(' renewals leftDue: ')
		if len(splits) == 2:
			renewals = int(splits[0])
			datePlusPossibleOverdueSplits = splits[1].split(' ')
			if len(datePlusPossibleOverdueSplits) > 1:
				debug("Overdue")
			dueDate = datetime.strptime(datePlusPossibleOverdueSplits[0], '%m/%d/%Y').date()
			return CheckedOutItem(title, dueDate, renewals)

		index = allText.find("Due:")
		if index != -1:
			dueDate = datetime.strptime(allText[index + 5:], '%m/%d/%Y').date()
			return CheckedOutItem(title, dueDate, 0)

		warning("Failed to parse: " + allText.strip())
		return None

	def CheckedOutItems(self):
		items = []

		itemsOutUrl = self.host + '/Mobile/MyAccount/ItemsOut'
		r = self.session.get(itemsOutUrl, timeout=60)
		self.DumpDebugFile("itemsout-0.html", r.text)
		soup = BeautifulSoup(r.content, "lxml")

		breadcrumbsDiv = soup.find_all('div', id='breadcrumbs')
		breadcrumbsText = breadcrumbsDiv[0].text
		totalItemsMatch = search(r'\((\d+)', breadcrumbsText)
		if totalItemsMatch is None:
			return []
		totalItems = int(totalItemsMatch.group(1))
		itemsPerPage = 5
		totalPages = -(-totalItems // itemsPerPage) # round up
		debug("totalItems={}, totalPages={}".format(totalItems, totalPages))

		for tr in soup.find_all(lambda e: e.name == 'tr' and len(e('td')) != 0):
			checkedOutItem = self.ParseCheckedOutItem(tr)
			if checkedOutItem is not None:
				items.append(checkedOutItem)

		itemsOutWithPageUrl = self.host + '/Mobile/MyAccount/ItemsOut?page={}'

		for page in range(1, totalPages):
			url = itemsOutWithPageUrl.format(page)
			r = self.session.get(url, timeout=60)
			self.DumpDebugFile("itemsout-{}.html".format(page), r.text)
			soup = BeautifulSoup(r.content, "lxml")
			for tr in soup.find_all(lambda e: e.name == 'tr' and len(e('td')) != 0):
				items.append(self.ParseCheckedOutItem(tr))

		# assert(totalItems == len(items))
		return items

	def ParseHold(self, tr):
		td1 = tr('td')[1]
		title = td1.find('a').text
		debug("Hold: title=" + title)
		debug("td1.text=" + str(td1.text))
		text = td1.text[len(title):]
		match = search(r'(Held|Pending|Shipped|Active|Inactive|Cancelled|Unclaimed)\s*\((.*)\)', text)
		if match is None:
			errorMessage = 'Failed to parse hold. text="{}"'.format(text)
			error(errorMessage)
			raise RuntimeError(errorMessage)
		status = match.group(1)
		date = match.group(2)
		listPos = None
		listSize = None
		if status == "Pending":
			debug("Pending: " + text)
			return PendingItem(title=title, reservationDate=datetime.strptime(date.strip(), "as of %m/%d/%Y").date())
		elif status == "Shipped":
			date = datetime.now().date() - timedelta(days=int(date.strip()[:-8]))
			return ShippedItem(title=title, shippedDate=date)
		elif status == "Active":
			date = datetime.strptime(date.strip()[6:], '%m/%d/%Y').date()
			td2 = tr('td')[2]
			splits = td2.text.strip().split(' Of ')
			listPos = int(splits[0].strip())
			listSize = int(splits[1].strip())
			return ActiveHold(title=title, activationDate=date, queuePosition=listPos, queueSize=listSize)
		elif status == "Inactive":
			date = datetime.strptime(date.strip()[6:], '%m/%d/%Y').date()
			return SuspendedHold(title=title, reactivationDate=date)
		elif status == "Cancelled":
			date = datetime.strptime(date.strip()[3:], '%m/%d/%Y').date()
			return CancelledHold(title=title, cancellationDate=date)
		elif status == "Held":
			debug("Held: " + date)
			if date == "until tomorrow":
				days = 1
			elif date == "until today":
				days = 0
			else:
				match = search(r'for (\d+) more day', date)
				debug(str(match.group(1)) + ' more days')
				days = int(match.group(1))
			date = (datetime.today() + timedelta(days=days)).date()
			return HeldItem(title=title, expiryDate=date)
		elif status == "Unclaimed":
			debug("Unclaimed: " + date)
			assert False, "Unclaimed stuff is now cancelled"
		error("Unknown status type: " + status + ", text=" + text)
		return None

	def Holds(self):
		items = []
		holdsUrl = self.host + '/Mobile/MyAccount/Holds'
		r = self.session.get(holdsUrl, timeout=60)
		self.DumpDebugFile("holds-1.html", r.text)
		soup = BeautifulSoup(r.content, "lxml")

		for tr in soup.find_all(lambda e: e.name == 'tr' and len(e('td')) != 0):
			items.append(self.ParseHold(tr))

		footer = soup.find_all('div', class_='list-footer-options')[0].text
		pages = int(search(r"Page\s+1\s+of\s+(\d+)", footer).group(1))
		holdsWithPageUrl = self.host + "/Mobile/MyAccount/Holds?page={}"
		for page in range(1, pages):
			r = self.session.get(holdsWithPageUrl.format(page), timeout=60)
			self.DumpDebugFile("holds-{}.html".format(page), r.text)
			soup = BeautifulSoup(r.content, "lxml")
			for tr in soup.find_all(lambda e: e.name == 'tr' and len(e('td')) != 0):
				hold = self.ParseHold(tr)
				if hold is not None:
					items.append(hold)
				else:
					error("Failed to parse hold: " + str(tr))
		return items

	def DumpDebugFile(self, filename, content):
		if False:
			from tempfile import gettempdir
			with open(join(gettempdir(), "log", filename), "w") as theFile:
				theFile.write(content)
