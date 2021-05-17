#!/usr/bin/env python

from os import environ
from pprint import pformat

from pytest import mark

from wccls import MultCoLibBiblioCommons, StatusType, WcclsBiblioCommons

def CheckOutput(items, prefix):
	actualCount = {}
	actualDigitalCount = {}
	expectedCount = {}
	expectedDigitalCount = {}
	for status in StatusType:
		actualCount[status] = 0
		actualDigitalCount[status] = 0
		countString = environ[f'{prefix}_COUNT_{status.name.upper()}'].split('/')
		expectedCount[status] = int(countString[0])
		expectedDigitalCount[status] = int(countString[1])
	for item in items:
		actualCount[item.status] += 1
		if item.isDigital is True:
			actualDigitalCount[item.status] += 1
		attributesNotNone = ['dueDate', 'reactivationDate', 'expiryDate', 'shippedDate', 'activationDate', 'queuePosition', 'copies']
		for attribute in attributesNotNone:
			if hasattr(item, attribute):
				assert getattr(item, attribute) is not None, f"{item} {attribute} didn't parse correctly"

	for status in StatusType:
		assert actualCount[status] == expectedCount[status], f'Mismatch in {status.name} count. {pformat(actualCount)}\n{pformat(items)}'
		assert actualDigitalCount[status] == expectedDigitalCount[status], f'Mismatch in {status.name} digital count. {pformat(actualDigitalCount)}\n{pformat(items)}'

def ScrubStrings(stringReplacementPairs):
	def BeforeRecordResponse(response):
		for string, replacement in stringReplacementPairs:
			response['body']['string'] = response['body']['string'].replace(string.encode(), replacement.encode())
			if 'headers' in response and 'Set-Cookie' in response['headers']:
				cookies = []
				for cookie in response['headers']['Set-Cookie']:
					cookies.append(cookie.replace(string, replacement))
				response['headers']['Set-Cookie'] = cookies
		return response
	return BeforeRecordResponse

@mark.vcr(
	filter_post_data_parameters=['name', 'user_pin'],
	filter_headers=['Cookie'],
	decode_compressed_response=True,
	before_record_response=ScrubStrings([
		(environ['WCCLS_CARD_NUMBER'], 'WCCLS_CARD_NUMBER'),
		(environ['SCRUB_EMAIL'], 'SCRUBBED_EMAIL')]))
def test_wccls():
	library = WcclsBiblioCommons(login=environ['WCCLS_CARD_NUMBER'], password=environ['WCCLS_PASSWORD'], debug_=False)
	CheckOutput(library.items, 'WCCLS')

@mark.vcr(
	filter_post_data_parameters=['name', 'user_pin'],
	filter_headers=['Cookie'],
	decode_compressed_response=True,
	before_record_response=ScrubStrings([
		(environ['MULTCOLIB_CARD_NUMBER'], 'MULTCOLIB_CARD_NUMBER'),
		(environ['SCRUB_EMAIL'], 'SCRUBBED_EMAIL')]))
def test_multcolib():
	library = MultCoLibBiblioCommons(login=environ['MULTCOLIB_CARD_NUMBER'], password=environ['MULTCOLIB_PASSWORD'], debug_=False)
	CheckOutput(library.items, 'MULTCOLIB')
