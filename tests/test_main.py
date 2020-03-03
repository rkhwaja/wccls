#!/usr/bin/env python

from logging import info
from os import environ
from pprint import pformat

from wccls import MultCoLibBiblioCommons, StatusType, Wccls, WcclsBiblioCommons

def CheckOutput(items, prefix):
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

	assert checkedOutOverdriveCount == int(environ[f"{prefix}_COUNT_CHECKEDOUT_OVERDRIVE"]), "Mismatch in CheckedOut Overdrive count"
	assert heldOverdriveCount == int(environ[f"{prefix}_COUNT_HELD_OVERDRIVE"]), "Mismatch in Held Overdrive count"

	for status, count in itemsByStatus.items():
		assert count == int(environ[f"{prefix}_COUNT_{status.name.upper()}"]), f"Mismatch in {status.name} count. {pformat(itemsByStatus)}"

def test_wccls():
	library = WcclsBiblioCommons(login=environ["WCCLS_CARD_NUMBER"], password=environ["WCCLS_PASSWORD"], debug_=True)
	CheckOutput(library.items, "WCCLS")

def test_multcolib():
	library = MultCoLibBiblioCommons(login=environ["MULTCOLIB_CARD_NUMBER"], password=environ["MULTCOLIB_PASSWORD"], debug_=True)
	CheckOutput(library.items, "MULTCOLIB")
