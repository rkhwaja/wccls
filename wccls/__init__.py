from .wccls import * # pylint: disable=wildcard-import
from .bibliocommons import * # pylint: disable=wildcard-import

Wccls = WcclsBiblioCommons

__all__ = wccls.__all__ + bibliocommons.__all__ # pylint: disable=undefined-variable
