"""Agent-OS Governance layer for Semantic Kernel.

This module provides governance controls for Semantic Kernel agents,
including policy enforcement, rate limiting, and audit logging.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from semantic_kernel.agents.agentmesh.identity import CMVKIdentity
from semantic_kernel.agents.agentmesh.trust import (
    TrustHandshake,
    TrustPolicy,
    TrustedAgentCard,
)

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel
    from semantic_kernel.agents.agent import Agent


class ViolationType(Enum):
    """Types of policy violations."""

    RATE_LIMIT = "rate_limit"
    CAPABILITY_DENIED = "capability_denied"
    TRUST_FAILURE = "trust_failure"
    RESOURCE_LIMIT = "resource_limit"
    AUDIT_FAILURE = "audit_failure"


@dataclass
class PolicyViolation:
    """Record of a governance policy violation."""

    violation_type: ViolationType
    timestamp: datetime
    agent_did: Optional[str]
    details: str
    action_taken: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GovernancePolicy:
    """Governance policy configuration for agents.

    Controls what agents can do, how often, and what gets logged.
    """

    # Rate limiting
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    max_tokens_per_request: int = 100000

    # Capability restrictions
    allowed_functions: Optional[List[str]] = None
    denied_functions: Optional[List[str]] = None
    allowed_plugins: Optional[List[str]] = None

    # Resource limits
    max_concurrent_tasks: int = 10
    max_memory_mb: int = 1024
    timeout_seconds: int = 300

    # Audit settings
    audit_all_invocations: bool = False
    audit_function_calls: bool = True
    audit_failures: bool = True
    log_input_output: bool = False

    # Trust requirements
    require_trust_verification: bool = True
    min_trust_score: float = 0.7
    block_unverified_agents: bool = True


@dataclass
class RateLimitState:
    """Tracks rate limiting state."""

    minute_window_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    hour_window_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    minute_count: int = 0
    hour_count: int = 0


class GovernanceKernel:
    """Governance wrapper for Semantic Kernel.

    Provides policy enforcement, rate limiting, and audit logging
    around kernel operations.
    """

    def __init__(
        self,
        kernel: "Kernel",
        identity: CMVKIdentity,
        policy: Optional[GovernancePolicy] = None,
    ):
        """Initialize governance kernel.

        Args:
            kernel: The Semantic Kernel instance to govern
            identity: This kernel's identity
            policy: Governance policy to enforce
        """
        self._kernel = kernel
        self._identity = identity
        self._policy = policy or GovernancePolicy()
        self._handshake = TrustHandshake(
            identity,
            TrustPolicy(
                min_trust_score=self._policy.min_trust_score,
                block_unverified=self._policy.block_unverified_agents,
            ),
        )
        self._violations: List[PolicyViolation] = []
        self._audit_log: List[Dict[str, Any]] = []
        self._rate_limits: Dict[str, RateLimitState] = {}
        self._active_tasks: int = 0

    @property
    def kernel(self) -> "Kernel":
        """Get the underlying kernel."""
        return self._kernel

    @property
    def identity(self) -> CMVKIdentity:
        """Get this kernel's identity."""
        return self._identity

    @property
    def policy(self) -> GovernancePolicy:
        """Get the governance policy."""
        return self._policy

    def _check_rate_limit(self, invoker_did: str) -> bool:
        """Check if request is within rate limits.

        Args:
            invoker_did: The invoker's DID

        Returns:
            True if within limits, False otherwise
        """
        now = datetime.now(timezone.utc)

        if invoker_did not in self._rate_limits:
            self._rate_limits[invoker_did] = RateLimitState()

        state = self._rate_limits[invoker_did]

        # Reset minute window if needed
        minute_elapsed = (now - state.minute_window_start).total_seconds()
        if minute_elapsed >= 60:
            state.minute_window_start = now
            state.minute_count = 0

        # Reset hour window if needed
        hour_elapsed = (now - state.hour_window_start).total_seconds()
        if hour_elapsed >= 3600:
            state.hour_window_start = now
            state.hour_count = 0

        # Check limits
        if state.minute_count >= self._policy.max_requests_per_minute:
            return False
        if state.hour_count >= self._policy.max_requests_per_hour:
            return False

        # Increment counters
        state.minute_count += 1
        state.hour_count += 1

        return True

    def _check_function_allowed(self, function_name: str) -> bool:
        """Check if function is allowed by policy.

        Args:
            function_name: Name of the function to check

        Returns:
            True if allowed, False otherwise
        """
        if self._policy.denied_functions:
            if function_name in self._policy.denied_functions:
                return False

        if self._policy.allowed_functions:
            if function_name not in self._policy.allowed_functions:
                return False

        return True

    def _record_violation(
        self,
        violation_type: ViolationType,
        agent_did: Optional[str],
        details: str,
        action: str,
    ) -> PolicyViolation:
        """Record a policy violation.

        Args:
            violation_type: Type of violation
            agent_did: The violating agent's DID
            details: Description of violation
            action: Action taken in response

        Returns:
            The recorded violation
        """
        violation = PolicyViolation(
            violation_type=violation_type,
            timestamp=datetime.now(timezone.utc),
            agent_did=agent_did,
            details=details,
            action_taken=action,
        )
        self._violations.append(violation)
        return violation

    def _audit(
        self,
        event_type: str,
        invoker_did: Optional[str],
        function_name: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an audit event.

        Args:
            event_type: Type of event
            invoker_did: Invoker's DID
            function_name: Function being called
            success: Whether operation succeeded
            details: Additional details
        """
        if not self._policy.audit_all_invocations:
            if not success and not self._policy.audit_failures:
                return
            if function_name and not self._policy.audit_function_calls:
                return

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "invoker_did": invoker_did,
            "function_name": function_name,
            "success": success,
            "details": details or {},
        }
        self._audit_log.append(record)

    async def invoke_function(
        self,
        function_name: str,
        invoker_card: Optional[TrustedAgentCard] = None,
        **kwargs: Any,
    ) -> Any:
        """Invoke a function with governance checks.

        Args:
            function_name: Name of function to invoke
            invoker_card: Optional invoker's agent card
            **kwargs: Arguments for the function

        Returns:
            Function result

        Raises:
            PermissionError: If governance checks fail
        """
        invoker_did = invoker_card.identity.did if invoker_card and invoker_card.identity else None

        # Verify trust if required
        if self._policy.require_trust_verification and invoker_card:
            result = self._handshake.verify_peer(invoker_card)
            if not result.trusted:
                self._record_violation(
                    ViolationType.TRUST_FAILURE,
                    invoker_did,
                    f"Trust verification failed: {result.reason}",
                    "Request blocked",
                )
                self._audit("function_call", invoker_did, function_name, False, {"reason": result.reason})
                raise PermissionError(f"Trust verification failed: {result.reason}")

        # Check rate limits
        if invoker_did and not self._check_rate_limit(invoker_did):
            self._record_violation(
                ViolationType.RATE_LIMIT,
                invoker_did,
                "Rate limit exceeded",
                "Request blocked",
            )
            self._audit("function_call", invoker_did, function_name, False, {"reason": "rate_limit"})
            raise PermissionError("Rate limit exceeded")

        # Check function is allowed
        if not self._check_function_allowed(function_name):
            self._record_violation(
                ViolationType.CAPABILITY_DENIED,
                invoker_did,
                f"Function {function_name} not allowed",
                "Request blocked",
            )
            self._audit("function_call", invoker_did, function_name, False, {"reason": "function_denied"})
            raise PermissionError(f"Function {function_name} is not allowed by policy")

        # Check concurrent task limit
        if self._active_tasks >= self._policy.max_concurrent_tasks:
            self._record_violation(
                ViolationType.RESOURCE_LIMIT,
                invoker_did,
                "Max concurrent tasks exceeded",
                "Request blocked",
            )
            raise PermissionError("Max concurrent tasks exceeded")

        # Execute function
        self._active_tasks += 1
        try:
            # Get function from kernel and invoke
            func = self._kernel.get_function(function_name)
            result = await func.invoke(self._kernel, **kwargs)
            self._audit("function_call", invoker_did, function_name, True)
            return result
        except Exception as e:
            self._audit("function_call", invoker_did, function_name, False, {"error": str(e)})
            raise
        finally:
            self._active_tasks -= 1

    def get_violations(self) -> List[PolicyViolation]:
        """Get all recorded violations."""
        return self._violations.copy()

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Get the audit log."""
        return self._audit_log.copy()

    def clear_violations(self) -> None:
        """Clear violation records."""
        self._violations.clear()

    def clear_audit_log(self) -> None:
        """Clear audit log."""
        self._audit_log.clear()

    def get_governance_summary(self) -> Dict[str, Any]:
        """Get governance metrics summary."""
        return {
            "total_violations": len(self._violations),
            "violations_by_type": {
                vtype.value: sum(1 for v in self._violations if v.violation_type == vtype)
                for vtype in ViolationType
            },
            "audit_events": len(self._audit_log),
            "active_tasks": self._active_tasks,
            "rate_limited_agents": len(self._rate_limits),
        }


class GovernedAgent:
    """Wrapper for Semantic Kernel agents with governance.

    Provides governance controls around agent operations.
    """

    def __init__(
        self,
        agent: "Agent",
        identity: CMVKIdentity,
        policy: Optional[GovernancePolicy] = None,
    ):
        """Initialize governed agent.

        Args:
            agent: The agent to govern
            identity: Agent's cryptographic identity
            policy: Governance policy
        """
        self._agent = agent
        self._identity = identity
        self._policy = policy or GovernancePolicy()
        self._handshake = TrustHandshake(
            identity,
            TrustPolicy(
                min_trust_score=self._policy.min_trust_score,
                block_unverified=self._policy.block_unverified_agents,
            ),
        )
        self._agent_card = self._create_agent_card()
        self._violations: List[PolicyViolation] = []

    def _create_agent_card(self) -> TrustedAgentCard:
        """Create this agent's card."""
        card = TrustedAgentCard(
            name=self._identity.agent_name,
            description=f"Semantic Kernel agent: {self._agent.name}",
            capabilities=self._identity.capabilities,
        )
        card.sign(self._identity)
        return card

    @property
    def agent(self) -> "Agent":
        """Get the underlying agent."""
        return self._agent

    @property
    def identity(self) -> CMVKIdentity:
        """Get agent identity."""
        return self._identity

    @property
    def agent_card(self) -> TrustedAgentCard:
        """Get agent's trust card."""
        return self._agent_card

    def verify_peer(self, peer_card: TrustedAgentCard) -> bool:
        """Verify a peer agent.

        Args:
            peer_card: Peer's agent card

        Returns:
            True if peer is trusted
        """
        result = self._handshake.verify_peer(peer_card)
        return result.trusted

    def get_violations(self) -> List[PolicyViolation]:
        """Get recorded violations."""
        return self._violations.copy()
