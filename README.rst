Overview
========
Scraper for the WCCLS account page

Usage
=====

.. code:: python

 wccls = Wccls(login=cardNumber, password=password)
 for item in wccls.items:
     print(item)
