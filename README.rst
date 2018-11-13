Overview
========
This is a scraper for the WCCLS account page.

Usage
=====

.. image:: https://travis-ci.org/rkhwaja/wccls.svg?branch=master
   :target: https://travis-ci.org/rkhwaja/wccls

.. code-block:: python

  wccls = Wccls(login=cardNumber, password=password)
  for item in wccls.items:
      print(item)
