# Overview

This is a read-only scraper for the [WCCLS](https://wccls.bibliocommons.com) account page. It also works for the [Multnomah County Bibliocommons site](https://multcolib.bibliocommons.com)

# Usage

![image](https://github.com/rkhwaja/wccls/workflows/ci/badge.svg) [![codecov](https://codecov.io/gh/rkhwaja/wccls/branch/master/graph/badge.svg)](https://codecov.io/gh/rkhwaja/wccls)

``` python
from wccls import Wccls, WcclsAsync
items = Wccls(login=card_number_or_username, password=password)
for item in items:
    print(item)

items = await WcclsAsync(login=card_number_or_username, password=password)
for item in items:
    print(item)
```

# Running tests

## Run against the live website

- Set the environment variables to show what the expected counts are for the various categories

- Run
```bash
pytest
```

## To record new test data
Set SCRUB_EMAIL, WCCLS_CARD_NUMBER, WCCLS_PASSWORD environment variables
``` python
pytest --collect=save
```

## To test existing test data
``` python
pytest
```
