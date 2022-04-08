from os import environ

from pytest import mark

from wccls import BiblioCommons, BiblioCommonsAsync, Wccls, WcclsAsync

@mark.asyncio
async def testBibliocommonsAsync():
	items = await BiblioCommonsAsync('wccls', environ['WCCLS_CARD_NUMBER'], environ['WCCLS_PASSWORD'])
	assert len(items) == 7

def testBibliocommonsSync():
	items = BiblioCommons('wccls', environ['WCCLS_CARD_NUMBER'], environ['WCCLS_PASSWORD'])
	assert len(items) == 7

@mark.asyncio
async def testWcclsAsync():
	items = await WcclsAsync(environ['WCCLS_CARD_NUMBER'], environ['WCCLS_PASSWORD'])
	assert len(items) == 7

def testWcclsSync():
	items = Wccls(environ['WCCLS_CARD_NUMBER'], environ['WCCLS_PASSWORD'])
	assert len(items) == 7
