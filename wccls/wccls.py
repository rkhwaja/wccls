from enum import Enum

# status types
StatusType = Enum("StatusType", "Held, Pending, Shipped, Active, Inactive, Cancelled, CheckedOut, Unclaimed")

class Item:
	def __init__(self, title, status):
		self.title = title
		self.status = status

	def __repr__(self):
		return "<Item title={}, status={}>".format(self.title, self.status.name)

class CheckedOutItem(Item):
	def __init__(self, title, dueDate, renewals):
		super().__init__(title, StatusType.CheckedOut)
		self.dueDate = dueDate
		self.renewals = renewals

	def __repr__(self):
		return "<CheckedOutItem {}, dueDate={}>".format(super().__repr__(), self.dueDate)

class SuspendedHold(Item):
	def __init__(self, title, reactivationDate):
		super().__init__(title, StatusType.Inactive)
		self.reactivationDate = reactivationDate

	def __repr__(self):
		return "<SuspendedHold {}, reactivationDate={}>".format(super().__repr__(), self.reactivationDate)

class HeldItem(Item):
	def __init__(self, title, expiryDate):
		super().__init__(title, StatusType.Held)
		self.expiryDate = expiryDate

	def __repr__(self):
		return "<HeldItem {}, expiryDate={}>".format(super().__repr__(), self.expiryDate)

class ShippedItem(Item):
	def __init__(self, title, shippedDate):
		super().__init__(title, StatusType.Shipped)
		self.shippedDate = shippedDate

	def __repr__(self):
		return "<ShippedItem {}, shippedDate={}>".format(super().__repr__(), self.shippedDate)

class ActiveHold(Item):
	def __init__(self, title, activationDate, queuePosition, queueSize):
		super().__init__(title, StatusType.Active)
		self.activationDate = activationDate
		self.queuePosition = queuePosition
		self.queueSize = queueSize

	def __repr__(self):
		return "<ActiveHold {}, activationDate={}, queuePosition={}, queueSize={}>".format(super().__repr__(), self.activationDate, self.queuePosition, self.queueSize)

class CancelledHold(Item):
	def __init__(self, title, cancellationDate):
		super().__init__(title, StatusType.Cancelled)
		self.cancellationDate = cancellationDate

	def __repr__(self):
		return "<CancelledHold {}, cancellationDate={}>".format(super().__repr__(), self.cancellationDate)

class PendingItem(Item):
	def __init__(self, title, reservationDate):
		super().__init__(title, StatusType.Pending)
		self.reservationDate = reservationDate

	def __repr__(self):
		return "<PendingItem {}, reservationDate={}>".format(super().__repr__(), self.reservationDate)
