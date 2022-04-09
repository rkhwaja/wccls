from typing import List

from aiohttp import ClientSession
from requests import Session

from .parser import Parser
from .wccls import Item

def _DoRequestSync(session, request):
	if request.verb == 'GET':
		response = session.get(request.url, allow_redirects=request.allowRedirects)
	elif request.verb == 'POST':
		response = session.post(request.url, data=request.data, allow_redirects=request.allowRedirects)
	else:
		assert False, f'Unexpected request: {request}'
	response.raise_for_status()
	return response.text

async def _DoRequestAsync(session, request):
	if request.verb == 'GET':
		async with session.get(request.url, allow_redirects=request.allowRedirects, raise_for_status=True) as resp:
			return await resp.text()
	elif request.verb == 'POST':
		async with session.post(request.url, data=request.data, allow_redirects=request.allowRedirects, raise_for_status=True) as resp:
			return await resp.text()
	else:
		assert False, f'Unexpected request: {request}'

def BiblioCommons(subdomain: str, login: str, password: str) -> List[Item]:
	parser = Parser(subdomain, login, password)
	with Session() as session:
		reqs = parser.Receive(None, None)
		while len(reqs) > 0:
			req = reqs.pop()
			resp = _DoRequestSync(session, req)
			reqs.extend(parser.Receive(req.url, resp))
	return parser.items

async def BiblioCommonsAsync(subdomain: str, login: str, password: str) -> List[Item]:
	parser = Parser(subdomain, login, password)
	async with ClientSession() as session:
		reqs = parser.Receive(None, None)
		while len(reqs) > 0:
			req = reqs.pop()
			response = await _DoRequestAsync(session, req)
			reqs.extend(parser.Receive(req.url, response))
		return parser.items

Wccls = lambda login, password: BiblioCommons('wccls', login, password)
MultCoLib = lambda login, password: BiblioCommons('multcolib', login, password)

WcclsAsync = lambda login, password: BiblioCommonsAsync('wccls', login, password)
MultCoLibAsync = lambda login, password: BiblioCommonsAsync('multcolib', login, password)
