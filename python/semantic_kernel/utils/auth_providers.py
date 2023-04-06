# Copyright (c) Microsoft. All rights reserved.

from typing import Optional, Tuple


def try_get_auth_from_named_provider(
    name: Optional[str],
) -> Tuple[Optional[str], Optional[str], bool]:
    try:
        import __sk_auth_providers  # type: ignore

        providers = getattr(__sk_auth_providers, "providers", {})
        if not name:
            # Use the first available provider
            name = next(iter(providers.keys()), None)
            if not name:
                raise ValueError("No auth providers registered")

        if name not in __sk_auth_providers.providers:
            raise ValueError(
                f"Failed to load auth provider '{name}'. "
                f"Registered providers: {', '.join(providers.keys())}"
            )

        return __sk_auth_providers.providers[name]()
    except ImportError:
        raise ValueError("Auth providers module not found (__sk_auth_providers)")
