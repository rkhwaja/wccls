Overview
========
This is a scraper for the WCCLS account page. It currently seems to work for the Multnomah County library site too and probably other Bibliocommons sites.

Usage
=====

.. image:: https://travis-ci.org/rkhwaja/wccls.svg?branch=master
   :target: https://travis-ci.org/rkhwaja/wccls

.. code-block:: python

  wccls = Wccls(login=cardNumber, password=password)
  for item in wccls.items:
      print(item)
