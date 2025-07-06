"""
Expose some bits of jq for typing
"""

# Type usage only
from jq import _NO_VALUE  # pyright:ignore [reportPrivateUsage]
from jq import _Program  # pyright:ignore [reportPrivateUsage]
from jq import _ProgramWithInput  # pyright:ignore [reportPrivateUsage]
from jq import _ResultIterator  # pyright:ignore [reportPrivateUsage]
from jq import compile


__all__ = [
    "compile",
    "Program",
    "ProgramWithInput",
    "ResultIterator",
    "NO_VALUE",
]


NO_VALUE = _NO_VALUE

type Program = _Program
type ProgramWithInput = _ProgramWithInput
type ResultIterator = _ResultIterator
