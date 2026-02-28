"""Primitive type aliases for laakhay-ta."""

from datetime import date, datetime
from decimal import Decimal
from typing import TypeAlias

Symbol: TypeAlias = str
Price: TypeAlias = Decimal
Qty: TypeAlias = Decimal
Volume: TypeAlias = Decimal
Rate: TypeAlias = Decimal
Timestamp: TypeAlias = datetime

PriceLike: TypeAlias = Decimal | float | int | str
QtyLike: TypeAlias = Decimal | float | int | str
RateLike: TypeAlias = Decimal | float | int | str
TimestampLike: TypeAlias = datetime | date | str | int
