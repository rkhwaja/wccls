#!/usr/bin/env python

from logging import info
from os import environ
from pprint import pformat

from wccls import MultnomahBiblioCommons, StatusType, Wccls, WcclsBiblioCommons

def CheckOutput(items):
	itemsByStatus = {}
	for status in StatusType:
		itemsByStatus[status] = 0
	checkedOutOverdriveCount = 0
	heldOverdriveCount = 0
	for item in items:
		info(item)
		itemsByStatus[item.status] += 1
		if item.status == StatusType.CheckedOut and item.isOverdrive is True:
			checkedOutOverdriveCount += 1
		if item.status == StatusType.Held and item.isOverdrive is True:
			heldOverdriveCount += 1

	assert checkedOutOverdriveCount == int(environ["WCCLS_COUNT_CHECKEDOUT_OVERDRIVE"]), "Mismatch in CheckedOut Overdrive count"
	assert heldOverdriveCount == int(environ["WCCLS_COUNT_HELD_OVERDRIVE"]), "Mismatch in Held Overdrive count"

	for status, count in itemsByStatus.items():
		assert count == int(environ[f"WCCLS_COUNT_{status.name.upper()}"]), f"Mismatch in {status.name} count. {pformat(itemsByStatus)}"

def test_recommended():
	wccls = Wccls(login=environ["WCCLS_CARD_NUMBER"], password=environ["WCCLS_PASSWORD"], debug_=False)
	CheckOutput(wccls.items)

def test_wccls_bibliocommons():
	wccls = WcclsBiblioCommons(login=environ["WCCLS_CARD_NUMBER"], password=environ["WCCLS_PASSWORD"], debug_=True)
	CheckOutput(wccls.items)

def test_multnomah_bibliocommons():
	library = MultnomahBiblioCommons(login=environ["MULTNOMAH_CARD_NUMBER"], password=environ["MULTNOMAH_PASSWORD"], debug_=True)
	CheckOutput(library.items)
