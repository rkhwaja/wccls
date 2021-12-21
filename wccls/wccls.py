from dataclasses import dataclass
from datetime import date
from enum import Enum

class ParseError(Exception):
	pass

StatusType = Enum('StatusType', [])

def _AddStatusType(name):
	global StatusType # pylint: disable=global-statement
	names = [x.name for x in StatusType]
	names.append(name)
	StatusType = Enum('StatusType', names)

FormatType = Enum('Format', ['DownloadableAudiobook', 'eBook', 'Book', 'DVD', 'BluRay', 'GraphicNovel'])

@dataclass
class Item:
	title: str
	isDigital: bool
	format: str

	@property
	def status(self) -> StatusType:
		return StatusType[self.__class__.__name__]

	@classmethod
	def __init_subclass__(cls, *args, **kwargs): # pylint: disable=unused-argument
		_AddStatusType(cls.__name__)

@dataclass
class Checkout(Item):
	dueDate: date
	renewals: int

	@property
	def renewable(self):
		return not self.isDigital and self.renewals > 0

@dataclass
class HoldPaused(Item):
	reactivationDate: date

@dataclass
class HoldReady(Item):
	"""Being held at the library"""
	expiryDate: date

@dataclass
class HoldInTransit(Item):
	"""Shipping to the library"""
	shippedDate: date

@dataclass
class HoldNotReady(Item):
	"""In the queue"""
	activationDate: date
	queuePosition: int
	queueSize: int
	copies: int
