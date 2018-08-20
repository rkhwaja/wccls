#!/usr/bin/env python3

from setuptools import find_packages, setup

with open("README.rst") as f:
	long_description = f.read()

setup(name="wccls",
	version="1.0",
	description="WCCLS scraper",
	long_description=long_description,
	author="Rehan Khwaja",
	author_email="rehan@khwaja.name",
	url="https://github.com/rkhwaja/wccls",
	packages=find_packages(),
	install_requires=["beautifulsoup4", "requests"],
	classifiers=[
		"Development Status :: 5 - Production/Stable",
		"Intended Audience :: Developers",
		"Programming Language :: Python :: 3.6",
		"Programming Language :: Python :: 3.7"
	],
	keywords="",
)
