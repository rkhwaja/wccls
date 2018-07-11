Overview
========
Scraper for the WCCLS account page

Usage
=====

.. image:: https://travis-ci.org/rkhwaja/wccls.svg?branch=master

.. code-block:: python

  wccls = Wccls(login=cardNumber, password=password)
  for item in wccls.items:
      print(item)
