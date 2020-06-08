Overview
========
This is a scraper for the WCCLS account page.

Usage
=====

.. image:: https://github.com/rkhwaja/wccls/workflows/ci/badge.svg

.. code-block:: python

  wccls = Wccls(login=cardNumber, password=password)
  for item in wccls.items:
      print(item)
