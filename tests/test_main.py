#!/usr/bin/env python

from logging import info
from os import environ
from unittest import skip

from wccls import StatusType, Wccls, WcclsDesktop, WcclsMobile

def CheckOutput(items):
	itemsByStatus = {}
	overdriveCount = 0
	for item in items:
		info(item)
		itemsByStatus[item.status] = itemsByStatus.get(item.status, 0) + 1
		if item.status == StatusType.CheckedOut and item.isOverdrive is True:
			overdriveCount += 1

	assert overdriveCount == int(environ["WCCLS_COUNT_OVERDRIVE"]), "Mismatch in Overdrive count"

	for status, count in itemsByStatus.items():
		assert count == int(environ[f"WCCLS_COUNT_{status.name.upper()}"]), f"Mismatch in {status.name} count"

@skip("Can't login to desktop site")
def test_desktop():
	wccls = WcclsDesktop(login=environ["WCCLS_CARD_NUMBER"], password=environ["WCCLS_PASSWORD"], debug_=False)
	CheckOutput(wccls.items)

def test_mobile():
	wccls = WcclsMobile(login=environ["WCCLS_CARD_NUMBER"], password=environ["WCCLS_PASSWORD"], debug_=False)
	CheckOutput(wccls.items)

def test_recommended():
	wccls = Wccls(login=environ["WCCLS_CARD_NUMBER"], password=environ["WCCLS_PASSWORD"], debug_=False)
	CheckOutput(wccls.items)

def test_bibliocommons():
	wccls = WcclsBiblioCommons(username=environ["WCCLS_CARD_NUMBER"], password=environ["WCCLS_PASSWORD"], debug=True)
