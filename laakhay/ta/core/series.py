"""High-performance Series data structure for time series data."""

from __future__ import annotations

import decimal
from dataclasses import dataclass
from typing import Generic, TypeVar, Iterator, overload, TypeAlias, Any, Union

from .types import Timestamp, Symbol, Price, Qty

T = TypeVar('T')

@dataclass(slots=True, frozen=True)
class Series(Generic[T]):
    """Immutable time series with generic value type."""
    timestamps: tuple[Timestamp, ...]  # Sorted timestamps
    values: tuple[T, ...]              # Corresponding values
    symbol: Symbol                     # Trading symbol
    timeframe: str                     # Timeframe (e.g., '1h', '4h')

    def __post_init__(self) -> None:
        """Validate series data integrity after initialization."""
        if len(self.timestamps) != len(self.values):
            raise ValueError("Timestamps and values must have the same length")

        if len(self.timestamps) > 1:
            if any(later < earlier for earlier, later in zip(self.timestamps, self.timestamps[1:], strict=False)):
                raise ValueError("Timestamps must be sorted")

    @property
    def length(self) -> int:
        """Number of data points in the series."""
        return len(self.timestamps)

    @property
    def is_empty(self) -> bool:
        """Whether the series is empty."""
        return self.length == 0

    def __len__(self) -> int:
        return self.length

    def __getitem__(self, index: Union[int, slice]) -> Union[tuple[Timestamp, T], Series[T]]:
        """Access single data point or slice the series."""
        try:
            if isinstance(index, int):
                return self.timestamps[index], self.values[index]
            else:
                # Handle slice case
                return Series[T](
                    timestamps=self.timestamps[index],
                    values=self.values[index],
                    symbol=self.symbol,
                    timeframe=self.timeframe
                )
        except (TypeError, KeyError) as e:
            if "indices must be integers or slices" in str(e):
                raise TypeError("Series indices must be integers or slices") from e
            raise

    def __iter__(self) -> Iterator[tuple[Timestamp, T]]:
        """Iterate over (timestamp, value) pairs."""
        return zip(self.timestamps, self.values)

    @overload
    def __add__(self, other: Series[T]) -> Series[T]: ...
    @overload
    def __add__(self, other: T) -> Series[T]: ...

    def __add__(self, other: Series[T] | T) -> Series[T]:
        """Concatenate series or add a scalar to all values."""
        if isinstance(other, Series):
            if self.symbol != other.symbol or self.timeframe != other.timeframe:
                raise ValueError("Cannot add series with different symbols or timeframes")
            
            # Check if series have same length and timestamps for element-wise operations
            if len(self) == len(other):
                # Check if timestamps are the same (for element-wise operations)
                if self.timestamps == other.timestamps:
                    try:
                        new_values_list = []
                        for v1, v2 in zip(self.values, other.values):
                            new_values_list.append(v1 + v2)  # type: ignore
                        new_values = tuple(new_values_list)  # type: ignore[misc]
                        return Series[T](
                            timestamps=self.timestamps,
                            values=new_values,  # type: ignore[arg-type]
                            symbol=self.symbol,
                            timeframe=self.timeframe
                        )
                    except TypeError:
                        # Fall through to concatenation if element-wise fails
                        pass
            
            # Concatenate and sort by timestamp
            combined_timestamps = self.timestamps + other.timestamps
            combined_values = self.values + other.values  # type: ignore[misc]
            
            # Sort by timestamp while maintaining value correspondence
            sorted_pairs = sorted(zip(combined_timestamps, combined_values))
            sorted_timestamps = tuple(pair[0] for pair in sorted_pairs)
            sorted_values = tuple(pair[1] for pair in sorted_pairs)
            
            return Series[T](
                timestamps=sorted_timestamps,
                values=sorted_values,
                symbol=self.symbol,
                timeframe=self.timeframe
            )
        else:
            # Scalar addition (requires T to support addition)
            try:
                # Use a more explicit approach to avoid type checker issues
                new_values_list = []
                for v in self.values:
                    new_values_list.append(v + other)  # type: ignore
                new_values = tuple(new_values_list)  # type: ignore[misc]
            except TypeError:
                raise TypeError(f"Cannot add {type(other)} to series values of type {type(self.values[0]) if self.values else 'unknown'}")
            return Series[T](
                timestamps=self.timestamps,
                values=new_values,  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe
            )
    
    def __sub__(self, other: Series[T] | T) -> Series[T]:
        """Subtract scalar or element-wise subtract series."""
        if isinstance(other, Series):
            # Element-wise series subtraction (requires both series to have same length and timestamps)
            if len(self) != len(other):
                raise ValueError(f"Cannot subtract series of different lengths: {len(self)} vs {len(other)}")
            
            try:
                new_values_list = []
                for v1, v2 in zip(self.values, other.values):
                    new_values_list.append(v1 - v2)  # type: ignore
                new_values = tuple(new_values_list)  # type: ignore[misc]
            except TypeError:
                raise TypeError(f"Cannot subtract series values of types {type(self.values[0])} and {type(other.values[0])}")
            
            return Series[T](
                timestamps=self.timestamps,
                values=new_values,  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe
            )
        else:
            # Scalar subtraction
            try:
                new_values_list = []
                for v in self.values:
                    new_values_list.append(v - other)  # type: ignore
                new_values = tuple(new_values_list)  # type: ignore[misc]
            except TypeError:
                raise TypeError(f"Cannot subtract {type(other)} from series values of type {type(self.values[0]) if self.values else 'unknown'}")
            return Series[T](
                timestamps=self.timestamps,
                values=new_values,  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe
            )
    
    def __mul__(self, other: Series[T] | T) -> Series[T]:
        """Multiply series by scalar or element-wise multiply by series."""
        if isinstance(other, Series):
            # Element-wise series multiplication
            if len(self) != len(other):
                raise ValueError(f"Cannot multiply series of different lengths: {len(self)} vs {len(other)}")
            
            try:
                new_values_list = []
                for v1, v2 in zip(self.values, other.values):
                    new_values_list.append(v1 * v2)  # type: ignore
                new_values = tuple(new_values_list)  # type: ignore[misc]
            except TypeError:
                raise TypeError(f"Cannot multiply series values of types {type(self.values[0])} and {type(other.values[0])}")
            
            return Series[T](
                timestamps=self.timestamps,
                values=new_values,  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe
            )
        else:
            # Scalar multiplication
            try:
                new_values_list = []
                for v in self.values:
                    new_values_list.append(v * other)  # type: ignore
                new_values = tuple(new_values_list)  # type: ignore[misc]
            except TypeError:
                raise TypeError(f"Cannot multiply series values of type {type(self.values[0]) if self.values else 'unknown'} by {type(other)}")
            return Series[T](
                timestamps=self.timestamps,
                values=new_values,  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe
            )
    
    def __truediv__(self, other: Series[T] | T) -> Series[T]:
        """Divide series by scalar or element-wise divide by series."""
        if isinstance(other, Series):
            # Element-wise series division
            if len(self) != len(other):
                raise ValueError(f"Cannot divide series of different lengths: {len(self)} vs {len(other)}")
            
            try:
                new_values_list = []
                for v1, v2 in zip(self.values, other.values):
                    new_values_list.append(v1 / v2)  # type: ignore
                new_values = tuple(new_values_list)  # type: ignore[misc]
            except TypeError:
                raise TypeError(f"Cannot divide series values of types {type(self.values[0])} and {type(other.values[0])}")
            except ZeroDivisionError:
                raise ValueError("Cannot divide by zero in series")
            
            return Series[T](
                timestamps=self.timestamps,
                values=new_values,  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe
            )
        else:
            # Scalar division
            try:
                new_values_list = []
                for v in self.values:
                    new_values_list.append(v / other)  # type: ignore
                new_values = tuple(new_values_list)  # type: ignore[misc]
            except TypeError:
                raise TypeError(f"Cannot divide series values of type {type(self.values[0]) if self.values else 'unknown'} by {type(other)}")
            except ZeroDivisionError:
                raise ValueError("Cannot divide by zero")
            return Series[T](
                timestamps=self.timestamps,
                values=new_values,  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe
            )
    
    def __neg__(self) -> Series[T]:
        """Unary negation of series."""
        try:
            new_values_list = []
            for v in self.values:
                new_values_list.append(-v)  # type: ignore
            new_values = tuple(new_values_list)  # type: ignore[misc]
        except TypeError:
            raise TypeError(f"Cannot negate series values of type {type(self.values[0]) if self.values else 'unknown'}")
        return Series[T](
            timestamps=self.timestamps,
            values=new_values,  # type: ignore[arg-type]
            symbol=self.symbol,
            timeframe=self.timeframe
        )
    
    def __pos__(self) -> Series[T]:
        """Unary plus of series (returns copy)."""
        return Series[T](
            timestamps=self.timestamps,
            values=self.values,
            symbol=self.symbol,
            timeframe=self.timeframe
        )
    
    def __mod__(self, other: Series[T] | T) -> Series[T]:
        """Modulo series by scalar or element-wise modulo by series."""
        if isinstance(other, Series):
            # Element-wise series modulo
            if len(self) != len(other):
                raise ValueError(f"Cannot perform modulo on series of different lengths: {len(self)} vs {len(other)}")
            
            try:
                new_values_list = []
                for v1, v2 in zip(self.values, other.values):
                    new_values_list.append(v1 % v2)  # type: ignore
                new_values = tuple(new_values_list)  # type: ignore[misc]
            except TypeError:
                raise TypeError(f"Cannot perform modulo on series values of types {type(self.values[0])} and {type(other.values[0])}")
            except (ZeroDivisionError, decimal.InvalidOperation):
                raise ZeroDivisionError("Cannot perform modulo with zero in series")
            
            return Series[T](
                timestamps=self.timestamps,
                values=new_values,  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe
            )
        else:
            # Scalar modulo
            try:
                new_values_list = []
                for v in self.values:
                    new_values_list.append(v % other)  # type: ignore
                new_values = tuple(new_values_list)  # type: ignore[misc]
            except TypeError:
                raise TypeError(f"Cannot perform modulo on series values of type {type(self.values[0]) if self.values else 'unknown'} with {type(other)}")
            except (ZeroDivisionError, decimal.InvalidOperation):
                raise ZeroDivisionError("Cannot perform modulo with zero in series")
            return Series[T](
                timestamps=self.timestamps,
                values=new_values,  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe
            )
    
    def __pow__(self, other: Series[T] | T) -> Series[T]:
        """Power series by scalar or element-wise power by series."""
        if isinstance(other, Series):
            # Element-wise series power
            if len(self) != len(other):
                raise ValueError(f"Cannot perform power on series of different lengths: {len(self)} vs {len(other)}")
            
            try:
                new_values_list = []
                for v1, v2 in zip(self.values, other.values):
                    new_values_list.append(v1 ** v2)  # type: ignore
                new_values = tuple(new_values_list)  # type: ignore[misc]
            except TypeError:
                raise TypeError(f"Cannot perform power on series values of types {type(self.values[0])} and {type(other.values[0])}")
            
            return Series[T](
                timestamps=self.timestamps,
                values=new_values,  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe
            )
        else:
            # Scalar power
            try:
                new_values_list = []
                for v in self.values:
                    new_values_list.append(v ** other)  # type: ignore
                new_values = tuple(new_values_list)  # type: ignore[misc]
            except TypeError:
                raise TypeError(f"Cannot perform power on series values of type {type(self.values[0]) if self.values else 'unknown'} with {type(other)}")
            return Series[T](
                timestamps=self.timestamps,
                values=new_values,  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe
            )

    def slice_by_time(self, start: Timestamp, end: Timestamp) -> Series[T]:
        """Slice series by time range using binary search for efficiency."""
        if start > end:
            raise ValueError("Start time must be <= end time")
        
        # Binary search for start index
        left, right = 0, len(self.timestamps)
        while left < right:
            mid = (left + right) // 2
            if self.timestamps[mid] < start:
                left = mid + 1
            else:
                right = mid
        start_idx = left
        
        # Binary search for end index
        left, right = start_idx, len(self.timestamps)
        while left < right:
            mid = (left + right) // 2
            if self.timestamps[mid] <= end:
                left = mid + 1
            else:
                right = mid
        end_idx = left
        
        return Series[T](
            timestamps=self.timestamps[start_idx:end_idx],
            values=self.values[start_idx:end_idx],
            symbol=self.symbol,
            timeframe=self.timeframe
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert series to dictionary format."""
        return {
            'timestamps': [ts.isoformat() for ts in self.timestamps],
            'values': list(self.values),
            'symbol': self.symbol,
            'timeframe': self.timeframe,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Series[T]:
        """Create series from dictionary format."""
        from .timestamps import coerce_timestamp
        
        timestamps = tuple(coerce_timestamp(ts) for ts in data['timestamps'])
        values = tuple(data['values'])
        
        return cls(
            timestamps=timestamps,
            values=values,
            symbol=data['symbol'],
            timeframe=data['timeframe'],
        )

# Type aliases for common series types
PriceSeries: TypeAlias = Series[Price]
QtySeries: TypeAlias = Series[Qty]
