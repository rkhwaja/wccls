from logging import getLogger, NullHandler

from .item_types import *
from .bibliocommons import *

getLogger(__name__).addHandler(NullHandler())
