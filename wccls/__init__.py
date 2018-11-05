from .wccls import * # pylint: disable=wildcard-import
from .wccls_mobile import * # pylint: disable=wildcard-import
from .bibliocommons import * # pylint: disable=wildcard-import

# mobile works at the moment
Wccls = WcclsMobile

__all__ = wccls.__all__ + wccls_mobile.__all__ + bibliocommons.__all__ # pylint: disable=undefined-variable
