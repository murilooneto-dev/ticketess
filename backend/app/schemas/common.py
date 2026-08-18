from typing import Annotated

from pydantic import StringConstraints

EmailField = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        max_length=255,
    ),
]

UsernameField = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        # o pattern roda antes da normalização para minúsculas, então precisa
        # aceitar maiúsculas também — o valor final já sai em minúsculo.
        pattern=r"^[a-zA-Z0-9._-]{3,80}$",
    ),
]
