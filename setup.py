#!/usr/bin/env python3

from setuptools import find_packages, setup

with open("README.rst") as f:
	long_description = f.read()

setup(name="wccls",
	version="0.4",
	description="WCCLS scraper",
	long_description=long_description,
	author="Rehan Khwaja",
	author_email="rehan@khwaja.name",
	url="https://github.com/rkhwaja/wccls",
	packages=find_packages(),
	install_requires=["BeautifulSoup4", "requests"],
	classifiers=[
		"Development Status :: 5 - Production/Stable",
		"Intended Audience :: Developers",
		"Programming Language :: Python :: 3.6"
	],
	keywords="",
)
