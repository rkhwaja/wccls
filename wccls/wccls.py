from enum import Enum

__all__ = ["ParseError", "StatusType", "Item", "CheckedOutItem", "SuspendedHold", "HeldItem", "ShippedItem", "ActiveHold", "CancelledHold", "PendingItem", "UnclaimedHold"]

class ParseError(Exception):
	pass

# status types
StatusType = Enum("StatusType", "Held, Pending, Shipped, Active, Inactive, Cancelled, CheckedOut, Unclaimed")

class Item:
	def __init__(self, title, status):
		self.title = title
		self.status = status

	def __repr__(self):
		return f"<Item title={self.title}, status={self.status.name}>"

class CheckedOutItem(Item):
	def __init__(self, title, dueDate, renewals, isOverdrive):
		super().__init__(title, StatusType.CheckedOut)
		self.dueDate = dueDate
		self.renewals = renewals
		self.isOverdrive = isOverdrive

	@property
	def renewable(self):
		return not self.isOverdrive and self.renewals > 0

	def __repr__(self):
		return f"<CheckedOutItem {super().__repr__()}, dueDate={self.dueDate}, renewals={self.renewals}, isOverdrive={self.isOverdrive}>"

# The same as a paused hold
class SuspendedHold(Item):
	def __init__(self, title, reactivationDate):
		super().__init__(title, StatusType.Inactive)
		self.reactivationDate = reactivationDate

	def __repr__(self):
		return f"<SuspendedHold {super().__repr__()}, reactivationDate={self.reactivationDate}>"

# Being held at the library
class HeldItem(Item):
	def __init__(self, title, expiryDate):
		super().__init__(title, StatusType.Held)
		self.expiryDate = expiryDate

	def __repr__(self):
		return f"<HeldItem {super().__repr__()}, expiryDate={self.expiryDate}>"

# Shipping to the library
class ShippedItem(Item):
	def __init__(self, title, shippedDate):
		super().__init__(title, StatusType.Shipped)
		self.shippedDate = shippedDate

	def __repr__(self):
		return f"<ShippedItem {super().__repr__()}, shippedDate={self.shippedDate}>"

# In the queue
class ActiveHold(Item):
	def __init__(self, title, activationDate, queuePosition, queueSize, copies):
		super().__init__(title, StatusType.Active)
		self.activationDate = activationDate
		self.queuePosition = queuePosition
		self.queueSize = queueSize
		self.copies = copies

	def __repr__(self):
		return f"<ActiveHold {super().__repr__()}, activationDate={self.activationDate}, queuePosition={self.queuePosition}, queueSize={self.queueSize}, copies={self.copies}>"

# Cancelled - not sure if this shows up anymore
class CancelledHold(Item):
	def __init__(self, title, cancellationDate):
		super().__init__(title, StatusType.Cancelled)
		self.cancellationDate = cancellationDate

	def __repr__(self):
		return f"<CancelledHold {super().__repr__()}, cancellationDate={self.cancellationDate}>"

# This is the state after it's been requested but before it's an ActiveHold
class PendingItem(Item):
	def __init__(self, title, reservationDate):
		super().__init__(title, StatusType.Pending)
		self.reservationDate = reservationDate

	def __repr__(self):
		return f"<PendingItem {super().__repr__()}, reservationDate={self.reservationDate}>"

# The hold expired - not sure if this shows up anymore
class UnclaimedHold(Item):
	def __init__(self, title):
		super().__init__(title, StatusType.Unclaimed)
