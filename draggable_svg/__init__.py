from .board import (
    __version__,  # It is defined inside a module, and imported here.
                  # The other way around would introduce cyclic reference.
    Board,
    get_differential,
    )

