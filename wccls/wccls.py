from enum import Enum

class ParseError(Exception):
	pass

StatusType = Enum('StatusType', [])

def _AddStatusType(name):
	global StatusType # pylint: disable=global-statement
	names = [x.name for x in StatusType]
	names.append(name)
	StatusType = Enum('StatusType', names)

class Item:
	def __init__(self, title, isDigital):
		self.title = title
		global StatusType # pylint: disable=global-statement
		self.status = StatusType[self.__class__.__name__]
		self.isDigital = isDigital

	def __repr__(self):
		return f'<Item title={self.title}, isDigital={self.isDigital}>'

	@classmethod
	def __init_subclass__(cls, *args, **kwargs): # pylint: disable=unused-argument
		_AddStatusType(cls.__name__)

class Checkout(Item):
	def __init__(self, title, dueDate, renewals, isDigital):
		super().__init__(title, isDigital)
		self.dueDate = dueDate
		self._renewals = renewals

	@property
	def renewable(self):
		return not self.isDigital and self._renewals > 0

	def __repr__(self):
		return f'<Checkout {super().__repr__()}, dueDate={self.dueDate}, renewals={self._renewals}>'

class HoldPaused(Item):
	def __init__(self, title, reactivationDate, isDigital):
		super().__init__(title, isDigital)
		self.reactivationDate = reactivationDate

	def __repr__(self):
		return f'<HoldPaused {super().__repr__()}, reactivationDate={self.reactivationDate}>'

# Being held at the library
class HoldReady(Item):
	def __init__(self, title, expiryDate, isDigital):
		super().__init__(title, isDigital)
		self.expiryDate = expiryDate

	def __repr__(self):
		return f'<HoldReady {super().__repr__()}, expiryDate={self.expiryDate}>'

# Shipping to the library
class HoldInTransit(Item):
	def __init__(self, title, shippedDate):
		super().__init__(title, False)
		self.shippedDate = shippedDate

	def __repr__(self):
		return f'<HoldInTransit {super().__repr__()}, shippedDate={self.shippedDate}>'

# In the queue
class HoldNotReady(Item):
	def __init__(self, title, activationDate, queuePosition, queueSize, copies, isDigital):
		super().__init__(title, isDigital)
		self.activationDate = activationDate
		self.queuePosition = queuePosition
		self.queueSize = queueSize
		self.copies = copies

	def __repr__(self):
		return f'<HoldNotReady {super().__repr__()}, activationDate={self.activationDate}, queuePosition={self.queuePosition}, queueSize={self.queueSize}, copies={self.copies}>'
