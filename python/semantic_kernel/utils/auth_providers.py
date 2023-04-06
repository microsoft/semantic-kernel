# Copyright (c) Microsoft. All rights reserved.

from typing import Optional, Tuple


# Define __sk_auth_providers if it doesn't exist
try:
    # pyright: reportUndefinedVariable=false
    __sk_auth_providers
except NameError:
    __sk_auth_providers = {}


def try_get_auth_from_named_provider(
    name: str,
) -> Tuple[Optional[str], Optional[str], bool]:
    assert __sk_auth_providers is not None
    assert isinstance(__sk_auth_providers, dict)

    if name in __sk_auth_providers:
        return __sk_auth_providers[name]()

    raise ValueError(
        f"Auth provider '{name}' not found. "
        f"Registered providers: {', '.join(__sk_auth_providers.keys())}"
    )
