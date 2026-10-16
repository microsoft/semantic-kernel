# Copyright (c) Microsoft. All rights reserved.

import re
from typing import Any


class MemoryGuardResult:
    """Result of a memory guard scanning operation."""

    def __init__(
        self,
        is_safe: bool,
        threat_type: str | None = None,
        matched_pattern: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a new instance of MemoryGuardResult.

        Args:
            is_safe (bool): Whether the scanned memory content is safe.
            threat_type (str | None): Threat classification if unsafe.
            matched_pattern (str | None): Pattern or signature that triggered the block.
            details (dict[str, Any] | None): Additional telemetry and context.
        """
        self.is_safe = is_safe
        self.threat_type = threat_type
        self.matched_pattern = matched_pattern
        self.details = details or {}

    def __repr__(self) -> str:
        return f"MemoryGuardResult(is_safe={self.is_safe}, threat_type={self.threat_type!r})"


class MemoryPoisoningError(Exception):
    """Exception raised when memory data fails security inspection (OWASP ASI06 / LLM04)."""

    pass


class MemoryGuardBase:
    """Abstract base class for memory protection guards against poisoning attacks (OWASP ASI06)."""

    def scan_write(
        self,
        text: str,
        collection: str | None = None,
        id: str | None = None,
    ) -> MemoryGuardResult:
        """Scan text prior to saving into memory storage.

        Args:
            text (str): The raw text to inspect.
            collection (str | None): Target memory collection.
            id (str | None): Identifier of the memory record.

        Returns:
            MemoryGuardResult: Security scan assessment.
        """
        raise NotImplementedError

    def scan_read(
        self,
        text: str,
        collection: str | None = None,
        id: str | None = None,
    ) -> MemoryGuardResult:
        """Scan text after retrieval from memory storage before feeding to agent.

        Args:
            text (str): The retrieved text.
            collection (str | None): Source collection.
            id (str | None): Record ID.

        Returns:
            MemoryGuardResult: Security scan assessment.
        """
        return MemoryGuardResult(is_safe=True)


class DefaultMemoryGuard(MemoryGuardBase):
    """Reference implementation of OWASP Agent Memory Guard for Semantic Kernel.

    Defends vector memory stores against:
      - Direct & indirect prompt injections
      - System instruction overriding patterns (e.g. 'Ignore previous instructions')
      - Delimiter hijacking and developer mode exploits
    """

    DEFAULT_POISONING_PATTERNS = [
        r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions?|directions?|prompts?)",
        r"disregard\s+(?:all\s+)?(?:previous|prior)\s+(?:instructions?|guidelines?)",
        r"new\s+(?:instruction|directive|system\s+prompt)\s*:",
        r"(?:^|
)\s*(?:system|developer|admin)\s*:\s*",
        r"\[(?:system|admin|override|inst)\]",
        r"bypass\s+(?:guardrails?|safety|filters?|rules?)",
        r"you\s+are\s+now\s+(?:unrestricted|in\s+developer\s+mode|dan)",
    ]

    def __init__(self, custom_patterns: list[str] | None = None) -> None:
        """Initialize DefaultMemoryGuard with regex patterns.

        Args:
            custom_patterns (list[str] | None): Optional additional regex rules.
        """
        patterns = self.DEFAULT_POISONING_PATTERNS + (custom_patterns or [])
        self._compiled_patterns = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in patterns]

    def scan_write(
        self,
        text: str,
        collection: str | None = None,
        id: str | None = None,
    ) -> MemoryGuardResult:
        """Scan memory writes for injection signatures."""
        if not text:
            return MemoryGuardResult(is_safe=True)

        for pat in self._compiled_patterns:
            match = pat.search(text)
            if match:
                return MemoryGuardResult(
                    is_safe=False,
                    threat_type="PROMPT_INJECTION_OR_OVERRIDE",
                    matched_pattern=match.group(0),
                    details={"collection": collection, "id": id, "match_span": match.span()},
                )

        return MemoryGuardResult(is_safe=True)

    def scan_read(
        self,
        text: str,
        collection: str | None = None,
        id: str | None = None,
    ) -> MemoryGuardResult:
        """Scan memory reads before passing to LLM prompts."""
        return self.scan_write(text=text, collection=collection, id=id)
