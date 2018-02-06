from .wccls import ActiveHold, CancelledHold, CheckedOutItem, HeldItem, Item, PendingItem, ShippedItem, StatusType, SuspendedHold
from .wccls_desktop import WcclsDesktop
from .wccls_mobile import WcclsMobile

# mobile works at the moment
Wccls = WcclsMobile
