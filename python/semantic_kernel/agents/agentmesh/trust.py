"""Trust verification for AgentMesh."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from semantic_kernel.agents.agentmesh.identity import CMVKIdentity, CMVKSignature


@dataclass
class TrustPolicy:
    """Trust verification policy."""

    require_verification: bool = True
    min_trust_score: float = 0.7
    allowed_capabilities: Optional[List[str]] = None
    block_unverified: bool = True
    cache_ttl_seconds: int = 900


@dataclass
class TrustVerificationResult:
    """Result of trust verification."""

    trusted: bool
    trust_score: float
    reason: str
    verified_capabilities: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class TrustedAgentCard:
    """Agent card for discovery and verification."""

    name: str
    description: str
    capabilities: List[str]
    identity: Optional[CMVKIdentity] = None
    trust_score: float = 1.0
    card_signature: Optional[CMVKSignature] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def _get_signable_content(self) -> str:
        content = {
            "name": self.name,
            "description": self.description,
            "capabilities": sorted(self.capabilities),
            "trust_score": self.trust_score,
            "identity_did": self.identity.did if self.identity else None,
            "identity_public_key": self.identity.public_key if self.identity else None,
        }
        return json.dumps(content, sort_keys=True, separators=(",", ":"))

    def sign(self, identity: CMVKIdentity) -> None:
        """Sign the card."""
        self.identity = identity.public_identity()
        signable = self._get_signable_content()
        self.card_signature = identity.sign(signable)

    def verify_signature(self) -> bool:
        """Verify card signature."""
        if not self.identity or not self.card_signature:
            return False
        signable = self._get_signable_content()
        return self.identity.verify_signature(signable, self.card_signature)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "trust_score": self.trust_score,
            "metadata": self.metadata,
        }
        if self.identity:
            result["identity"] = self.identity.to_dict()
        if self.card_signature:
            result["card_signature"] = self.card_signature.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrustedAgentCard":
        identity = CMVKIdentity.from_dict(data["identity"]) if "identity" in data else None
        card_signature = CMVKSignature.from_dict(data["card_signature"]) if "card_signature" in data else None
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            capabilities=data.get("capabilities", []),
            identity=identity,
            trust_score=data.get("trust_score", 1.0),
            card_signature=card_signature,
            metadata=data.get("metadata", {}),
        )


class TrustHandshake:
    """Handles trust verification between agents."""

    def __init__(self, my_identity: CMVKIdentity, policy: Optional[TrustPolicy] = None):
        self.my_identity = my_identity
        self.policy = policy or TrustPolicy()
        self._verified_peers: Dict[str, tuple[TrustVerificationResult, datetime]] = {}
        self._cache_ttl = timedelta(seconds=self.policy.cache_ttl_seconds)

    def _get_cached_result(self, did: str) -> Optional[TrustVerificationResult]:
        if did in self._verified_peers:
            result, timestamp = self._verified_peers[did]
            if datetime.now(timezone.utc) - timestamp < self._cache_ttl:
                return result
            del self._verified_peers[did]
        return None

    def _cache_result(self, did: str, result: TrustVerificationResult) -> None:
        self._verified_peers[did] = (result, datetime.now(timezone.utc))

    def verify_peer(
        self,
        peer_card: TrustedAgentCard,
        required_capabilities: Optional[List[str]] = None,
        min_trust_score: Optional[float] = None,
    ) -> TrustVerificationResult:
        """Verify a peer agent."""
        warnings: List[str] = []
        min_score = min_trust_score or self.policy.min_trust_score

        if peer_card.identity:
            cached = self._get_cached_result(peer_card.identity.did)
            if cached:
                return cached

        if not peer_card.identity:
            return TrustVerificationResult(
                trusted=False, trust_score=0.0, reason="No identity provided"
            )

        if not peer_card.identity.did.startswith("did:cmvk:"):
            return TrustVerificationResult(
                trusted=False, trust_score=0.0, reason="Invalid DID format"
            )

        if not peer_card.verify_signature():
            return TrustVerificationResult(
                trusted=False, trust_score=0.0, reason="Signature verification failed"
            )

        if peer_card.trust_score < min_score:
            return TrustVerificationResult(
                trusted=False,
                trust_score=peer_card.trust_score,
                reason=f"Trust score {peer_card.trust_score} below minimum {min_score}",
            )

        verified_caps = peer_card.capabilities.copy()
        if required_capabilities:
            missing = set(required_capabilities) - set(peer_card.capabilities)
            if missing:
                return TrustVerificationResult(
                    trusted=False,
                    trust_score=peer_card.trust_score,
                    reason=f"Missing capabilities: {missing}",
                    verified_capabilities=verified_caps,
                )

        result = TrustVerificationResult(
            trusted=True,
            trust_score=peer_card.trust_score,
            reason="Verification successful",
            verified_capabilities=verified_caps,
            warnings=warnings,
        )
        self._cache_result(peer_card.identity.did, result)
        return result

    def clear_cache(self) -> None:
        self._verified_peers.clear()
