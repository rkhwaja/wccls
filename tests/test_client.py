from logging import info
from os import environ
from pytest import mark

from wccls import Wccls, WcclsAsync

@mark.skipif('WCCLS_CARD_NUMBER' not in environ or 'WCCLS_PASSWORD' not in environ, reason='Need username and password')
def test_sync_client():
	items = Wccls(login=environ['WCCLS_CARD_NUMBER'], password=environ['WCCLS_PASSWORD'])
	# just expecting no errors
	info(f'{len(items)=}')

@mark.skipif('WCCLS_CARD_NUMBER' not in environ or 'WCCLS_PASSWORD' not in environ, reason='Need username and password')
@mark.asyncio
async def test_async_client():
	items = await WcclsAsync(login=environ['WCCLS_CARD_NUMBER'], password=environ['WCCLS_PASSWORD'])
	# just expecting no errors
	info(f'{len(items)=}')
