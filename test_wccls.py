#!/usr/bin/env python3

from logging import info
from os import environ
from unittest import skip

from wccls import StatusType, Wccls, WcclsDesktop, WcclsMobile

def CheckOutput(items):
	itemsByStatus = {}
	for item in items:
		info(item)
		itemsByStatus[item.status] = itemsByStatus.get(item.status, 0) + 1

	for status, count in itemsByStatus.items():
		assert count == int(environ[f"WCCLS_COUNT_{status.name.upper()}"])

@skip("Can't login to desktop site")
def test_desktop():
	wccls = WcclsDesktop(login=environ["WCCLS_CARD_NUMBER"], password=environ["WCCLS_PASSWORD"], debug=False)
	CheckOutput(wccls.items)

# mobile website parsing appears to be broken - just use the desktop one which is better in every way anyway
def test_mobile():
	wccls = WcclsMobile(login=environ["WCCLS_CARD_NUMBER"], password=environ["WCCLS_PASSWORD"], debug=False)
	CheckOutput(wccls.items)

def test_recommended():
	wccls = Wccls(login=environ["WCCLS_CARD_NUMBER"], password=environ["WCCLS_PASSWORD"], debug=False)
	CheckOutput(wccls.items)
