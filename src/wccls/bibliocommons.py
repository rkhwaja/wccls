from __future__ import annotations

from httpx import AsyncClient, Client

from .parser import Parser
from .item_types import Item

def _DoRequestSync(session, request):
	if request.verb == 'GET':
		response = session.get(request.url, follow_redirects=request.allowRedirects)
	elif request.verb == 'POST':
		response = session.post(request.url, data=request.data, follow_redirects=request.allowRedirects)
	else:
		assert False, f'Unexpected request: {request}'
	response.raise_for_status()
	return response.text

async def _DoRequestAsync(session, request):
	if request.verb == 'GET':
		resp = await session.get(request.url, follow_redirects=request.allowRedirects)
		resp.raise_for_status()
		return resp.text
	if request.verb == 'POST':
		resp = await session.post(request.url, data=request.data, follow_redirects=request.allowRedirects)
		resp.raise_for_status()
		return resp.text
	assert False, f'Unexpected request: {request}'

def BiblioCommons(subdomain: str, login: str, password: str) -> list[Item]:
	"""Gets the list of items for a Bibliocommons site"""
	parser = Parser(subdomain, login, password)
	with Client() as session:
		reqs = parser.Receive(None, None)
		while len(reqs) > 0:
			req = reqs.pop()
			resp = _DoRequestSync(session, req)
			reqs.extend(parser.Receive(req.url, resp))
	return parser.items

async def BiblioCommonsAsync(subdomain: str, login: str, password: str) -> list[Item]:
	"""Gets the list of items for a Bibliocommons site"""
	parser = Parser(subdomain, login, password)
	async with AsyncClient() as session:
		reqs = parser.Receive(None, None)
		while len(reqs) > 0:
			req = reqs.pop()
			response = await _DoRequestAsync(session, req)
			reqs.extend(parser.Receive(req.url, response))
		return parser.items

def Wccls(login: str, password: str) -> list[Item]:
	"""Gets the list of items for the WCCLS site"""
	return BiblioCommons('wccls', login, password)

def MultCoLib(login: str, password: str) -> list[Item]:
	"""Gets the list of items for the Multnomah County Library site"""
	return BiblioCommons('multcolib', login, password)

async def WcclsAsync(login: str, password: str) -> list[Item]:
	"""Gets the list of items for the WCCLS site"""
	return await BiblioCommonsAsync('wccls', login, password)

async def MultCoLibAsync(login: str, password: str) -> list[Item]:
	"""Gets the list of items for the Multnomah County Library site"""
	return await BiblioCommonsAsync('multcolib', login, password)
