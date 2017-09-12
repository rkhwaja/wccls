#!/usr/bin/env python3

from logging import info
from os import environ

from wccls import WcclsDesktop, WcclsMobile

def test_desktop():
	cardNumber = environ["WCCLS_CARD_NUMBER"]
	password = environ["WCCLS_PASSWORD"]
	wccls = WcclsDesktop(login=cardNumber, password=password, debug=True)
	for item in wccls.items:
		info(item)

# mobile website parsing appears to be broken - just use the desktop one which is better in every way anyway
# def test_mobile():
# 	cardNumber = environ["WCCLS_CARD_NUMBER"]
# 	password = environ["WCCLS_PASSWORD"]
# 	wccls = WcclsMobile(login=cardNumber, password=password)
# 	for item in wccls.items:
# 		info(item)
