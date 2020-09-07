# Overview

This is a scraper for the WCCLS account page.

# Usage

![image](https://github.com/rkhwaja/wccls/workflows/ci/badge.svg) [![codecov](https://codecov.io/gh/rkhwaja/wccls/branch/master/graph/badge.svg)](https://codecov.io/gh/rkhwaja/wccls)

``` python
wccls = Wccls(login=cardNumber, password=password)
for item in wccls.items:
    print(item)
```
