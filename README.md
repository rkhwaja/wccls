# Overview

This is a read-only scraper for the [WCCLS](https://wccls.bibliocommons.com) account page. It also works for the [Multnomah County Bibliocommons site](https://multcolib.bibliocommons.com)

# Usage

![image](https://github.com/rkhwaja/wccls/workflows/ci/badge.svg) [![codecov](https://codecov.io/gh/rkhwaja/wccls/branch/master/graph/badge.svg)](https://codecov.io/gh/rkhwaja/wccls)

``` python
wccls = WcclsBiblioCommons(login=card_number_or_username, password=password)
for item in wccls.items:
    print(item)
```

# Running tests

## Run against the live website

- Set the environment variables to show what the expected counts are for the various categories

- Run
```bash
pytest
```

## To record new cassettes
``` python
pytest --vcr-record=all
```

## To replay existing cassettes
``` python
pytest --vcr-record=none
```
