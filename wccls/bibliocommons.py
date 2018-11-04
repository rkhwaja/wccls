from pprint import pprint

from requests_html import HTMLSession

__all__ = ["WcclsBiblioCommons"]

class WcclsBiblioCommons:
	def __init__(self, username, password, debug_=False):
		self.session = HTMLSession()
		loginPage = self.session.get("https://wccls.bibliocommons.com/user/login?destination=%2F")
		loginForm = loginPage.html.find(".loginForm")[0]
		print(loginForm.html)
		inputs = loginForm.find("input")
		pprint(inputs)
		formData = {}
		for input_ in inputs:
			formData[input_.attrs["name"]] == input_.attrs["value"]
		formData["user_pin"] = password
		formData["name"] = username
		loggedInPage = self.session.post(loginForm.attrs["action"], data=formData)
		print(loggedInPage)

from os import environ
x = WcclsBiblioCommons(environ["WCCLS_CARD_NUMBER"], environ["WCCLS_PASSWORD"])
