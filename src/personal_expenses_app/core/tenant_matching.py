"""Choose which words of a tenant's name identify their payments in bank descriptions."""

from __future__ import annotations

import re
from typing import Iterable, Optional


def tenant_tokens(tenant: Optional[str]) -> list[str]:
    """Lowercased name tokens of a tenant string.

    The string is split on whitespace and '&'; tokens shorter than 2 characters are
    dropped and duplicates removed (order kept).
    """
    if not tenant:
        return []
    tokens = [t.lower() for t in re.split(r"[\s&]+", tenant.strip()) if len(t) >= 2]
    return list(dict.fromkeys(tokens))


def tenant_match_tokens(tenant: Optional[str], other_tenants: Iterable[Optional[str]]) -> tuple[list[str], bool]:
    """Return ``(tokens, require_all)`` for linking expenses to this tenant's property.

    A token that also appears in another property's tenant name (e.g. a first name
    shared by two tenants) cannot tell the properties apart, so it is not used. Any one
    of the remaining, distinctive tokens is enough to match: for
    "Jose Tellez & Veronica Flores" next to another tenant "Jose Soto", payments from
    "Veronica Flores" or "Jose Tellez" match, but one from just "Jose" does not.

    If every token is shared with another tenant, all of them must appear in the
    description (``require_all=True``).
    """
    tokens = tenant_tokens(tenant)
    shared = {t for other in other_tenants for t in tenant_tokens(other)}
    distinctive = [t for t in tokens if t not in shared]
    if distinctive:
        return distinctive, False
    return tokens, True
